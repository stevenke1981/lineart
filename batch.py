"""Batch prompt generation from JSON or CSV input files."""

import csv
import json
import logging
from pathlib import Path

from engine import build_custom_character, generate_prompts, load_character
from exceptions import LineartError

logger = logging.getLogger(__name__)

def _normalize_job(raw: dict) -> dict:
    """Normalize a single batch job dict."""
    character = str(raw.get("character", "")).strip()
    types_raw = raw.get("types", raw.get("type", ""))
    if isinstance(types_raw, list):
        types = [str(t).strip() for t in types_raw if str(t).strip()]
    else:
        types = [t.strip() for t in str(types_raw).split(",") if t.strip()]

    if not character:
        raise LineartError("Batch job missing 'character' field")
    if not types:
        raise LineartError(f"Batch job for '{character}' missing 'types' field")

    return {
        "character": character,
        "types": types,
        "model": str(raw.get("model", "sd")).strip() or "sd",
        "lang": str(raw.get("lang", "zh")).strip() or "zh",
        "ar": str(raw.get("ar", "")).strip(),
        "custom": bool(raw.get("custom", False)),
        "form": raw.get("form", {}),
    }


def load_batch_file(filepath: str | Path) -> list[dict]:
    """Load batch jobs from a JSON or CSV file."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Batch file not found: {path}")

    suffix = path.suffix.lower()
    if suffix == ".json":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            data = data.get("jobs", data.get("items", [data]))
        if not isinstance(data, list):
            raise LineartError("Batch JSON must be a list of job objects")
        return [_normalize_job(job) for job in data]

    if suffix == ".csv":
        jobs: list[dict] = []
        with open(path, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                jobs.append(_normalize_job(row))
        return jobs

    raise LineartError(f"Unsupported batch file format: {suffix} (use .json or .csv)")


def run_batch(jobs: list[dict]) -> list[dict]:
    """Execute batch jobs and return result records."""
    results: list[dict] = []

    for index, job in enumerate(jobs, start=1):
        char_id = job["character"]
        logger.info("Batch job %d: character=%s types=%s", index, char_id, job["types"])

        if job["custom"]:
            char_data = build_custom_character(job.get("form", {}), lang=job["lang"])
            resolved_id = "custom"
        else:
            char_data = load_character(char_id)
            resolved_id = char_id

        prompts = generate_prompts(
            output_types=job["types"],
            model=job["model"],
            lang=job["lang"],
            ar=job["ar"],
            char_id=resolved_id,
            char_data=char_data,
        )

        for output_type, prompt in prompts.items():
            results.append(
                {
                    "character": resolved_id,
                    "char_label": char_data.get("label", {}).get("zh", resolved_id),
                    "output_type": output_type,
                    "model": job["model"],
                    "lang": job["lang"],
                    "ar": job["ar"],
                    "prompt": prompt,
                }
            )

    return results
