"""Phase output types and phase definitions."""
from typing import TypedDict, Optional


class ClassifyOutput(TypedDict):
    """Output of classify phase."""
    file_type: str
    source_path: str
    metadata: dict
    detected_language: Optional[str]


class ParseOutput(TypedDict):
    """Output of parse phase."""
    raw_content: str
    sections: list[dict]
    metadata: dict
    parse_time_ms: float


class ExtractOutput(TypedDict):
    """Output of extract phase."""
    claims: list[dict]
    entities: list[dict]
    relations: list[dict]
    extraction_time_ms: float


class MergeOutput(TypedDict):
    """Output of merge phase."""
    merged_claims: list[dict]
    conflicts: list[dict]
    merged_entities: list[dict]


class ValidateOutput(TypedDict):
    """Output of validate phase."""
    validated_claims: list[dict]
    validation_errors: list[dict]
    confidence_scores: dict[str, float]


class StoreOutput(TypedDict):
    """Output of store phase."""
    vault_path: str
    claims_db_path: str
    stored_count: int
    wiki_pages_created: list[str]


# Import phase definitions
from .classify import CLASSIFY_PHASE
from .parse import PARSE_PHASE
from .extract import EXTRACT_PHASE
from .merge import MERGE_PHASE
from .validate import VALIDATE_PHASE
from .store import STORE_PHASE


# All phases in order
DEFAULT_PHASES = [
    CLASSIFY_PHASE,
    PARSE_PHASE,
    EXTRACT_PHASE,
    MERGE_PHASE,
    VALIDATE_PHASE,
    STORE_PHASE,
]


def get_default_phase_list() -> list:
    """Get the default phase list for the ingest pipeline."""
    return DEFAULT_PHASES.copy()


__all__ = [
    'DEFAULT_PHASES',
    'get_default_phase_list',
    'CLASSIFY_PHASE',
    'PARSE_PHASE',
    'EXTRACT_PHASE',
    'MERGE_PHASE',
    'VALIDATE_PHASE',
    'STORE_PHASE',
    'ClassifyOutput',
    'ParseOutput',
    'ExtractOutput',
    'MergeOutput',
    'ValidateOutput',
    'StoreOutput',
]