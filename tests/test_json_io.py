import json
import os

import pytest

from utils.json_io import atomic_write_json


def test_atomic_write_json_success(tmp_path):
    target = tmp_path / "config.json"
    payload = {"value": 1}

    atomic_write_json(target, payload)

    with target.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    assert data == payload


def test_atomic_write_json_failure_rolls_back(monkeypatch, tmp_path):
    target = tmp_path / "config.json"
    atomic_write_json(target, {"value": 1})
    original = target.read_text(encoding="utf-8")

    def fail_replace(src, dst):
        raise PermissionError("simulated failure")

    monkeypatch.setattr(os, "replace", fail_replace)

    with pytest.raises(PermissionError):
        atomic_write_json(target, {"value": 2})

    assert target.read_text(encoding="utf-8") == original
    temp_files = [path for path in tmp_path.iterdir() if path != target]
    assert temp_files == []

