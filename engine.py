"""Core prompt assembly engine."""

import logging
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

from adapters import get_adapter
from exceptions import CharacterNotFoundError, LanguageNotFoundError, TemplateNotFoundError

logger = logging.getLogger(__name__)

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
        raise LanguageNotFoundError(f"Language file not found: {filepath}")
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
        raise CharacterNotFoundError(
            f"Character '{char_id}' not found. Available: {', '.join(list_characters())}"
        )
    with open(filepath, encoding="utf-8") as f:
        char_data = yaml.safe_load(f)["character"]
    if "gender" not in char_data:
        char_data["gender"] = {"zh": "中性", "en": "neutral"}
    logger.info("Loaded character '%s'", char_id)
    return char_data


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


def get_defined_outputs(char_data: dict) -> list[str]:
    """Return only output types that a character actually defines in YAML."""
    return sorted(char_data.get("outputs", {}).keys())


def get_compatible_outputs(char_data: dict) -> list[str]:
    """Return output types that can be safely used with this character.

    Includes both defined outputs and available templates.
    For templates without a character definition, fallback is applied.
    """
    return list_outputs(char_data)


# ── Custom Character Builder ───────────────────────────────────────────


@dataclass
class _BilingualDefault:
    """A bilingual field with zh/en defaults."""

    zh: str = ""
    en: str = ""

    def to_dict(self) -> dict[str, str]:
        return {"zh": self.zh, "en": self.en}


def _bd(zh: str, en: str) -> _BilingualDefault:
    """Shorthand factory for _BilingualDefault."""
    return _BilingualDefault(zh=zh, en=en)


@dataclass
class _CharacterForm:
    """Structured form for building a custom character.

    All fields have bilingual defaults — empty input falls back to them.
    """

    name: _BilingualDefault = field(default_factory=lambda: _bd("自訂角色", "Custom Character"))
    gender: _BilingualDefault = field(default_factory=lambda: _bd("中性", "neutral"))
    face_shape: _BilingualDefault = field(default_factory=lambda: _bd("瓜子臉", "oval face"))
    eyes: _BilingualDefault = field(default_factory=lambda: _bd("大眼睛", "big eyes"))
    expression: _BilingualDefault = field(default_factory=lambda: _bd("無表情", "neutral"))
    mouth: _BilingualDefault = field(default_factory=lambda: _bd("閉唇", "closed lips"))
    head_angle: _BilingualDefault = field(default_factory=lambda: _bd("正面", "front facing"))
    action: _BilingualDefault = field(default_factory=lambda: _bd("站立", "standing"))
    hair_style: _BilingualDefault = field(default_factory=lambda: _bd("長髮", "long hair"))
    hair_acc: _BilingualDefault = field(default_factory=lambda: _bd("", ""))
    robe: _BilingualDefault = field(default_factory=lambda: _bd("上衣", "top"))
    collar: _BilingualDefault = field(default_factory=lambda: _bd("圓領", "round collar"))
    waist: _BilingualDefault = field(default_factory=lambda: _bd("腰帶", "belt"))

    @classmethod
    def from_form_dict(cls, form: dict[str, str]) -> "_CharacterForm":
        """Build a form from a flat dict (e.g. CLI args or HTTP POST)."""
        return cls(
            name=_BilingualDefault(
                zh=form.get("char_name", "").strip() or "自訂角色",
                en=form.get("char_name_en", "").strip() or "Custom Character",
            ),
            gender=_BilingualDefault(
                zh=form.get("gender", "").strip() or "中性",
                en=form.get("gender_en", "").strip() or "neutral",
            ),
            face_shape=_BilingualDefault(
                zh=form.get("face_shape", "").strip() or "瓜子臉",
                en=form.get("face_shape_en", "").strip() or "oval face",
            ),
            eyes=_BilingualDefault(
                zh=form.get("eyes", "").strip() or "大眼睛",
                en=form.get("eyes_en", "").strip() or "big eyes",
            ),
            expression=_BilingualDefault(
                zh=form.get("expression", "").strip() or "無表情",
                en=form.get("expression_en", "").strip() or "neutral",
            ),
            mouth=_BilingualDefault(
                zh=form.get("mouth", "").strip() or "閉唇",
                en=form.get("mouth_en", "").strip() or "closed lips",
            ),
            head_angle=_BilingualDefault(
                zh=form.get("head_angle", "").strip() or "正面",
                en=form.get("head_angle_en", "").strip() or "front facing",
            ),
            action=_BilingualDefault(
                zh=form.get("action", "").strip() or "站立",
                en=form.get("action_en", "").strip() or "standing",
            ),
            hair_style=_BilingualDefault(
                zh=form.get("hair_style", "").strip() or "長髮",
                en=form.get("hair_style_en", "").strip() or "long hair",
            ),
            hair_acc=_BilingualDefault(
                zh=form.get("hair_acc", "").strip(),
                en=form.get("hair_acc_en", "").strip(),
            ),
            robe=_BilingualDefault(
                zh=form.get("robe", "").strip() or "上衣",
                en=form.get("robe_en", "").strip() or "top",
            ),
            collar=_BilingualDefault(
                zh=form.get("collar", "").strip() or "圓領",
                en=form.get("collar_en", "").strip() or "round collar",
            ),
            waist=_BilingualDefault(
                zh=form.get("waist", "").strip() or "腰帶",
                en=form.get("waist_en", "").strip() or "belt",
            ),
        )

    def to_character_dict(self) -> dict:
        """Convert this form into a character dict for the pipeline."""
        return {
            "id": "custom",
            "label": self.name.to_dict(),
            "gender": self.gender.to_dict(),
            "base_style": {
                "zh": "動漫角色設定稿，黑白墨線，乾淨線稿，白底，超精細線條",
                "en": (
                    "anime character design sheet, black and white ink, "
                    "clean lineart, white background, ultra-fine lines"
                ),
            },
            "components": {
                "face": {
                    "shape": self.face_shape.to_dict(),
                    "eyes": self.eyes.to_dict(),
                },
                "expression": {
                    "type": self.expression.to_dict(),
                    "mouth": self.mouth.to_dict(),
                },
                "pose": {
                    "head_angle": self.head_angle.to_dict(),
                    "action": self.action.to_dict(),
                },
                "hair": {
                    "style": self.hair_style.to_dict(),
                    "accessories": _split_acc(self.hair_acc.zh, self.hair_acc.en),
                },
                "clothing": {
                    "robe": self.robe.to_dict(),
                    "collar": self.collar.to_dict(),
                    "waist": self.waist.to_dict(),
                },
            },
            "outputs": {},
        }


