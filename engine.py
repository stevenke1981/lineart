"""Core prompt assembly engine."""

from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

from adapters import get_adapter

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
    with open(filepath, encoding="utf-8") as f:
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
            f"Character '{char_id}' not found. Available: {', '.join(list_characters())}"
        )
    with open(filepath, encoding="utf-8") as f:
        return yaml.safe_load(f)["character"]


def list_templates() -> list[str]:
    """Return available template names (from templates/ directory)."""
    tmpls = []
    for f in TEMPLATES_DIR.glob("*.j2"):
        tmpls.append(f.stem)
    return sorted(tmpls)


def list_outputs(char_data: dict) -> list[str]:
    """Return available output types for a character (defined + all templates)."""
    defined = set(char_data.get("outputs", {}).keys())
    available = set(list_templates())
    return sorted(defined | available)


# ── Custom Character Builder ───────────────────────────────────────────
def build_custom_character(form: dict, lang: str = "zh") -> dict:
    """Build a character dict from form fields (for custom character).

    Every field has a bilingual default — empty form input falls back to it.
    """
    # ── Defaults ──────────────────────────────────────────────────────
    defaults = {
        "char_name": ("自訂角色", "Custom Character"),
        "char_name_en": ("自訂角色", "Custom Character"),
        "face_shape": ("瓜子臉", "oval face"),
        "face_shape_en": ("瓜子臉", "oval face"),
        "eyes": ("大眼睛", "big eyes"),
        "eyes_en": ("大眼睛", "big eyes"),
        "expression": ("無表情", "neutral"),
        "expression_en": ("無表情", "neutral"),
        "mouth": ("閉唇", "closed lips"),
        "mouth_en": ("閉唇", "closed lips"),
        "head_angle": ("正面", "front facing"),
        "head_angle_en": ("正面", "front facing"),
        "action": ("站立", "standing"),
        "action_en": ("站立", "standing"),
        "hair_style": ("長髮", "long hair"),
        "hair_style_en": ("長髮", "long hair"),
        "hair_acc": ("", ""),
        "hair_acc_en": ("", ""),
        "robe": ("上衣", "top"),
        "robe_en": ("上衣", "top"),
        "collar": ("圓領", "round collar"),
        "collar_en": ("圓領", "round collar"),
        "waist": ("腰帶", "belt"),
        "waist_en": ("腰帶", "belt"),
    }

    def val(key):
        raw = form.get(key, "").strip()
        if raw:
            return raw
        # Fall back to default
        zh_def, en_def = defaults.get(key, ("", ""))
        if key.endswith("_en"):
            return en_def
        return zh_def

    def t(zh_key, en_key):
        return {"zh": val(zh_key), "en": val(en_key)}

    char = {
        "id": "custom",
        "label": t("char_name", "char_name_en"),
        "base_style": {
            "zh": "動漫角色設定稿，黑白墨線，乾淨線稿，白底，超精細線條",
            "en": (
                "anime character design sheet, black and white ink, "
                "clean lineart, white background, ultra-fine lines"
            ),
        },
        "components": {
            "face": {
                "shape": t("face_shape", "face_shape_en"),
                "eyes": t("eyes", "eyes_en"),
            },
            "expression": {
                "type": t("expression", "expression_en"),
                "mouth": t("mouth", "mouth_en"),
            },
            "pose": {
                "head_angle": t("head_angle", "head_angle_en"),
                "action": t("action", "action_en"),
            },
            "hair": {
                "style": t("hair_style", "hair_style_en"),
                "accessories": _split_acc(val("hair_acc"), val("hair_acc_en")),
            },
            "clothing": {
                "robe": t("robe", "robe_en"),
                "collar": t("collar", "collar_en"),
                "waist": t("waist", "waist_en"),
            },
        },
        "outputs": {},
    }
    return char


def _split_acc(zh_text: str, en_text: str) -> list[dict]:
    """Split comma-separated accessories into bilingual list."""
    zh_items = [x.strip() for x in zh_text.split(",") if x.strip()]
    en_items = [x.strip() for x in en_text.split(",") if x.strip()]
    max_len = max(len(zh_items), len(en_items), 1)
    result = []
    for i in range(max_len):
        result.append(
            {
                "zh": zh_items[i] if i < len(zh_items) else "",
                "en": en_items[i] if i < len(en_items) else "",
            }
        )
    return result


# ── Template Engine ────────────────────────────────────────────────────
_jinja_env: Environment | None = None


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
    output_type: str,
    model: str = "sd",
    lang: str = "zh",
    ar: str = "",
    char_id: str = "",
    char_data: dict | None = None,
) -> str:
    """Full pipeline: load → render → adapt → return.

    Args:
        output_type: Template name (e.g. 'three_view')
        model: 'sd' | 'mj' | 'nai'
        lang: 'zh' | 'en'
        ar: Aspect ratio (e.g. '3:4', '16:9')
        char_id: Load from YAML (used when char_data is None)
        char_data: Direct character dict (skips YAML load)

    Returns:
        Assembled prompt string
    """
    # 1. Load character
    if char_data is None:
        char_data = load_character(char_id)

    # 2. Validate output type
    templates = list_templates()
    if output_type not in templates:
        raise ValueError(
            f"Output type '{output_type}' not found. Available templates: {', '.join(templates)}"
        )

    # 3. Ensure output type entry exists
    if "outputs" not in char_data:
        char_data["outputs"] = {}
    if output_type not in char_data["outputs"]:
        char_data["outputs"][output_type] = {
            "label": {"zh": output_type, "en": output_type},
            "style": {"zh": "", "en": ""},
        }

    # 4. Render intermediate format
    template_name = f"{output_type}.j2"
    intermediate = render_template(template_name, char_data, lang=lang)

    # 5. Adapt to model
    adapter = get_adapter(model)
    prompt = adapter.format(intermediate, lang=lang, ar=ar)

    return prompt


def generate_prompts(
    output_types: list[str],
    model: str = "sd",
    lang: str = "zh",
    ar: str = "",
    char_id: str = "",
    char_data: dict | None = None,
) -> dict[str, str]:
    """Generate prompts for multiple output types at once.

    Returns dict mapping output_type → prompt string.
    """
    results = {}
    for ot in output_types:
        results[ot] = generate_prompt(
            output_type=ot,
            model=model,
            lang=lang,
            ar=ar,
            char_id=char_id,
            char_data=char_data,
        )
    return results
