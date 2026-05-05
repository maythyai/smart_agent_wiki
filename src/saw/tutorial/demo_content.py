"""
Demo content generator for Smart Agent Wiki tutorial.

This module creates sample documents for the interactive tutorial
to help new users explore the features.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict


# Sample documents for tutorial
SAMPLE_DOCUMENTS: Dict[str, str] = {
    "project-notes.md": """# Project Notes - Q2 2024

## Overview

This document outlines the key decisions and progress for the Smart Agent Wiki project.

## Timeline

- **Phase 1**: Research and planning (Jan-Feb)
- **Phase 2**: Core development (Mar-May)
- **Phase 3**: Testing and deployment (Jun-Jul)

## Key Decisions

### Architecture

We decided to use a four-layer storage architecture:
1. Vault (immutable originals)
2. Claims (structured assertions)
3. Wiki (synthesized pages)
4. Index (search layer)

### Technology Stack

- Python 3.11+ for backend
- SQLite for local storage
- React for web UI
- FastMCP for integration

## Team

- Alice: Project lead
- Bob: Backend developer
- Carol: Frontend developer
- Dave: Documentation

## Next Steps

1. Complete Phase 2 by end of Q2
2. Begin user testing
3. Prepare for Phase 3 launch

---
*Last updated: May 2024*
""",
    "meeting-summary.md": """# Meeting Summary - Project Review

**Date**: April 15, 2024
**Attendees**: Alice, Bob, Carol, Dave

## Agenda

1. Sprint progress review
2. Technical decisions
3. Timeline updates

## Discussion

### Sprint Progress

The team completed 15 story points this sprint:
- Authentication system (5 pts)
- Document ingestion pipeline (6 pts)
- Basic search functionality (4 pts)

### Technical Decisions

**Approved**: Use LiteLLM for multi-model support
- Rationale: Simplifies integration with multiple LLM providers
- Impact: Reduces vendor lock-in

**Approved**: Implement confidence scoring
- Rationale: Helps users trust the extracted information
- Implementation: 4-tier system (verified → single-source → unverified)

### Timeline Updates

- Original target: June 30
- Updated target: July 15 (2 week buffer added)
- Reason: Additional testing requirements

## Action Items

- [ ] Bob: Complete API documentation
- [ ] Carol: Add visualization features
- [ ] Dave: Update user guide
- [ ] Alice: Schedule stakeholder demo

---
*Meeting notes by Alice*
""",
    "utils.py": '''#!/usr/bin/env python3
"""
Utility functions for Smart Agent Wiki.

This module provides helper functions for common operations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional


def process_data(input_path: Path, output_path: Optional[Path] = None) -> dict:
    """
    Process data from input file and return results.

    Args:
        input_path: Path to input file
        output_path: Optional output path for results

    Returns:
        Dictionary containing processed data

    Example:
        >>> result = process_data(Path("data.json"))
        >>> print(result["status"])
        'success'
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Read and process data
    data = input_path.read_text()
    result = {
        "status": "success",
        "lines": len(data.splitlines()),
        "size": input_path.stat().st_size,
    }

    # Write output if path provided
    if output_path:
        output_path.write_text(str(result))

    return result


def validate_config(config: dict) -> bool:
    """
    Validate configuration dictionary.

    Args:
        config: Configuration dictionary to validate

    Returns:
        True if valid, raises ValueError otherwise
    """
    required_keys = ["name", "version", "storage"]
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required config key: {key}")

    return True


class DataProcessor:
    """Class for processing batches of data."""

    def __init__(self, batch_size: int = 100):
        """Initialize processor with batch size."""
        self.batch_size = batch_size
        self.processed = 0

    def process_batch(self, items: list) -> list:
        """Process a batch of items."""
        results = []
        for item in items[:self.batch_size]:
            results.append(self._process_item(item))
            self.processed += 1
        return results

    def _process_item(self, item) -> dict:
        """Process single item."""
        return {"input": item, "processed": True}


if __name__ == "__main__":
    # Example usage
    result = process_data(Path("example.json"))
    print(f"Processed: {result}")
''',
}


def create_sample_documents(output_dir: Path) -> None:
    """
    Create sample documents for the tutorial.

    Args:
        output_dir: Directory to create documents in
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    for filename, content in SAMPLE_DOCUMENTS.items():
        filepath = output_dir / filename
        filepath.write_text(content)

    print(f"Created {len(SAMPLE_DOCUMENTS)} sample documents in {output_dir}")


def get_sample_document(name: str) -> Optional[str]:
    """
    Get a specific sample document by name.

    Args:
        name: Document filename

    Returns:
        Document content or None if not found
    """
    return SAMPLE_DOCUMENTS.get(name)


def list_sample_documents() -> list[str]:
    """
    List all available sample documents.

    Returns:
        List of document filenames
    """
    return list(SAMPLE_DOCUMENTS.keys())


if __name__ == "__main__":
    # Create demo documents in current directory
    import sys

    output_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("./demo-documents")
    create_sample_documents(output_path)
    print(f"\nSample documents created in: {output_path}")
    print("\nDocuments:")
    for name in list_sample_documents():
        print(f"  - {name}")
