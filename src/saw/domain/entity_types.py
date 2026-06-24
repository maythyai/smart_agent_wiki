"""Entity type system for user-facing page classification.

Provides typed entities (person, project, concept, meeting, etc.) layered
on top of the internal PageType enum. Each type can carry an optional
schema defining expected fields. Schemas are advisory, not enforced.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class EntityField:
    """A field definition within an entity type schema."""

    name: str
    field_type: str  # "string", "date", "url", "select", "number", "tags"
    required: bool = False
    description: str = ""
    options: list[str] = field(default_factory=list)  # for "select" type

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "field_type": self.field_type,
            "required": self.required,
            "description": self.description,
            "options": self.options,
        }


@dataclass(frozen=True)
class EntityType:
    """A user-facing entity type for wiki pages."""

    id: str
    name: str
    icon: str
    description: str = ""
    fields: list[EntityField] = field(default_factory=list)
    color: str = "#6366f1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "icon": self.icon,
            "description": self.description,
            "fields": [f.to_dict() for f in self.fields],
            "color": self.color,
        }


# Built-in entity types
_BUILTIN_TYPES: list[EntityType] = [
    EntityType(
        id="note",
        name="Note",
        icon="📝",
        description="General-purpose note",
        color="#6366f1",
    ),
    EntityType(
        id="person",
        name="Person",
        icon="👤",
        description="A person — contact, colleague, or reference",
        fields=[
            EntityField("email", "string", description="Email address"),
            EntityField("role", "string", description="Role or title"),
            EntityField("organization", "string", description="Organization"),
        ],
        color="#3b82f6",
    ),
    EntityType(
        id="project",
        name="Project",
        icon="📊",
        description="A project with status and timeline",
        fields=[
            EntityField(
                "status",
                "select",
                description="Project status",
                options=["active", "completed", "on-hold", "cancelled"],
            ),
            EntityField("start_date", "date", description="Start date"),
            EntityField("end_date", "date", description="End date"),
            EntityField("team", "tags", description="Team members"),
        ],
        color="#10b981",
    ),
    EntityType(
        id="concept",
        name="Concept",
        icon="💡",
        description="An idea, theory, or concept",
        fields=[
            EntityField("domain", "string", description="Domain or field"),
            EntityField("related_concepts", "tags", description="Related concepts"),
        ],
        color="#f59e0b",
    ),
    EntityType(
        id="meeting",
        name="Meeting",
        icon="📅",
        description="Meeting notes with attendees and decisions",
        fields=[
            EntityField("date", "date", required=True, description="Meeting date"),
            EntityField("attendees", "tags", description="Attendees"),
            EntityField("decisions", "string", description="Key decisions"),
        ],
        color="#ef4444",
    ),
    EntityType(
        id="reference",
        name="Reference",
        icon="📚",
        description="A book, article, or external reference",
        fields=[
            EntityField("authors", "string", description="Authors"),
            EntityField("url", "url", description="URL"),
            EntityField("published_date", "date", description="Publication date"),
        ],
        color="#8b5cf6",
    ),
    EntityType(
        id="bookmark",
        name="Bookmark",
        icon="🔖",
        description="A saved web page or resource",
        fields=[
            EntityField("url", "url", required=True, description="URL"),
            EntityField("saved_date", "date", description="Date saved"),
        ],
        color="#ec4899",
    ),
]


class EntityTypeRegistry:
    """Registry for entity types — built-in + user-defined.

    Built-in types are always available. User types can be added via
    `.saw/entity_types.yaml` and are merged at runtime.
    """

    def __init__(self, user_types: list[EntityType] | None = None) -> None:
        self._types: dict[str, EntityType] = {}
        # Register built-in types
        for t in _BUILTIN_TYPES:
            self._types[t.id] = t
        # Register user types (override built-ins if same id)
        if user_types:
            for t in user_types:
                self._types[t.id] = t

    def get(self, type_id: str) -> EntityType | None:
        """Get entity type by id. Returns None if not found."""
        return self._types.get(type_id)

    def list_types(self) -> list[EntityType]:
        """List all registered entity types."""
        return list(self._types.values())

    def get_schema(self, type_id: str) -> list[EntityField] | None:
        """Get field schema for an entity type."""
        t = self._types.get(type_id)
        return t.fields if t else None

    def validate_properties(
        self, type_id: str, props: dict[str, Any]
    ) -> list[str]:
        """Validate properties against type schema. Returns list of errors."""
        schema = self.get_schema(type_id)
        if schema is None:
            return [f"Unknown entity type: {type_id}"]

        errors: list[str] = []
        for f in schema:
            if f.required and f.name not in props:
                errors.append(f"Missing required field: {f.name}")
        return errors

    @classmethod
    def from_yaml(cls, yaml_path: str) -> EntityTypeRegistry:
        """Load user entity types from a YAML file and create registry."""
        import yaml as _yaml
        from pathlib import Path

        user_types: list[EntityType] = []
        path = Path(yaml_path)
        if path.is_file():
            try:
                with open(path, encoding="utf-8") as f:
                    data = _yaml.safe_load(f) or {}
                for item in data.get("types", []):
                    fields = [
                        EntityField(
                            name=fd.get("name", ""),
                            field_type=fd.get("type", "string"),
                            required=fd.get("required", False),
                            description=fd.get("description", ""),
                            options=fd.get("options", []),
                        )
                        for fd in item.get("fields", [])
                    ]
                    user_types.append(
                        EntityType(
                            id=item["id"],
                            name=item.get("name", item["id"].title()),
                            icon=item.get("icon", "📄"),
                            description=item.get("description", ""),
                            fields=fields,
                            color=item.get("color", "#6366f1"),
                        )
                    )
            except Exception:
                pass  # Fall back to built-in types only

        return cls(user_types=user_types)


# Module-level default registry instance
_default_registry: EntityTypeRegistry | None = None


def get_registry() -> EntityTypeRegistry:
    """Get the default EntityTypeRegistry (singleton)."""
    global _default_registry
    if _default_registry is None:
        _default_registry = EntityTypeRegistry()
    return _default_registry
