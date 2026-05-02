"""Property mapping system for Notion to SAW field conversion.

Plan 12-02: Property mapping and block transformation.
Per NOTI-04: Notion properties map correctly to SAW fields.
Per NOTI-07: Property type changes handled gracefully.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
import logging

from saw.db.notion_models import NotionDatabaseConfigModel


logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


# Default value mappings for SAW enums
DEFAULT_CONFIDENCE_VALUE_MAP = {
    "Unverified": "unverified",
    "Single Source": "single_source",
    "Single-Source": "single_source",
    "single_source": "single_source",
    "Cross-Validated": "cross_validated",
    "Cross Validated": "cross_validated",
    "cross_validated": "cross_validated",
    "Human Verified": "human_verified",
    "Human-Verified": "human_verified",
    "human_verified": "human_verified",
}

DEFAULT_FRESHNESS_VALUE_MAP = {
    "Fresh": "fresh",
    "fresh": "fresh",
    "Stale": "stale",
    "stale": "stale",
    "Rotten": "rotten",
    "rotten": "rotten",
}


@dataclass
class PropertyMappingConfig:
    """Configuration for property mapping.

    Defines how Notion property names map to SAW field names.

    Attributes:
        title_property: Notion property name for title (default: "Title").
        confidence_property: Notion property name for confidence (default: "Confidence").
        freshness_property: Notion property name for freshness (default: "Freshness").
        tags_property: Notion property name for tags (default: "Tags").
        last_sync_property: Notion property name for last sync datetime.
        custom_mappings: Additional property -> field mappings.
        confidence_value_map: Notion select options -> SAW enum values.
        freshness_value_map: Notion select options -> SAW enum values.
    """

    title_property: str = "Title"
    confidence_property: str = "Confidence"
    freshness_property: str = "Freshness"
    tags_property: str = "Tags"
    last_sync_property: str = "Last Sync"
    custom_mappings: dict[str, str] = field(default_factory=dict)
    confidence_value_map: dict[str, str] = field(default_factory=lambda: DEFAULT_CONFIDENCE_VALUE_MAP)
    freshness_value_map: dict[str, str] = field(default_factory=lambda: DEFAULT_FRESHNESS_VALUE_MAP)


class PropertyMapper:
    """Maps Notion properties to SAW fields.

    Per NOTI-04: Flexible mapping between Notion properties and SAW fields.
    Per NOTI-07: Handles property type changes gracefully.
    """

    def __init__(
        self,
        config: PropertyMappingConfig,
        database_config: Optional[NotionDatabaseConfigModel],
    ) -> None:
        """Initialize property mapper.

        Args:
            config: Mapping configuration.
            database_config: Database-specific configuration (optional).
        """
        self._config = config
        self._database_config = database_config

        # Merge database-specific property mappings if available
        self._property_mappings = config.custom_mappings.copy()
        if database_config and database_config.property_mapping:
            self._property_mappings.update(database_config.property_mapping)

    def map_properties(self, properties: dict[str, Any]) -> dict:
        """Extract all mapped fields from Notion properties.

        Args:
            properties: Notion page properties dict.

        Returns:
            Dict with SAW-compatible field names and values.
        """
        return {
            "title": self.extract_title(properties),
            "confidence": self.extract_confidence(properties),
            "freshness": self.extract_freshness(properties),
            "tags": self.extract_tags(properties),
            "last_sync": self._extract_last_sync(properties),
        }

    def map_property_value(self, prop: dict, target_field: str) -> Any:
        """Extract value from property for target field.

        Dispatches to type-specific handler.

        Args:
            prop: Notion property dict.
            target_field: Target SAW field name.

        Returns:
            Extracted value.
        """
        prop_type = prop.get("type", "unknown")
        handler = getattr(self, f"_extract_{prop_type}", self._extract_unknown)
        return handler(prop)

    def extract_title(self, properties: dict) -> str:
        """Extract title from Notion properties.

        Args:
            properties: Notion page properties dict.

        Returns:
            Title string or empty string if not found.
        """
        prop_name = self._config.title_property

        # Find by configured name or by type
        if prop_name in properties:
            prop = properties[prop_name]
            if prop.get("type") == "title":
                return self._extract_title_text(prop)

        # Fallback: find by type
        for name, prop in properties.items():
            if prop.get("type") == "title":
                return self._extract_title_text(prop)

        return ""

    def _extract_title_text(self, prop: dict) -> str:
        """Extract text from title property."""
        title_list = prop.get("title", [])
        if title_list:
            return title_list[0].get("plain_text", "")
        return ""

    def extract_confidence(self, properties: dict) -> str:
        """Extract confidence from Notion select property.

        Args:
            properties: Notion page properties dict.

        Returns:
            Confidence enum value (default: "unverified").
        """
        prop_name = self._config.confidence_property

        if prop_name not in properties:
            return "unverified"

        prop = properties[prop_name]
        select_value = prop.get("select", {})
        if not select_value:
            return "unverified"

        option_name = select_value.get("name", "")
        return self._config.confidence_value_map.get(option_name, "unverified")

    def extract_freshness(self, properties: dict) -> str:
        """Extract freshness from Notion select property.

        Args:
            properties: Notion page properties dict.

        Returns:
            Freshness enum value (default: "fresh").
        """
        prop_name = self._config.freshness_property

        if prop_name not in properties:
            return "fresh"

        prop = properties[prop_name]
        select_value = prop.get("select", {})
        if not select_value:
            return "fresh"

        option_name = select_value.get("name", "")
        return self._config.freshness_value_map.get(option_name, "fresh")

    def extract_tags(self, properties: dict) -> list[str]:
        """Extract tags from Notion multi-select property.

        Args:
            properties: Notion page properties dict.

        Returns:
            List of tag strings.
        """
        prop_name = self._config.tags_property

        if prop_name not in properties:
            return []

        prop = properties[prop_name]
        multi_select = prop.get("multi_select", [])
        return [opt.get("name", "") for opt in multi_select if opt.get("name")]

    def _extract_last_sync(self, properties: dict) -> Optional[datetime]:
        """Extract last sync datetime.

        Args:
            properties: Notion page properties dict.

        Returns:
            Last sync datetime or None.
        """
        prop_name = self._config.last_sync_property

        if prop_name not in properties:
            return None

        prop = properties[prop_name]
        return self._extract_date(prop)

    def _extract_select(self, prop: dict, value_map: dict, default: str) -> str:
        """Extract select property value.

        Args:
            prop: Notion select property.
            value_map: Value mapping dict.
            default: Default value.

        Returns:
            Mapped value or default.
        """
        select = prop.get("select", {})
        if not select:
            return default
        name = select.get("name", "")
        return value_map.get(name, default)

    def _extract_multi_select(self, prop: dict) -> list[str]:
        """Extract multi-select values.

        Args:
            prop: Notion multi_select property.

        Returns:
            List of option names.
        """
        multi_select = prop.get("multi_select", [])
        return [opt.get("name", "") for opt in multi_select if opt.get("name")]

    def _extract_date(self, prop: dict) -> Optional[datetime]:
        """Extract date from date property.

        Args:
            prop: Notion date property.

        Returns:
            datetime or None.
        """
        date_obj = prop.get("date", {})
        if not date_obj:
            return None

        start = date_obj.get("start")
        if start:
            try:
                # Handle ISO format
                if isinstance(start, str):
                    return datetime.fromisoformat(start.replace("Z", "+00:00"))
                return start
            except Exception:
                logger.warning(f"Failed to parse date: {start}")
        return None

    def _extract_checkbox(self, prop: dict) -> bool:
        """Extract checkbox value.

        Args:
            prop: Notion checkbox property.

        Returns:
            Boolean value.
        """
        return prop.get("checkbox", False)

    def _extract_number(self, prop: dict) -> Optional[int | float]:
        """Extract number value.

        Args:
            prop: Notion number property.

        Returns:
            Int or float value.
        """
        return prop.get("number")

    def _extract_url(self, prop: dict) -> Optional[str]:
        """Extract URL value.

        Args:
            prop: Notion url property.

        Returns:
            URL string.
        """
        return prop.get("url")

    def _extract_email(self, prop: dict) -> Optional[str]:
        """Extract email value.

        Args:
            prop: Notion email property.

        Returns:
            Email string.
        """
        return prop.get("email")

    def _extract_phone(self, prop: dict) -> Optional[str]:
        """Extract phone value.

        Args:
            prop: Notion phone_number property.

        Returns:
            Phone string.
        """
        return prop.get("phone_number")

    def _extract_rich_text(self, prop: dict) -> str:
        """Extract rich text as plain string.

        Args:
            prop: Notion rich_text property.

        Returns:
            Plain text string.
        """
        rich_text = prop.get("rich_text", [])
        return "".join(seg.get("plain_text", "") for seg in rich_text)

    def _extract_files(self, prop: dict) -> list[dict]:
        """Extract files list.

        Args:
            prop: Notion files property.

        Returns:
            List of file dicts with name, url, expiry_time.
        """
        files = prop.get("files", [])
        result = []
        for f in files:
            file_info = {"name": f.get("name", "")}
            if f.get("type") == "external":
                file_info["url"] = f.get("external", {}).get("url", "")
            elif f.get("type") == "file":
                file_info["url"] = f.get("file", {}).get("url", "")
                file_info["expiry_time"] = f.get("file", {}).get("expiry_time")
            result.append(file_info)
        return result

    def _extract_relation(self, prop: dict) -> list[str]:
        """Extract relation page IDs.

        Args:
            prop: Notion relation property.

        Returns:
            List of page IDs.
        """
        relation = prop.get("relation", [])
        return [r.get("id", "") for r in relation if r.get("id")]

    def _extract_rollup(self, prop: dict) -> Any:
        """Extract rollup value.

        Args:
            prop: Notion rollup property.

        Returns:
            Rollup value (type depends on rollup config).
        """
        rollup = prop.get("rollup", {})
        return rollup.get("number", rollup.get("date", rollup.get("array", None)))

    def _extract_created_time(self, prop: dict) -> Optional[datetime]:
        """Extract created_time.

        Args:
            prop: Notion created_time property.

        Returns:
            datetime or None.
        """
        created = prop.get("created_time")
        if created:
            if isinstance(created, str):
                return datetime.fromisoformat(created.replace("Z", "+00:00"))
            return created
        return None

    def _extract_last_edited_time(self, prop: dict) -> Optional[datetime]:
        """Extract last_edited_time.

        Args:
            prop: Notion last_edited_time property.

        Returns:
            datetime or None.
        """
        edited = prop.get("last_edited_time")
        if edited:
            if isinstance(edited, str):
                return datetime.fromisoformat(edited.replace("Z", "+00:00"))
            return edited
        return None

    def _extract_created_by(self, prop: dict) -> Optional[dict]:
        """Extract created_by user info.

        Args:
            prop: Notion created_by property.

        Returns:
            User info dict.
        """
        user = prop.get("created_by", {})
        if user:
            return {
                "id": user.get("id", ""),
                "name": user.get("name", ""),
                "type": user.get("type", ""),
            }
        return None

    def _extract_last_edited_by(self, prop: dict) -> Optional[dict]:
        """Extract last_edited_by user info.

        Args:
            prop: Notion last_edited_by property.

        Returns:
            User info dict.
        """
        user = prop.get("last_edited_by", {})
        if user:
            return {
                "id": user.get("id", ""),
                "name": user.get("name", ""),
                "type": user.get("type", ""),
            }
        return None

    def _extract_unknown(self, prop: dict) -> Any:
        """Handle unknown property type.

        Args:
            prop: Unknown property.

        Returns:
            None with warning logged.
        """
        prop_type = prop.get("type", "unknown")
        logger.warning(f"Unknown property type: {prop_type}")
        return None

    def validate_property_schema(self, database_schema: dict) -> list[str]:
        """Check if required properties exist in schema.

        Args:
            database_schema: Notion database property schema.

        Returns:
            List of warnings for missing properties.
        """
        warnings = []
        required = [
            self._config.title_property,
            self._config.confidence_property,
            self._config.freshness_property,
            self._config.tags_property,
        ]

        for prop_name in required:
            if prop_name not in database_schema:
                warnings.append(f"Missing property: {prop_name}")

        return warnings

    def map_to_notion_properties(self, claim: dict, schema: dict) -> dict:
        """Map SAW fields back to Notion property format.

        Per NOTI-07: Respects Notion property schema. Skips if type changed.

        Args:
            claim: SAW Claim dict.
            schema: Notion database property schema.

        Returns:
            Dict of Notion properties.
        """
        result = {}

        # Title
        title_prop = self._config.title_property
        if title_prop in schema:
            if schema[title_prop].get("type") == "title":
                result[title_prop] = {
                    "title": [{"text": {"content": claim.get("title", "")}, "type": "text"}]
                }
            else:
                logger.warning(f"Property '{title_prop}' is not title type, skipping")

        # Confidence
        conf_prop = self._config.confidence_property
        if conf_prop in schema:
            if schema[conf_prop].get("type") == "select":
                # Reverse map confidence value
                confidence = claim.get("confidence", "unverified")
                reverse_map = {v: k for k, v in self._config.confidence_value_map.items()}
                notion_value = reverse_map.get(confidence, "Unverified")
                result[conf_prop] = {"select": {"name": notion_value}}
            else:
                logger.warning(f"Property '{conf_prop}' changed from select, skipping")

        # Freshness
        fresh_prop = self._config.freshness_property
        if fresh_prop in schema:
            if schema[fresh_prop].get("type") == "select":
                freshness = claim.get("freshness", "fresh")
                reverse_map = {v: k for k, v in self._config.freshness_value_map.items()}
                notion_value = reverse_map.get(freshness, "Fresh")
                result[fresh_prop] = {"select": {"name": notion_value}}
            else:
                logger.warning(f"Property '{fresh_prop}' changed from select, skipping")

        # Tags
        tags_prop = self._config.tags_property
        if tags_prop in schema:
            if schema[tags_prop].get("type") == "multi_select":
                tags = claim.get("tags", [])
                result[tags_prop] = {
                    "multi_select": [{"name": tag} for tag in tags]
                }
            else:
                logger.warning(f"Property '{tags_prop}' changed from multi_select, skipping")

        return result


# Convenience functions

def extract_title(properties: dict, config: Optional[PropertyMappingConfig] = None) -> str:
    """Extract title from properties."""
    config = config or PropertyMappingConfig()
    mapper = PropertyMapper(config, None)
    return mapper.extract_title(properties)


def extract_confidence(properties: dict, config: Optional[PropertyMappingConfig] = None) -> str:
    """Extract confidence from properties."""
    config = config or PropertyMappingConfig()
    mapper = PropertyMapper(config, None)
    return mapper.extract_confidence(properties)


def extract_freshness(properties: dict, config: Optional[PropertyMappingConfig] = None) -> str:
    """Extract freshness from properties."""
    config = config or PropertyMappingConfig()
    mapper = PropertyMapper(config, None)
    return mapper.extract_freshness(properties)


def extract_tags(properties: dict, config: Optional[PropertyMappingConfig] = None) -> list[str]:
    """Extract tags from properties."""
    config = config or PropertyMappingConfig()
    mapper = PropertyMapper(config, None)
    return mapper.extract_tags(properties)
