from pathlib import Path
import json
import gzip
import uuid
from typing import Any
from src.utils import paths
import hashlib


def write_result_artifact(data: Any, user_id: int, config_hash: str) -> str:
    dest = paths.ARTIFACTS / "results" / str(user_id)
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / f"{config_hash}.json.gz"
    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump(data, f, default=str)
    return str(path)


def write_explanation_artifact(data: Any, user_id: int) -> str:
    dest = paths.ARTIFACTS / "explanations" / str(user_id)
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / f"explanation_{uuid.uuid4().hex}.json"
    # Use a deterministic JSON serialization for hashing
    text = json.dumps(data, ensure_ascii=False, sort_keys=True, default=str, indent=2)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

    # Compute SHA256 of the dumped JSON
    h = hashlib.sha256()
    h.update(text.encode("utf-8"))
    digest = h.hexdigest()

    return {"path": str(path), "hash": digest}


def read_result_artifact(path: str) -> Any:
    p = Path(path)
    if not p.exists():
        return None
    with gzip.open(p, "rt", encoding="utf-8") as f:
        return json.load(f)

def get_symbols():
    symbols = []
    with open(paths.ARTIFACTS / "symbols.json", "r") as f:
        data = json.load(f)
        for category in data.values():
            symbols.extend(category.keys())

    return sorted(symbols)
