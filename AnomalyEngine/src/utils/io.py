from pathlib import Path
import json
import gzip
import uuid
from typing import Any
from src.utils.paths import ARTIFACTS


def write_result_artifact(data: Any, user_id: int, config_hash: str) -> str:
    dest = ARTIFACTS / "results" / str(user_id)
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / f"{config_hash}.json.gz"
    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump(data, f, default=str)
    return str(path)


def write_explanation_artifact(data: Any, user_id: int) -> str:
    dest = ARTIFACTS / "explanations" / str(user_id)
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / f"explanation_{uuid.uuid4().hex}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, default=str, indent=2)
    return str(path)


def read_result_artifact(path: str) -> Any:
    p = Path(path)
    if not p.exists():
        return None
    with gzip.open(p, "rt", encoding="utf-8") as f:
        return json.load(f)

def get_symbols():
    symbols = []
    with open(ARTIFACTS / "symbols.json", "r") as f:
        data = json.load(f)
        for category in data.values():
            symbols.extend(category.keys())

    return sorted(symbols)
