from pathlib import Path
import json
import gzip
from typing import Any

from src.utils.paths import ARTIFACTS


def write_result_artifact(data: Any, user_id: int, config_hash: str) -> str:
    dest = ARTIFACTS / "results" / str(user_id)
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / f"{config_hash}.json.gz"
    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump(data, f, default=str)
    return str(path)


def read_result_artifact(path: str) -> Any:
    p = Path(path)
    if not p.exists():
        return None
    with gzip.open(p, "rt", encoding="utf-8") as f:
        return json.load(f)
