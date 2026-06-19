"""Core prompt assembly engine."""

import os
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from typing import Optional

from adapters import get_adapter, BaseAdapter

# ── Paths ──────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent
CHARACTERS_DIR = PROJECT_ROOT / "characters"
TEMPLATES_DIR = PROJECT_ROOT / "templates"
I18N_DIR = PROJECT_ROOT / "i18n"


# ── I18n ───────────────────────────────────────────────────────────────
def load_i18n(lang: str = "zh") -> dict:
    """Load a language dictionary."""
    filepath = I18N_DIR / f"{lang}.yaml"
    if not filepath.exists():
        raise FileNotFoundError(f"Language file not found: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# ── Characters ─────────────────────────────────────────────────────────
def list_characters() -> list[str]:
    """Return available character IDs."""
    chars = []
    for f in CHARACTERS_DIR.glob("*.yaml"):
        chars.append(f.stem)
    return sorted(chars)


def load_character(char_id: str) -> dict:
    """Load a character definition by ID."""
    filepath = CHARACTERS_DIR / f"{char_id}.yaml"
    if not filepath.exists():
        raise FileNotFoundError(
            f"Character '{char_id}' not found. "
            f"Available: {', '.join(list_characters())}"
        )
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["character"]


def list_outputs(char_data: dict) -> list[str]:
    """Return available output types for a character."""
    return list(char_data.get("outputs", {}).keys())


# ── Template Engine ────────────────────────────────────────────────────
_jinja_env: Optional[Environment] = None


def _get_env() -> Environment:
    global _jinja_env
    if _jinja_env is None:
        _jinja_env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=select_autoescape(["html", "xml"]),
        )
    return _jinja_env


def render_template(template_name: str, char_data: dict, lang: str = "zh") -> str:
    """Render a Jinja2 template with character data."""
    env = _get_env()
    template = env.get_template(template_name)
    return template.render(char=char_data, lang=lang)


# ── Assembly Pipeline ──────────────────────────────────────────────────
def generate_prompt(
    char_id: str,
    output_type: str,
    model: str = "sd",
    lang: str = "zh",
) -> str:
    """Full pipeline: load → render → adapt → return."""
    # 1. Load character
    char_data = load_character(char_id)

    # 2. Validate output type
    outputs = list_outputs(char_data)
    if output_type not in outputs:
        raise ValueError(
            f"Output type '{output_type}' not found for '{char_id}'. "
            f"Available: {', '.join(outputs)}"
        )

    # 3. Render intermediate format
    template_name = f"{output_type}.j2"
    intermediate = render_template(template_name, char_data, lang=lang)

    # 4. Adapt to model
    adapter = get_adapter(model)
    prompt = adapter.format(intermediate, lang=lang)

    return prompt
