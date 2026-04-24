import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTEXT_PATH = ROOT / "config" / "llm_context.json"


def load_context() -> dict[str, Any]:
    with open(CONTEXT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
