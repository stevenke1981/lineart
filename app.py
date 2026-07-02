"""Flask Web GUI for Lineart — character design prompt generator.

Features:
- Pre-built characters with multi-select output types
- Custom character form (all fields editable)
- Aspect ratio selection
- Bilingual (zh/en) support
- Prompt history (SQLite) with /history page
- HTMX form submission + Alpine.js UI
"""

import logging

from flask import Flask, Response, jsonify, render_template, request

from engine import (
    build_custom_character,
    generate_prompt,
    generate_prompts,
    get_template_labels,
    list_characters,
    list_outputs,
    list_templates,
    load_character,
)
from exceptions import CharacterNotFoundError, LineartError
from history import (
    clear_history,
    delete_prompt,
    export_history,
    get_history,
    save_prompt,
)

logger = logging.getLogger(__name__)
app = Flask(__name__)

AR_PRESETS = [
    {
        "key": "3:4",
        "label_zh": "直式 3:4（角色設定稿）",
        "label_en": "Portrait 3:4 (character sheet)",
    },
    {"key": "1:1", "label_zh": "方形 1:1（頭像構圖）", "label_en": "Square 1:1 (portrait)"},
    {"key": "4:3", "label_zh": "橫式 4:3（半身構圖）", "label_en": "Landscape 4:3 (half body)"},
    {"key": "16:9", "label_zh": "寬螢幕 16:9（場景構圖）", "label_en": "Widescreen 16:9 (scene)"},
    {"key": "9:16", "label_zh": "直立 9:16（全身站立）", "label_en": "Vertical 9:16 (full body)"},
]

MODELS = [
    {"key": "sd", "label_zh": "Stable Diffusion", "label_en": "Stable Diffusion"},
    {"key": "mj", "label_zh": "MidJourney", "label_en": "MidJourney"},
    {"key": "nai", "label_zh": "NovelAI", "label_en": "NovelAI"},
    {"key": "dalle", "label_zh": "DALL·E 3", "label_en": "DALL·E 3"},
    {"key": "comfyui", "label_zh": "ComfyUI", "label_en": "ComfyUI"},
]

LANGS = [
    {"key": "zh", "label": "中文"},
    {"key": "en", "label": "English"},
]

GENDER_OPTIONS = [
    {"key": "male", "label_zh": "男", "label_en": "male"},
    {"key": "female", "label_zh": "女", "label_en": "female"},
    {"key": "neutral", "label_zh": "中性", "label_en": "neutral"},
    {"key": "genderless", "label_zh": "無性別", "label_en": "genderless"},
]

_GENDER_MAP = {
    "male": {"zh": "男", "en": "male"},
    "female": {"zh": "女", "en": "female"},
    "neutral": {"zh": "中性", "en": "neutral"},
    "genderless": {"zh": "無性別", "en": "genderless"},
}

# ── Metadata Helpers ───────────────────────────────────────────────

def get_characters_meta() -> list[dict]:
    """Return list of {id, label_zh, label_en, outputs}."""
    meta = []
    for cid in list_characters():
        data = load_character(cid)
        output_keys = list_outputs(data)
        char_outputs = data.get("outputs", {})
        meta.append(
            {
                "id": cid,
                "label_zh": data.get("label", {}).get("zh", cid),
                "label_en": data.get("label", {}).get("en", cid),
                "gender_zh": data.get("gender", {}).get("zh", ""),
                "gender_en": data.get("gender", {}).get("en", ""),
                "outputs": [
                    {
                        "key": k,
                        "zh": char_outputs[k]["label"]["zh"] if k in char_outputs else k,
                        "en": char_outputs[k]["label"]["en"] if k in char_outputs else k,
                    }
                    for k in output_keys
                ],
            }
        )
    return meta


def get_all_templates_meta() -> list[dict]:
    """Return list of {key, zh, en} for all templates."""
    zh_labels = get_template_labels("zh")
    en_labels = get_template_labels("en")
    return [
        {
            "key": t,
            "zh": zh_labels.get(t, t),
            "en": en_labels.get(t, t),
        }
        for t in list_templates()
    ]


def _build_char_data_from_form(form: dict) -> dict | None:
    """Build character data from form. Returns None for prebuilt mode errors."""
    mode = form.get("mode", "prebuilt")
    lang = form.get("lang", "zh")

    if mode == "custom":
        return build_custom_character(form, lang=lang)

    char_id = form.get("character", "")
    if not char_id:
        return None
    char_data = load_character(char_id)
    # Apply gender override
    gender_val = form.get("gender", "").strip()
    if gender_val and gender_val in _GENDER_MAP:
        char_data["gender"] = _GENDER_MAP[gender_val]
    return char_data


def _render_result_cards(results: dict[str, str], lang: str = "zh") -> str:
    """Render result HTML fragments for HTMX swap."""
    labels = get_template_labels(lang)
    copy_btn = "📋 複製" if lang == "zh" else "📋 Copy"
    copy_done = "✅ 已複製" if lang == "zh" else "✅ Copied"
    cards = [
        {
            "label": labels.get(output_type, output_type),
            "prompt": prompt,
            "rows": max(4, prompt.count("\n") + 2),
            "copy_btn": copy_btn,
            "copy_done": copy_done,
        }
        for output_type, prompt in results.items()
    ]
    return render_template("_result_cards.html", cards=cards)


def _render_error(message: str) -> str:
    """Render error HTML fragment for HTMX swap."""
    return render_template("_error.html", message=message)


