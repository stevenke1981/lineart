"""Flask Web GUI for Lineart — character design prompt generator.

Features:
- Pre-built characters with multi-select output types
- Custom character form (all fields editable)
- Aspect ratio selection
- Bilingual (zh/en) support
"""

from flask import Flask, jsonify, render_template, request

from engine import (
    build_custom_character,
    generate_prompt,
    generate_prompts,
    list_characters,
    list_outputs,
    list_templates,
    load_character,
)

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
]

LANGS = [
    {"key": "zh", "label": "中文"},
    {"key": "en", "label": "English"},
]


# ── Metadata ───────────────────────────────────────────────────────────
def get_characters_meta():
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


def get_all_templates_meta():
    """Return list of {key, zh, en} for all templates."""
    tmpls = list_templates()
    # Friendly names for templates
    names = {
        "three_view": ("人物三視圖", "Three-view Sheet"),
        "expressions": ("表情演變五連圖", "Expression Evolution"),
        "clothing_breakdown": ("服裝拆解圖", "Clothing Breakdown"),
        "hair_breakdown": ("髮飾拆解圖", "Hair Accessory Breakdown"),
        "action_pose": ("動態姿勢集", "Action Poses"),
        "chibi_version": ("Q版化", "Chibi Version"),
        "color_scheme": ("配色方案", "Color Scheme"),
        "weapon_prop": ("武器道具拆解", "Weapon/Prop Breakdown"),
    }
    return [{"key": t, "zh": names.get(t, (t, t))[0], "en": names.get(t, (t, t))[1]} for t in tmpls]


# ── Routes ────────────────────────────────────────────────────────────


@app.route("/")
def index():
    chars = get_characters_meta()
    templates = get_all_templates_meta()
    return render_template(
        "index.html",
        characters=chars,
        templates=templates,
        models=MODELS,
        langs=LANGS,
        ar_presets=AR_PRESETS,
    )


@app.route("/generate", methods=["POST"])
def generate():
    mode = request.form.get("mode", "prebuilt")  # 'prebuilt' | 'custom'
    model = request.form.get("model", "sd")
    lang = request.form.get("lang", "zh")
    ar = request.form.get("ar", "")
    output_types_str = request.form.get("output_types", "")
    output_types = [o.strip() for o in output_types_str.split(",") if o.strip()]

    if not output_types:
        return jsonify({"error": "請選擇至少一個輸出類型"}), 400

    try:
        if mode == "custom":
            char_data = build_custom_character(request.form, lang=lang)
            char_id = ""
        else:
            char_id = request.form.get("character", "")
            if not char_id:
                return jsonify({"error": "請選擇角色"}), 400
            char_data = None

        if len(output_types) == 1:
            prompt = generate_prompt(
                output_type=output_types[0],
                model=model,
                lang=lang,
                ar=ar,
                char_id=char_id,
                char_data=char_data,
            )
            return jsonify({"results": {output_types[0]: prompt}})
        else:
            results = generate_prompts(
                output_types=output_types,
                model=model,
                lang=lang,
                ar=ar,
                char_id=char_id,
                char_data=char_data,
            )
            return jsonify({"results": results})

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/characters")
def api_characters():
    return jsonify(get_characters_meta())


@app.route("/api/templates")
def api_templates():
    return jsonify(get_all_templates_meta())


@app.route("/api/outputs/<char_id>")
def api_outputs(char_id):
    try:
        data = load_character(char_id)
        outputs = list_outputs(data)
        char_outputs = data.get("outputs", {})
        result = []
        for k in outputs:
            if k in char_outputs:
                result.append(
                    {
                        "key": k,
                        "zh": char_outputs[k]["label"]["zh"],
                        "en": char_outputs[k]["label"]["en"],
                    }
                )
            else:
                result.append({"key": k, "zh": k, "en": k})
        return jsonify(result)
    except FileNotFoundError:
        return jsonify({"error": f"Character '{char_id}' not found"}), 404


if __name__ == "__main__":
    app.run(debug=True, port=5000)
