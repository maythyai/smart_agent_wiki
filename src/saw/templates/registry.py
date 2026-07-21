"""Template Registry - 模板注册表.

Loads and manages built-in templates from markdown files.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class Template:
    """A wiki page template."""
    id: str
    name: str
    description: str
    icon: str
    content: str
    frontmatter: dict = field(default_factory=dict)


@dataclass
class TemplateInfo:
    """Template metadata for listing."""
    id: str
    name: str
    description: str
    icon: str
    variables: list[str]


class TemplateRegistry:
    """Registry for built-in wiki templates."""

    # Template metadata
    TEMPLATES = {
        "daily_note": {
            "name": "Daily Note",
            "description": "Daily journal with focus areas and notes",
            "icon": "📅",
        },
        "meeting_notes": {
            "name": "Meeting Notes",
            "description": "Structured meeting notes with agenda and action items",
            "icon": "📝",
        },
        "project_overview": {
            "name": "Project Overview",
            "description": "Project plan with goals, timeline, and resources",
            "icon": "📊",
        },
        "concept_explainer": {
            "name": "Concept Explainer",
            "description": "Explain a concept with definition, examples, and references",
            "icon": "💡",
        },
        "research_summary": {
            "name": "Research Summary",
            "description": "Summarize research findings with sources and analysis",
            "icon": "🔬",
        },
    }

    def __init__(self):
        """Initialize template registry."""
        self._templates_dir = Path(__file__).parent
        self._cache: dict[str, Template] = {}

    def list_templates(self) -> list[TemplateInfo]:
        """List all available templates.

        Returns:
            List of TemplateInfo objects.
        """
        templates = []
        for template_id, meta in self.TEMPLATES.items():
            content = self._read_template_file(template_id)
            if content is not None:
                variables = self._extract_variables(content)
                templates.append(TemplateInfo(
                    id=template_id,
                    name=meta["name"],
                    description=meta["description"],
                    icon=meta["icon"],
                    variables=variables,
                ))
        return templates

    def get_template(self, template_id: str) -> Template | None:
        """Get a template by ID.

        Args:
            template_id: Template identifier.

        Returns:
            Template object or None if not found.
        """
        if template_id in self._cache:
            return self._cache[template_id]

        if template_id not in self.TEMPLATES:
            return None

        content = self._read_template_file(template_id)
        if content is None:
            return None

        meta = self.TEMPLATES[template_id]
        template = Template(
            id=template_id,
            name=meta["name"],
            description=meta["description"],
            icon=meta["icon"],
            content=content,
        )

        self._cache[template_id] = template
        return template

    def apply_template(self, template_id: str, variables: dict[str, str]) -> str | None:
        """Apply a template with variable substitution.

        Args:
            template_id: Template identifier.
            variables: Variable name to value mapping.

        Returns:
            Rendered content string or None if template not found.
        """
        template = self.get_template(template_id)
        if template is None:
            return None

        content = template.content

        # Add default variables
        if "date" not in variables:
            variables["date"] = datetime.now().strftime("%Y-%m-%d")

        # Replace {{variable}} placeholders
        for key, value in variables.items():
            content = content.replace(f"{{{{{key}}}}}", value)

        return content

    def _read_template_file(self, template_id: str) -> str | None:
        """Read template markdown file.

        Args:
            template_id: Template identifier.

        Returns:
            File content or None if not found.
        """
        path = self._templates_dir / f"{template_id}.md"
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def _extract_variables(self, content: str) -> list[str]:
        """Extract {{variable}} placeholders from content.

        Args:
            content: Template content.

        Returns:
            List of unique variable names.
        """
        matches = re.findall(r"\{\{(\w+)\}\}", content)
        # Preserve order, deduplicate
        seen: set[str] = set()
        variables: list[str] = []
        for m in matches:
            if m not in seen:
                seen.add(m)
                variables.append(m)
        return variables


# Singleton instance
_registry: TemplateRegistry | None = None


def get_registry() -> TemplateRegistry:
    """Get or create the template registry singleton."""
    global _registry
    if _registry is None:
        _registry = TemplateRegistry()
    return _registry
