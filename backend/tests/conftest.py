import os
import sys

# Ensure the backend root is importable as `app` regardless of CWD.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from app.deps import Credentials


@pytest.fixture
def no_creds() -> Credentials:
    """Empty credentials → exercises the mock / heuristic code paths."""
    return Credentials(
        angel_client_id="",
        angel_api_key="",
        angel_pin="",
        angel_totp_secret="",
        groq_api_key="",
    )