def build_custom_character(form: dict[str, str], lang: str = "zh") -> dict:
    """Build a character dict from form fields (for custom character).

    Every field has a bilingual default — empty form input falls back to it.
    """
    return _CharacterForm.from_form_dict(form).to_character_dict()


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


@cache
def _get_env() -> Environment:
    """Get (or create) the cached Jinja2 environment."""
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )


def render_template(template_name: str, char_data: dict, lang: str = "zh") -> str:
    """Render a Jinja2 template with character data and i18n."""
    env = _get_env()
    template = env.get_template(template_name)
    i18n = load_i18n(lang)
    return template.render(char=char_data, lang=lang, i18n=i18n)


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
        raise TemplateNotFoundError(
            f"Output type '{output_type}' not found. Available templates: {', '.join(templates)}"
        )

    # 3. Ensure output type entry exists with complete fields
    if "outputs" not in char_data:
        char_data["outputs"] = {}
    if output_type not in char_data["outputs"]:
        char_data["outputs"][output_type] = {
            "label": {"zh": output_type, "en": output_type},
            "style": {"zh": "", "en": ""},
            "variants": [],
        }
    else:
        # Ensure sub-fields exist even for defined outputs
        output_def = char_data["outputs"][output_type]
        if "label" not in output_def:
            output_def["label"] = {"zh": output_type, "en": output_type}
        if "style" not in output_def:
            output_def["style"] = {"zh": "", "en": ""}
        if "variants" not in output_def:
            output_def["variants"] = []

    # 4. Render intermediate format
    template_name = f"{output_type}.j2"
    intermediate = render_template(template_name, char_data, lang=lang)

    # 5. Adapt to model
    adapter = get_adapter(model)
    prompt = adapter.format(intermediate, lang=lang, ar=ar)
    logger.info(
        "Generated prompt: type=%s, model=%s, lang=%s, char=%s",
        output_type,
        model,
        lang,
        char_id or "custom",
    )

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
