"""Flask Web GUI for Lineart — character design prompt generator."""

from flask import Flask, render_template, request, jsonify
from engine import (
    generate_prompt,
    list_characters,
    load_character,
    list_outputs,
)

app = Flask(__name__)

# ── Cache for character metadata ──────────────────────────────────────
def get_characters_meta():
    """Return list of {id, label_zh, label_en, outputs}."""
    meta = []
    for cid in list_characters():
        data = load_character(cid)
        outputs = list_outputs(data)
        meta.append({
            "id": cid,
            "label_zh": data.get("label", {}).get("zh", cid),
            "label_en": data.get("label", {}).get("en", cid),
            "outputs": [
                {"key": k, "zh": v.get("label", {}).get("zh", k), "en": v.get("label", {}).get("en", k)}
                for k, v in data.get("outputs", {}).items()
            ],
        })
    return meta


# ── Routes ────────────────────────────────────────────────────────────

@app.route("/")
def index():
    chars = get_characters_meta()
    return render_template("index.html",
                           characters=chars,
                           models=[
                               {"key": "sd", "label_zh": "Stable Diffusion", "label_en": "Stable Diffusion"},
                               {"key": "mj", "label_zh": "MidJourney", "label_en": "MidJourney"},
                               {"key": "nai", "label_zh": "NovelAI", "label_en": "NovelAI"},
                           ],
                           langs=[
                               {"key": "zh", "label": "中文"},
                               {"key": "en", "label": "English"},
                           ])


@app.route("/generate", methods=["POST"])
def generate():
    char_id = request.form.get("character", "")
    output_type = request.form.get("output", "")
    model = request.form.get("model", "sd")
    lang = request.form.get("lang", "zh")

    if not char_id or not output_type:
        return jsonify({"error": "請選擇角色和輸出類型"}), 400

    try:
        prompt = generate_prompt(char_id, output_type, model, lang)
        return jsonify({"prompt": prompt})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/characters")
def api_characters():
    return jsonify(get_characters_meta())


@app.route("/api/outputs/<char_id>")
def api_outputs(char_id):
    try:
        data = load_character(char_id)
        outputs = list_outputs(data)
        result = []
        for k in outputs:
            v = data["outputs"][k]["label"]
            result.append({"key": k, "zh": v.get("zh", k), "en": v.get("en", k)})
        return jsonify(result)
    except FileNotFoundError:
        return jsonify({"error": f"Character '{char_id}' not found"}), 404


if __name__ == "__main__":
    app.run(debug=True, port=5000)
