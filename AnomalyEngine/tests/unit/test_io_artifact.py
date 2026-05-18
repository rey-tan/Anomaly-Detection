import json
import os
from pathlib import Path

from src.utils.io import write_result_artifact, read_result_artifact
from src.utils.paths import ARTIFACTS


def test_write_and_read_artifact(tmp_path, monkeypatch):
    # Redirect ARTIFACTS to tmp_path for isolation
    monkeypatch.setattr("src.utils.paths.ARTIFACTS", tmp_path)

    data = {"metrics": {"a": 1}, "data": [{"x": 1}, {"x": 2}]}
    user_id = 42
    config_hash = "deadbeef"

    path = write_result_artifact(data, user_id, config_hash)
    p = Path(path)
    assert p.exists()

    loaded = read_result_artifact(path)
    assert loaded == data

    # cleanup
    os.remove(path)
