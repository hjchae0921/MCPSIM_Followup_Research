"""The OpenAI client used for embedding queries and the default coder.

OPENAI_API_KEY takes precedence over the Git-ignored .openai_key at the repo root.

coder/coder.py can build a separate client when a coder gateway is configured.
"""

import os
from pathlib import Path

from openai import OpenAI

if not os.environ.get("OPENAI_API_KEY"):
    key_file = Path(__file__).resolve().parents[1] / ".openai_key"
    if key_file.exists():
        os.environ["OPENAI_API_KEY"] = key_file.read_text().strip()

# Importing the CLI, inspecting prompts and running offline tests need no key.
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY") or "not-configured")


def require_credentials(api_client):
    if getattr(api_client, "api_key", None) == "not-configured":
        raise ValueError("Set OPENAI_API_KEY or .openai_key before model/embedding generation.")
