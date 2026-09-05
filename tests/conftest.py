"""Root conftest: set env vars before any test module imports litellm.

v1.12.0: litellm is imported at module level in ``saw.adapters.embeddings``
(same as ``saw.adapters.llm.router``). Without this env var, litellm tries
to fetch a remote model-cost map on first import, which times out in the
CI/runner sandbox and adds ~7 s per process. Setting it here (before any
test module is collected) forces the local backup.
"""
import os

os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")
