"""Notion connector implementation.

Plan 12-01: Notion connector core with OAuth.
Per NOTI-01: OAuth workspace connection.
Per NOTI-02: Database selection.
Per NOTI-09: Rate limiting (3 req/s).
Per NOTI-10: Sync cursor persistence.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from saw.connectors.protocol import (
    UnifiedConnectorInterface,
    AuthResult,
    ConnectorItem,
    AuthenticationError,
    SyncError,
)
from saw.domain.exceptions import ConnectorError
from saw.connectors.models import ConnectorConfig
from saw.connectors.rate_limiter import RateLimitManager
from saw.connectors.notion.models import NotionPage, NotionDatabase, NotionRichText
from saw.connectors.notion.oauth import NotionOAuthHandler
from saw.db.notion_models import NotionSyncCursorModel, NotionDatabaseConfigModel

logger = logging.getLogger(__name__)
from saw.domain.utils import utcnow  # noqa: F401


class NotionConnector(UnifiedConnectorInterface):
    """Notion connector implementing UnifiedConnectorInterface.

    Per NOTI-01: OAuth workspace connection.
    Per NOTI-09: Rate limiting enforced via notion-client SDK.
    Per NOTI-10: Sync cursor persists after each sync.
    """

    platform_name: str = "notion"
    supports_push: bool = True

    def __init__(
        self,
        config: ConnectorConfig,
        rate_limiter: RateLimitManager,
        session: AsyncSession,
        oauth_handler: Optional[NotionOAuthHandler] = None,
    ) -> None:
        """Initialize Notion connector.

        Args:
            config: Connector configuration.
            rate_limiter: Rate limiter for Notion API.
            session: SQLAlchemy async session for database operations.
            oauth_handler: OAuth handler for Notion (optional).
        """
        self._config = config
        self._rate_limiter = rate_limiter
        self._session = session
        self._oauth_handler = oauth_handler
        self._client: Optional[Any] = None
        self._selected_databases: list[dict] = []
        self._sync_cursors: dict[str, str] = {}

    async def _ensure_client(self) -> Any:
        """Ensure notion-client is initialized.

        Returns:
            Notion client instance.
        """
        if self._client is None:
            try:
                from notion_client import AsyncClient

                # Decrypt access token from config
                access_token = self._config.config.get("access_token", "")
                if not access_token:
                    # Try encrypted token
                    encrypted = self._config.credentials_encrypted
                    if encrypted:
                        from saw.connectors.token_encryption import TokenEncryption
                        encryption = TokenEncryption.from_env()
                        token_data = encryption.decrypt_token_set(encrypted)
                        access_token = token_data.get("access_token", "")

                self._client = AsyncClient(auth=access_token)
            except ImportError:
                logger.error(
                    "notion-client package is not installed. "
                    "Run: pip install notion-client"
                )
                raise ConnectorError(
                    "notion-client package is not installed. "
                    "Run: pip install notion-client"
                )

        return self._client

    async def _load_selected_databases(self) -> list[dict]:
        """Load selected databases from config.

        Returns:
            List of selected database configs.
        """
        stmt = (
            select(NotionDatabaseConfigModel)
            .where(NotionDatabaseConfigModel.connector_id == self._config.id)
            .where(NotionDatabaseConfigModel.is_selected == True)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        self._selected_databases = [
            {
                "database_id": m.database_id,
                "database_name": m.database_name,
                "sync_direction": m.sync_direction.value if m.sync_direction else "bidirectional",
                "property_mapping": m.property_mapping or {},
            }
            for m in models
        ]
        return self._selected_databases

    async def _load_sync_cursors(self) -> dict[str, str]:
        """Load sync cursors for incremental sync.

        Returns:
            Dict mapping database_id to cursor_token.
        """
        stmt = select(NotionSyncCursorModel).where(
            NotionSyncCursorModel.connector_id == self._config.id
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        self._sync_cursors = {
            m.database_id: m.cursor_token
            for m in models
            if m.cursor_token
        }
        return self._sync_cursors

    async def _auto_discover_databases(self) -> list[dict]:
        """Auto-discover Notion databases accessible to the connector.

        Queries the Notion API for all databases the integration has access to.
        Populates _selected_databases with discovered databases.

        Returns:
            List of discovered database configs.
        """
        if self._client is None:
            return []

        try:
            await self._rate_limiter.acquire()
            response = await self._client.search(
                filter={"property": "object", "value": "database"},
                page_size=10,
            )
            databases = response.get("results", [])

            self._selected_databases = []
            for db in databases:
                db_id = db.get("id", "")
                title_parts = db.get("title", [])
                db_name = (
                    title_parts[0].get("plain_text", db_id)
                    if title_parts
                    else db_id
                )
                self._selected_databases.append({
                    "database_id": db_id,
                    "database_name": db_name,
                    "sync_direction": "pull",
                    "property_mapping": {},
                })

            logger.info("Auto-discovered %d Notion databases", len(self._selected_databases))
            return self._selected_databases
        except Exception as e:
            logger.error("Failed to auto-discover Notion databases: %s", e)
            return []

    async def authenticate(self, credentials: dict) -> AuthResult:
        """Complete OAuth authentication flow.

        Per NOTI-01: Exchange OAuth code for tokens.

        Args:
            credentials: Dict with 'code' and 'state'.

        Returns:
            AuthResult with access token and workspace info.

        Raises:
            AuthenticationError: If authentication fails.
        """
        code = credentials.get("code")
        state = credentials.get("state")

        if not code or not state:
            raise AuthenticationError("Missing OAuth code or state")

        try:
            token_response, user_id = await self._oauth_handler.exchange_code(code, state)

            return AuthResult(
                access_token=token_response.get("encrypted_token", ""),
                refresh_token=None,
                expires_at=None,
                scopes=[],
                raw_response=token_response,
            )
        except Exception as e:
            raise AuthenticationError(f"Notion authentication failed: {str(e)}")

    async def get_items(
        self,
        since: Optional[datetime] = None,
        filters: Optional[dict] = None,
    ) -> list[ConnectorItem]:
        """Pull pages from selected Notion databases.

        Per NOTI-10: Sync cursor persists after each fetch.

        Args:
            since: Only return items updated after this timestamp.
            filters: Optional filters (database_id, etc.).

        Returns:
            List of ConnectorItem from selected databases.
        """
        await self._ensure_client()
        await self._load_selected_databases()
        await self._load_sync_cursors()

        # Auto-discover databases if none are configured
        if not self._selected_databases:
            logger.info("No databases configured — auto-discovering Notion databases")
            await self._auto_discover_databases()

        items: list[ConnectorItem] = []

        if not self._selected_databases:
            logger.warning("No Notion databases selected or discoverable — returning empty results")
            return items

        for db_config in self._selected_databases:
            database_id = db_config["database_id"]

            # Build query filter
            query_params: dict = {"database_id": database_id}

            if since:
                query_params["filter"] = {
                    "timestamp": "last_edited_time",
                    "last_edited_time": {"after": since.isoformat()},
                }

            # Use cursor if available
            cursor = self._sync_cursors.get(database_id)
            if cursor:
                query_params["start_cursor"] = cursor

            # Query pages
            await self._rate_limiter.acquire()
            response = await self._client.databases.query(**query_params)

            pages = response.get("results", [])
            has_more = response.get("has_more", False)
            next_cursor = response.get("next_cursor")

            # Transform pages to ConnectorItems
            for page_data in pages:
                item = self._transform_page_to_item(page_data)
                items.append(item)

            # Persist sync cursor
            if next_cursor or has_more:
                await self._update_sync_cursor(database_id, next_cursor)

        return items

    async def _update_sync_cursor(
        self,
        database_id: str,
        cursor_token: Optional[str],
    ) -> None:
        """Update sync cursor for database.

        Per NOTI-10: Cursor persists for resume capability.

        Args:
            database_id: Notion database ID.
            cursor_token: Pagination cursor.
        """
        stmt = select(NotionSyncCursorModel).where(
            NotionSyncCursorModel.connector_id == self._config.id,
            NotionSyncCursorModel.database_id == database_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        now = utcnow()

        if model:
            model.cursor_token = cursor_token
            model.last_sync_at = now
            model.items_synced += 1
        else:
            model = NotionSyncCursorModel(
                connector_id=self._config.id,
                database_id=database_id,
                cursor_token=cursor_token,
                last_sync_at=now,
                items_synced=1,
            )
            self._session.add(model)

        await self._session.flush()

    def _transform_page_to_item(self, page_data: dict) -> ConnectorItem:
        """Transform Notion page to ConnectorItem.

        Args:
            page_data: Raw page dict from Notion API.

        Returns:
            ConnectorItem with page data.
        """
        properties = page_data.get("properties", {})

        # Extract title
        title = ""
        for prop in properties.values():
            if prop.get("type") == "title":
                title_list = prop.get("title", [])
                if title_list:
                    title = title_list[0].get("plain_text", "")
                break

        # Extract timestamps
        created_time = page_data.get("created_time")
        edited_time = page_data.get("last_edited_time")

        return ConnectorItem(
            id=page_data.get("id", ""),
            title=title,
            content="",  # Content fetched separately in transformer
            url=page_data.get("url", ""),
            author=None,
            created_at=datetime.fromisoformat(created_time) if created_time else None,
            updated_at=datetime.fromisoformat(edited_time) if edited_time else None,
            metadata={
                "database_id": page_data.get("parent", {}).get("database_id"),
                "archived": page_data.get("archived", False),
                "properties": properties,
            },
        )

    async def put_item(self, item: ConnectorItem) -> str:
        """Push item to Notion.

        Creates or updates a page in Notion.

        Args:
            item: Item to create/update.

        Returns:
            Notion page ID.

        Raises:
            SyncError: If push fails.
        """
        await self._ensure_client()

        # Determine if update or create
        page_id = item.id if item.id and item.id.startswith("page-") else None

        try:
            if page_id:
                # Update existing page
                await self._rate_limiter.acquire()
                await self._client.pages.update(
                    page_id=page_id,
                    properties=self._build_notion_properties(item),
                )
                return page_id
            else:
                # Create new page
                database_id = item.metadata.get("database_id", "")
                if not database_id:
                    # Use first selected database
                    if self._selected_databases:
                        database_id = self._selected_databases[0]["database_id"]
                    else:
                        raise SyncError("No database specified for new page")

                await self._rate_limiter.acquire()
                response = await self._client.pages.create(
                    parent={"database_id": database_id},
                    properties=self._build_notion_properties(item),
                )
                return response.get("id", "")
        except Exception as e:
            raise SyncError(f"Failed to push item to Notion: {str(e)}")

    def _build_notion_properties(self, item: ConnectorItem) -> dict:
        """Build Notion properties dict from ConnectorItem.

        Args:
            item: ConnectorItem to transform.

        Returns:
            Dict of Notion properties.
        """
        properties = {
            "Title": {
                "title": [{"text": {"content": item.title}, "type": "text"}],
            },
        }
        return properties

    async def delete_item(self, item_id: str) -> bool:
        """Archive page in Notion.

        Note: Notion uses archive, not delete.

        Args:
            item_id: Notion page ID.

        Returns:
            True if archived, False if not found.

        Raises:
            SyncError: If archive fails.
        """
        await self._ensure_client()

        try:
            await self._rate_limiter.acquire()
            await self._client.pages.update(
                page_id=item_id,
                archived=True,
            )
            return True
        except Exception as e:
            if "not found" in str(e).lower():
                return False
            raise SyncError(f"Failed to archive Notion page: {str(e)}")

    def transform_to_claim(self, item: ConnectorItem) -> dict:
        """Convert Notion page to SAW Claim dict.

        Args:
            item: ConnectorItem from Notion.

        Returns:
            Dict matching Claim schema.
        """
        return {
            "title": item.title,
            "content": item.content,
            "source_platform": "notion",
            "source_id": item.id,
            "source_url": item.url,
            "metadata": {
                "notion_page_id": item.id,
                "notion_database_id": item.metadata.get("database_id"),
                "notion_created_time": item.created_at.isoformat() if item.created_at else None,
                "notion_last_edited_time": item.updated_at.isoformat() if item.updated_at else None,
                **item.metadata,
            },
        }

    def transform_from_claim(self, claim: dict) -> ConnectorItem:
        """Convert SAW Claim dict to Notion item format.

        Args:
            claim: SAW Claim dict.

        Returns:
            ConnectorItem ready for Notion push.
        """
        return ConnectorItem(
            id=claim.get("source_id", ""),
            title=claim.get("title", ""),
            content=claim.get("content", ""),
            url=claim.get("source_url"),
            author=None,
            created_at=None,
            updated_at=None,
            metadata={
                "database_id": claim.get("metadata", {}).get("notion_database_id", ""),
                "confidence": claim.get("confidence"),
                "freshness": claim.get("freshness"),
                "tags": claim.get("tags", []),
            },
        )

    async def list_databases(self) -> list[NotionDatabase]:
        """List accessible Notion databases.

        Returns:
            List of NotionDatabase objects.
        """
        await self._ensure_client()

        databases = []
        has_more = True
        start_cursor = None

        while has_more:
            await self._rate_limiter.acquire()
            response = await self._client.search(
                filter={"property": "object", "value": "database"},
                start_cursor=start_cursor,
            )

            for db_data in response.get("results", []):
                title_list = db_data.get("title", [])
                title = ""
                if title_list:
                    title = title_list[0].get("plain_text", "")

                databases.append(NotionDatabase(
                    id=db_data.get("id", ""),
                    title=[NotionRichText(type="text", plain_text=title, annotations={}, href=None)],
                    properties=db_data.get("properties", {}),
                    description=db_data.get("description", [{}])[0].get("plain_text", "") if db_data.get("description") else "",
                    url=db_data.get("url", ""),
                    is_selected=False,
                ))

            has_more = response.get("has_more", False)
            start_cursor = response.get("next_cursor")

        return databases