# ── Main Routes ────────────────────────────────────────────────────

@app.route("/")
def index() -> str:
    chars = get_characters_meta()
    templates = get_all_templates_meta()
    return render_template(
        "index.html",
        characters=chars,
        templates=templates,
        models=MODELS,
        langs=LANGS,
        ar_presets=AR_PRESETS,
        gender_options=GENDER_OPTIONS,
    )


@app.route("/generate", methods=["POST"])
def generate() -> str | Response | tuple[str | Response, int]:
    mode = request.form.get("mode", "prebuilt")
    model = request.form.get("model", "sd")
    lang = request.form.get("lang", "zh")
    ar = request.form.get("ar", "")
    output_types_str = request.form.get("output_types", "")
    output_types = [o.strip() for o in output_types_str.split(",") if o.strip()]
    is_htmx = request.headers.get("HX-Request") == "true"

    if not output_types:
        msg = "請選擇至少一個輸出類型" if lang == "zh" else "Please select at least one output type"
        if is_htmx:
            return _render_error(msg), 400
        return jsonify({"error": msg}), 400

    try:
        char_data = _build_char_data_from_form(request.form)
        if char_data is None:
            msg = "請選擇角色" if lang == "zh" else "Please select a character"
            if is_htmx:
                return _render_error(msg), 400
            return jsonify({"error": msg}), 400

        char_id = request.form.get("character", "") if mode == "prebuilt" else "custom"
        if mode == "prebuilt":
            char_label = char_data.get("label", {}).get("zh", char_id)
        else:
            char_label = char_data.get("label", {}).get("zh", "")
        gender = char_data.get("gender", {}).get("zh", "")

        if len(output_types) == 1:
            prompt = generate_prompt(
                output_type=output_types[0],
                model=model, lang=lang, ar=ar,
                char_id=char_id, char_data=char_data,
            )
            results = {output_types[0]: prompt}
        else:
            results = generate_prompts(
                output_types=output_types,
                model=model, lang=lang, ar=ar,
                char_id=char_id, char_data=char_data,
            )

        # Save each output to history
        for ot, prompt in results.items():
            try:
                save_prompt(
                    mode=mode, character=char_id, char_label=char_label,
                    gender=gender, model=model, lang=lang,
                    ar=ar, output_type=ot, prompt=prompt,
                )
            except Exception:
                logger.warning("Failed to save prompt to history", exc_info=True)

        if is_htmx:
            return _render_result_cards(results, lang=lang)

        return jsonify({"results": results})

    except LineartError as e:
        msg = str(e)
        if is_htmx:
            return _render_error(msg), 400
        return jsonify({"error": msg}), 400
    except Exception as e:
        logger.error("Generation failed", exc_info=True)
        msg = str(e)
        if is_htmx:
            return _render_error(msg), 400
        return jsonify({"error": msg}), 400


@app.route("/api/characters")
def api_characters() -> Response | tuple[Response, int]:
    return jsonify(get_characters_meta())


@app.route("/api/templates")
def api_templates() -> Response | tuple[Response, int]:
    return jsonify(get_all_templates_meta())


@app.route("/api/outputs/<char_id>")
def api_outputs(char_id: str) -> Response | tuple[Response, int]:
    try:
        data = load_character(char_id)
        outputs = list_outputs(data)
        char_outputs = data.get("outputs", {})
        result = []
        for k in outputs:
            if k in char_outputs:
                result.append({
                    "key": k,
                    "zh": char_outputs[k]["label"]["zh"],
                    "en": char_outputs[k]["label"]["en"],
                })
            else:
                result.append({"key": k, "zh": k, "en": k})
        return jsonify(result)
    except CharacterNotFoundError:
        return jsonify({"error": f"Character '{char_id}' not found"}), 404
    except LineartError as e:
        return jsonify({"error": str(e)}), 400


# ── History Routes ─────────────────────────────────────────────────

@app.route("/history")
def history_page() -> str:
    """Prompt history management page."""
    templates = get_all_templates_meta()
    return render_template(
        "history.html",
        models=MODELS,
        templates=templates,
    )


@app.route("/history/data")
def history_data() -> Response:
    """JSON endpoint for HTMX paginated history."""
    page = request.args.get("page", 1, type=int)
    model = request.args.get("model", "", type=str) or None
    output_type = request.args.get("output_type", "", type=str) or None
    data = get_history(page=page, model=model, output_type=output_type)
    return jsonify(data)


@app.route("/history/<int:prompt_id>", methods=["DELETE"])
def history_delete(prompt_id: int) -> Response | tuple[Response, int]:
    """Delete a single history record."""
    deleted = delete_prompt(prompt_id)
    if deleted:
        return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404


@app.route("/history/clear", methods=["POST"])
def history_clear() -> Response:
    """Clear all history records."""
    count = clear_history()
    return jsonify({"ok": True, "deleted": count})


@app.route("/history/export")
def history_export() -> Response | tuple[Response, int]:
    """Export history as JSON or CSV."""
    fmt = request.args.get("format", "json")
    if fmt not in ("json", "csv"):
        return jsonify({"error": "Unsupported format"}), 400

    content = export_history(format=fmt)
    content_type = "application/json" if fmt == "json" else "text/csv; charset=utf-8-sig"
    filename = f"lineart_history.{fmt}"
    return Response(
        content,
        mimetype=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
