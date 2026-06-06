import json
import hashlib
from src.utils import io as io_utils
from src.utils import paths as paths_module


def test_write_and_read_explanation_artifact(tmp_path, monkeypatch):
    # redirect ARTIFACTS to a tmp dir
    monkeypatch.setattr(paths_module, "ARTIFACTS", tmp_path)
    user_id = 123
    obj = {"model": "test", "summary": "ok", "entries": [1, 2, 3]}
    res = io_utils.write_explanation_artifact(obj, user_id)
    assert "path" in res and "hash" in res
    p = res["path"]
    with open(p, "r", encoding="utf-8") as f:
        text = f.read()
    # recompute hash
    assert hashlib.sha256(text.encode("utf-8")).hexdigest() == res["hash"]
    # read back and compare JSON
    loaded = json.loads(text)
    assert loaded == obj
