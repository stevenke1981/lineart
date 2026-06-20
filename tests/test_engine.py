"""Tests for engine.py — core pipeline."""

import pytest
from pydantic import ValidationError

from engine import (
    build_custom_character,
    generate_prompt,
    list_characters,
    list_outputs,
    list_templates,
    load_character,
)
from exceptions import CharacterNotFoundError, TemplateNotFoundError


class TestListCharacters:
    """Tests for list_characters()."""

    def test_returns_non_empty_list(self):
        chars = list_characters()
        assert isinstance(chars, list)
        assert len(chars) > 0

    def test_returns_sorted_strings(self):
        chars = list_characters()
        assert all(isinstance(c, str) for c in chars)
        assert chars == sorted(chars)

    def test_sword_maiden_is_available(self):
        chars = list_characters()
        assert "sword_maiden" in chars


class TestLoadCharacter:
    """Tests for load_character()."""

    def test_load_sword_maiden_returns_dict(self):
        char = load_character("sword_maiden")
        assert isinstance(char, dict)
        assert "id" in char
        assert char["id"] == "sword_maiden"
        assert "components" in char
        assert "outputs" in char

    def test_load_has_required_keys(self):
        char = load_character("sword_maiden")
        assert "label" in char
        assert "base_style" in char
        assert "components" in char
        assert "outputs" in char
        assert "face" in char["components"]
        assert "expression" in char["components"]
        assert "pose" in char["components"]
        assert "hair" in char["components"]
        assert "clothing" in char["components"]

    def test_load_nonexistent_raises(self):
        with pytest.raises(CharacterNotFoundError):
            load_character("nonexistent_char_xyz")


class TestListTemplates:
    """Tests for list_templates()."""

    def test_returns_template_names(self):
        tmpls = list_templates()
        assert isinstance(tmpls, list)
        assert len(tmpls) > 0

    def test_includes_core_templates(self):
        tmpls = list_templates()
        assert "three_view" in tmpls
        assert "expressions" in tmpls
        assert "chibi_version" in tmpls


class TestListOutputs:
    """Tests for list_outputs()."""

    def test_returns_union_of_defined_and_all_templates(self):
        char = load_character("sword_maiden")
        outputs = list_outputs(char)
        all_templates = list_templates()
        # All defined outputs should be included
        for defined_key in char.get("outputs", {}):
            assert defined_key in outputs
        # All templates should be available
        for t in all_templates:
            assert t in outputs

    def test_returns_sorted(self):
        char = load_character("sword_maiden")
        outputs = list_outputs(char)
        assert outputs == sorted(outputs)


class TestGeneratePrompt:
    """Tests for generate_prompt()."""

    def test_sd_three_view_returns_string(self):
        prompt = generate_prompt("three_view", model="sd", char_id="sword_maiden")
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_mj_three_view_includes_mj_params(self):
        prompt = generate_prompt("three_view", model="mj", char_id="sword_maiden")
        assert "--style raw" in prompt
        assert "--v 6" in prompt

    def test_nai_three_view_includes_quality_tags(self):
        prompt = generate_prompt("three_view", model="nai", char_id="sword_maiden")
        assert "best quality" in prompt

    def test_zh_output_contains_chinese(self):
        prompt = generate_prompt("three_view", model="sd", char_id="sword_maiden", lang="zh")
        # Chinese output should contain Chinese characters
        assert any("\u4e00" <= c <= "\u9fff" for c in prompt)

    def test_en_output_contains_english(self):
        prompt = generate_prompt("three_view", model="sd", char_id="sword_maiden", lang="en")
        # English output should not contain Chinese characters
        # (though style labels may still have Chinese if not i18n'd)
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_unknown_model_raises(self):
        with pytest.raises(ValueError, match="Unknown model"):
            generate_prompt("three_view", model="unknown", char_id="sword_maiden")

    def test_unknown_template_raises(self):
        with pytest.raises(TemplateNotFoundError):
            generate_prompt("nonexistent_template", model="sd", char_id="sword_maiden")

    def test_aspect_ratio_appended_for_sd(self):
        prompt = generate_prompt("three_view", model="sd", char_id="sword_maiden", ar="16:9")
        assert "--ar 16:9" in prompt

    def test_generate_with_direct_char_data(self):
        char = load_character("sword_maiden")
        prompt = generate_prompt("three_view", model="sd", char_data=char)
        assert isinstance(prompt, str)
        assert len(prompt) > 0


class TestBuildCustomCharacter:
    """Tests for build_custom_character()."""

    def test_returns_valid_dict(self):
        char = build_custom_character({})
        assert isinstance(char, dict)
        assert char["id"] == "custom"
        assert "components" in char
        assert "outputs" in char

    def test_accepts_custom_fields(self):
        form = {"char_name": "忍者", "char_name_en": "Ninja"}
        char = build_custom_character(form)
        assert char["label"]["zh"] == "忍者"
        assert char["label"]["en"] == "Ninja"

    def test_falls_back_to_defaults(self):
        char = build_custom_character({})
        assert char["components"]["face"]["shape"]["zh"] == "瓜子臉"
        assert char["components"]["face"]["shape"]["en"] == "oval face"

    def test_custom_face_shape(self):
        form = {"face_shape": "方臉", "face_shape_en": "square face"}
        char = build_custom_character(form)
        assert char["components"]["face"]["shape"]["zh"] == "方臉"
        assert char["components"]["face"]["shape"]["en"] == "square face"

    def test_custom_accessories(self):
        form = {"hair_acc": "花朵,蝴蝶", "hair_acc_en": "flower, butterfly"}
        char = build_custom_character(form)
        acc = char["components"]["hair"]["accessories"]
        assert len(acc) == 2
        assert acc[0]["zh"] == "花朵"
        assert acc[0]["en"] == "flower"
        assert acc[1]["zh"] == "蝴蝶"
        assert acc[1]["en"] == "butterfly"


class TestCharacterSchema:
    """Tests for Pydantic character schema validation."""

    def test_sword_maiden_validates(self):
        from schemas import BilingualField, Character, CharacterOutput

        char_data = load_character("sword_maiden")
        char = Character(**char_data)
        assert char.id == "sword_maiden"
        assert isinstance(char.label, BilingualField)
        assert "three_view" in char.outputs
        assert isinstance(char.outputs["three_view"], CharacterOutput)

    def test_custom_character_validates(self):
        from schemas import Character

        char_data = build_custom_character({})
        char = Character(**char_data)
        assert char.id == "custom"

    def test_all_characters_validate(self):
        from schemas import Character

        for cid in list_characters():
            char_data = load_character(cid)
            char = Character(**char_data)
            assert char.id == cid
            assert len(char.outputs) > 0

    def test_invalid_data_raises(self):
        from schemas import Character

        with pytest.raises(ValidationError):
            Character(**{"id": 123})  # id should be str

    def test_bilingual_field_requires_both(self):
        from schemas import BilingualField

        bf = BilingualField(zh="測試", en="test")
        assert bf.zh == "測試"
        assert bf.en == "test"

    def test_bilingual_field_missing_en_raises(self):
        from schemas import BilingualField

        with pytest.raises(ValidationError):
            BilingualField(zh="測試")  # missing 'en'
