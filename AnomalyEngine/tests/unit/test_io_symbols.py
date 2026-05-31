import json
from pathlib import Path

from src.utils.io import get_symbols, write_result_artifact, read_result_artifact
from src.utils.paths import ARTIFACTS


def test_get_symbols_reads_file(tmp_path, monkeypatch):
    # create a fake symbols.json in ARTIFACTS
    monkeypatch.setattr("src.utils.paths.ARTIFACTS", tmp_path)
    data = {"sector1": {"AAA": {}, "BBB": {}}, "sector2": {"CCC": {}}}
    (tmp_path / "symbols.json").write_text(json.dumps(data))

    syms = get_symbols()
    assert set(syms) == {"AAA", "BBB", "CCC"}


def test_write_and_read_artifact_gz(tmp_path, monkeypatch):
    monkeypatch.setattr("src.utils.paths.ARTIFACTS", tmp_path)
    payload = {"foo": [1, 2, 3]}
    path = write_result_artifact(payload, user_id=1, config_hash="abc123")
    assert Path(path).exists()
    loaded = read_result_artifact(path)
    assert loaded == payload
