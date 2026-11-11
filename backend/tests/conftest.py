import os

import pytest

os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic-key")
os.environ.setdefault("VOYAGE_API_KEY", "test-voyage-key")

requires_voyage_key = pytest.mark.skipif(
    os.environ["VOYAGE_API_KEY"] == "test-voyage-key",
    reason="needs a real VOYAGE_API_KEY to call the live Voyage API",
)
