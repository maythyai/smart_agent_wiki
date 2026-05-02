"""Database selection and sync cursor management for Notion connector.

Plan 12-01: Notion connector core with OAuth.
Per NOTI-02: Database selection persistence.
Per NOTI-10: Sync cursor persistence and resume capability.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from saw.connectors.notion.models import NotionDatabase, NotionRichText
from saw.db.notion_models import NotionDatabaseConfigModel, NotionSyncCursorModel

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


class DatabaseSelector:
    """Manages database selection and sync cursor for Notion connector.

    Per NOTI-02: Persist database selection with sync preferences.
    Per NOTI-10: Sync cursor persists after each sync for resume capability.
    """

    def __init__(
        self,
        client,  # notion_client.AsyncClient
        session: AsyncSession,
        connector_id: str,
    ) -> None:
        """Initialize database selector.

        Args:
            client: Notion API client.
            session: SQLAlchemy async session.
            connector_id: Connector identifier.
        """
        self._client = client
        self._session = session
        self._connector_id = connector_id
        self._database_cache: dict[str, NotionDatabase] = {}

    async def list_accessible_databases(self) -> list[NotionDatabase]:
        """List all databases user has access to.

        Uses Notion search API with database filter.

        Returns:
            List of NotionDatabase objects.
        """
        databases = []
        has_more = True
        start_cursor = None

        while has_more:
            response = await self._client.search(
                filter={"property": "object", "value": "database"},
                start_cursor=start_cursor,
            )

            for db_data in response.get("results", []):
                # Extract title from rich text
                title_list = db_data.get("title", [])
                title = ""
                if title_list:
                    title = title_list[0].get("plain_text", "")

                # Extract description
                desc_list = db_data.get("description", [])
                description = ""
                if desc_list:
                    description = desc_list[0].get("plain_text", "")

                db = NotionDatabase(
                    id=db_data.get("id", ""),
                    title=[NotionRichText(
                        type="text",
                        plain_text=title,
                        annotations={},
                        href=None,
                    )],
                    properties=db_data.get("properties", {}),
                    description=description,
                    url=db_data.get("url", ""),
                    is_selected=False,
                )
                databases.append(db)
                self._database_cache[db.id] = db

            has_more = response.get("has_more", False)
            start_cursor = response.get("next_cursor")

        return databases

    async def select_databases(self, database_ids: list[str]) -> None:
        """Select databases for sync.

        Persists selection to database.

        Args:
            database_ids: List of Notion database IDs to select.
        """
        # Clear existing selections
        await self.clear_selections()

        # Add new selections
        for db_id in database_ids:
            # Get cached database name
            db_name = self._database_cache.get(db_id, NotionDatabase(
                id=db_id,
                title=[NotionRichText(type="text", plain_text=db_id, annotations={}, href=None)],
                properties={},
                description="",
                url="",
            )).title[0].plain_text if db_id in self._database_cache else db_id

            config = NotionDatabaseConfigModel(
                connector_id=self._connector_id,
                database_id=db_id,
                database_name=db_name,
                is_selected=True,
            )
            self._session.add(config)

        await self._session.flush()

    async def clear_selections(self) -> None:
        """Clear all database selections for this connector."""
        stmt = delete(NotionDatabaseConfigModel).where(
            NotionDatabaseConfigModel.connector_id == self._connector_id
        )
        await self._session.execute(stmt)

    async def get_selected_databases(self) -> list[NotionDatabaseConfigModel]:
        """Get currently selected databases.

        Returns:
            List of NotionDatabaseConfigModel for selected databases.
        """
        stmt = (
            select(NotionDatabaseConfigModel)
            .where(NotionDatabaseConfigModel.connector_id == self._connector_id)
            .where(NotionDatabaseConfigModel.is_selected == True)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_property_mapping(
        self,
        database_id: str,
        mapping: dict,
    ) -> None:
        """Update property mapping for a database.

        Args:
            database_id: Notion database ID.
            mapping: Property to field mapping dict.
        """
        stmt = select(NotionDatabaseConfigModel).where(
            NotionDatabaseConfigModel.connector_id == self._connector_id,
            NotionDatabaseConfigModel.database_id == database_id,
        )
        result = await self._session.execute(stmt)
        config = result.scalar_one_or_none()

        if config:
            config.property_mapping = mapping
            await self._session.flush()
        else:
            logger.warning(f"Database config not found for {database_id}")

    async def get_sync_cursors(self) -> dict[str, str]:
        """Get all sync cursors for this connector.

        Returns:
            Dict mapping database_id to cursor_token.
        """
        stmt = select(NotionSyncCursorModel).where(
            NotionSyncCursorModel.connector_id == self._connector_id
        )
        result = await self._session.execute(stmt)
        cursors = result.scalars().all()

        return {
            c.database_id: c.cursor_token
            for c in cursors
            if c.cursor_token
        }

    async def update_sync_cursor(
        self,
        database_id: str,
        cursor_token: Optional[str],
        items_count: int = 0,
    ) -> None:
        """Update sync cursor for a database.

        Per NOTI-10: Cursor persists for resume capability.

        Args:
            database_id: Notion database ID.
            cursor_token: Pagination cursor (None to clear).
            items_count: Number of items synced in this batch.
        """
        stmt = select(NotionSyncCursorModel).where(
            NotionSyncCursorModel.connector_id == self._connector_id,
            NotionSyncCursorModel.database_id == database_id,
        )
        result = await self._session.execute(stmt)
        cursor = result.scalar_one_or_none()

        now = utcnow()

        if cursor:
            cursor.cursor_token = cursor_token
            cursor.last_sync_at = now
            cursor.items_synced += items_count
        else:
            cursor = NotionSyncCursorModel(
                connector_id=self._connector_id,
                database_id=database_id,
                cursor_token=cursor_token,
                last_sync_at=now,
                items_synced=items_count,
            )
            self._session.add(cursor)

        await self._session.flush()

    async def clear_sync_cursor(self, database_id: str) -> None:
        """Clear sync cursor for a database (after complete sync).

        Args:
            database_id: Notion database ID.
        """
        await self.update_sync_cursor(database_id, None)

    async def get_last_sync_times(self) -> dict[str, datetime]:
        """Get last sync times for all databases.

        Returns:
            Dict mapping database_id to last_sync_at.
        """
        stmt = select(NotionSyncCursorModel).where(
            NotionSyncCursorModel.connector_id == self._connector_id
        )
        result = await self._session.execute(stmt)
        cursors = result.scalars().all()

        return {
            c.database_id: c.last_sync_at
            for c in cursors
            if c.last_sync_at
        }
