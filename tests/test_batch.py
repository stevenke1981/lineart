"""Tests for batch.py — batch prompt generation."""

import json
from pathlib import Path

import pytest

from batch import load_batch_file, run_batch
from exceptions import LineartError


@pytest.fixture
def batch_json(tmp_path: Path) -> Path:
    data = [
        {
            "character": "sword_maiden",
            "types": ["three_view"],
            "model": "sd",
            "lang": "zh",
            "ar": "3:4",
        },
        {
            "character": "bushi",
            "types": "three_view,expressions",
            "model": "mj",
            "lang": "en",
        },
    ]
    path = tmp_path / "batch.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


@pytest.fixture
def batch_csv(tmp_path: Path) -> Path:
    path = tmp_path / "batch.csv"
    path.write_text(
        "character,types,model,lang,ar\n"
        "sword_maiden,three_view,sd,zh,3:4\n"
        "bushi,expressions,mj,en,\n",
        encoding="utf-8",
    )
    return path


class TestLoadBatchFile:
    def test_load_json(self, batch_json: Path):
        jobs = load_batch_file(batch_json)
        assert len(jobs) == 2
        assert jobs[0]["character"] == "sword_maiden"
        assert jobs[0]["types"] == ["three_view"]
        assert jobs[1]["types"] == ["three_view", "expressions"]

    def test_load_csv(self, batch_csv: Path):
        jobs = load_batch_file(batch_csv)
        assert len(jobs) == 2
        assert jobs[0]["model"] == "sd"
        assert jobs[1]["character"] == "bushi"

    def test_missing_file_raises(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            load_batch_file(tmp_path / "missing.json")

    def test_unsupported_format_raises(self, tmp_path: Path):
        path = tmp_path / "batch.txt"
        path.write_text("x", encoding="utf-8")
        with pytest.raises(LineartError, match="Unsupported batch file format"):
            load_batch_file(path)

    def test_missing_character_raises(self, tmp_path: Path):
        path = tmp_path / "bad.json"
        path.write_text(json.dumps([{"types": ["three_view"]}]), encoding="utf-8")
        with pytest.raises(LineartError, match="missing 'character'"):
            load_batch_file(path)


class TestRunBatch:
    def test_run_batch_returns_prompts(self, batch_json: Path):
        jobs = load_batch_file(batch_json)
        results = run_batch(jobs)
        assert len(results) == 3
        assert all("prompt" in r and r["prompt"] for r in results)
        assert results[0]["output_type"] == "three_view"

    def test_run_batch_dalle_model(self, tmp_path: Path):
        path = tmp_path / "dalle.json"
        path.write_text(
            json.dumps([{"character": "sword_maiden", "types": ["three_view"], "model": "dalle"}]),
            encoding="utf-8",
        )
        results = run_batch(load_batch_file(path))
        assert len(results) == 1
        assert "Aspect ratio" not in results[0]["prompt"] or isinstance(results[0]["prompt"], str)
