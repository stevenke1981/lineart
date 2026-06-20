"""Tests for adapters/ — model-specific prompt formatters."""

import pytest

from adapters import get_adapter
from adapters.midjourney import MidjourneyAdapter
from adapters.novelai import NovelAIAdapter
from adapters.stable_diffusion import StableDiffusionAdapter
from exceptions import ModelNotSupportedError

SAMPLE_INTERMEDIATE = """###BASE###
anime character sheet, black and white ink
###FACE###
oval face, big eyes
###OUTPUT###
style guide, character sheet"""


class TestGetAdapter:
    """Tests for get_adapter()."""

    def test_returns_sd_adapter(self):
        adapter = get_adapter("sd")
        assert isinstance(adapter, StableDiffusionAdapter)

    def test_returns_mj_adapter(self):
        adapter = get_adapter("mj")
        assert isinstance(adapter, MidjourneyAdapter)

    def test_returns_nai_adapter(self):
        adapter = get_adapter("nai")
        assert isinstance(adapter, NovelAIAdapter)

    def test_accepts_full_names(self):
        assert isinstance(get_adapter("stable_diffusion"), StableDiffusionAdapter)
        assert isinstance(get_adapter("midjourney"), MidjourneyAdapter)
        assert isinstance(get_adapter("novelai"), NovelAIAdapter)

    def test_unknown_model_raises(self):
        with pytest.raises(ModelNotSupportedError):
            get_adapter("unknown_model")

    def test_case_insensitive(self):
        assert isinstance(get_adapter("SD"), StableDiffusionAdapter)
        assert isinstance(get_adapter("MJ"), MidjourneyAdapter)


class TestBaseAdapterParseBlocks:
    """Tests for BaseAdapter._parse_blocks()."""

    def test_parse_blocks_correctly(self):
        adapter = StableDiffusionAdapter()
        blocks = adapter._parse_blocks(SAMPLE_INTERMEDIATE)
        assert blocks["BASE"] == "anime character sheet, black and white ink"
        assert blocks["FACE"] == "oval face, big eyes"
        assert blocks["OUTPUT"] == "style guide, character sheet"

    def test_parse_blocks_empty_text(self):
        adapter = StableDiffusionAdapter()
        blocks = adapter._parse_blocks("")
        assert blocks == {}

    def test_parse_blocks_with_extra_whitespace(self):
        text = """###BASE###
  content with spaces

###NEXT###
  next content"""
        adapter = StableDiffusionAdapter()
        blocks = adapter._parse_blocks(text)
        assert blocks["BASE"] == "content with spaces"
        assert blocks["NEXT"] == "next content"

    def test_parse_blocks_missing_keys(self):
        """Blocks without keys get assigned to HEADER."""
        adapter = StableDiffusionAdapter()
        blocks = adapter._parse_blocks("just some text")
        assert blocks["HEADER"] == "just some text"


class TestBaseAdapterFlattenBlocks:
    """Tests for BaseAdapter._flatten_blocks()."""

    def test_flatten_with_default_sep(self):
        adapter = StableDiffusionAdapter()
        blocks = {"A": "x", "B": "y"}
        result = adapter._flatten_blocks(blocks)
        assert result == "x, y"

    def test_flatten_skips_empty(self):
        adapter = StableDiffusionAdapter()
        blocks = {"A": "x", "B": "", "C": "z"}
        result = adapter._flatten_blocks(blocks)
        assert result == "x, z"

    def test_flatten_with_custom_sep(self):
        adapter = StableDiffusionAdapter()
        blocks = {"A": "x", "B": "y"}
        result = adapter._flatten_blocks(blocks, sep=" | ")
        assert result == "x | y"


class TestBaseAdapterNormalizePunct:
    """Tests for BaseAdapter._normalize_punct()."""

    def test_zh_keeps_chinese_punct(self):
        adapter = StableDiffusionAdapter()
        result = adapter._normalize_punct("大眼睛，可愛", lang="zh")
        assert "，" in result

    def test_en_converts_chinese_punct(self):
        adapter = StableDiffusionAdapter()
        result = adapter._normalize_punct("大眼睛，可愛。", lang="en")
        assert "，" not in result
        assert ", " in result

    def test_en_converts_period(self):
        adapter = StableDiffusionAdapter()
        result = adapter._normalize_punct("測試。", lang="en")
        assert ". " in result or result.endswith(".")

    def test_en_converts_dunhao(self):
        adapter = StableDiffusionAdapter()
        result = adapter._normalize_punct("貓、狗", lang="en")
        assert "、" not in result
        assert ", " in result

    def test_en_converts_corner_brackets(self):
        adapter = StableDiffusionAdapter()
        result = adapter._normalize_punct("「test」", lang="en")
        assert '"' in result

    def test_zh_unchanged_for_en_punct(self):
        adapter = StableDiffusionAdapter()
        original = "Hello, world."
        result = adapter._normalize_punct(original, lang="zh")
        assert result == original


class TestStableDiffusionAdapter:
    """Tests for StableDiffusionAdapter."""

    def test_format_returns_string(self):
        adapter = StableDiffusionAdapter()
        result = adapter.format(SAMPLE_INTERMEDIATE)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_format_includes_base_content(self):
        adapter = StableDiffusionAdapter()
        result = adapter.format(SAMPLE_INTERMEDIATE)
        assert "anime character sheet" in result

    def test_format_with_ar(self):
        adapter = StableDiffusionAdapter()
        result = adapter.format(SAMPLE_INTERMEDIATE, ar="16:9")
        assert "--ar 16:9" in result

    def test_format_without_ar(self):
        adapter = StableDiffusionAdapter()
        result = adapter.format(SAMPLE_INTERMEDIATE, ar="")
        assert "--ar" not in result


class TestMidjourneyAdapter:
    """Tests for MidjourneyAdapter."""

    def test_format_includes_mj_params(self):
        adapter = MidjourneyAdapter()
        result = adapter.format(SAMPLE_INTERMEDIATE)
        assert "--style raw" in result
        assert "--v 6" in result

    def test_format_uses_default_ar(self):
        adapter = MidjourneyAdapter()
        result = adapter.format(SAMPLE_INTERMEDIATE)
        assert "--ar" in result

    def test_format_custom_ar(self):
        adapter = MidjourneyAdapter()
        result = adapter.format(SAMPLE_INTERMEDIATE, ar="16:9")
        assert "--ar 16:9" in result

    def test_format_flows_natural_language(self):
        adapter = MidjourneyAdapter()
        result = adapter.format(SAMPLE_INTERMEDIATE)
        # Should be sentence-like, not comma-separated tag soup
        assert ". " in result or "Presented as" in result


class TestNovelAIAdapter:
    """Tests for NovelAIAdapter."""

    def test_format_includes_quality_tags(self):
        adapter = NovelAIAdapter()
        result = adapter.format(SAMPLE_INTERMEDIATE)
        assert "best quality" in result
        assert "absurdres" in result

    def test_format_returns_string(self):
        adapter = NovelAIAdapter()
        result = adapter.format(SAMPLE_INTERMEDIATE)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_format_appends_quality_after_content(self):
        adapter = NovelAIAdapter()
        result = adapter.format(SAMPLE_INTERMEDIATE)
        # Quality tags should be after the main content
        assert result.endswith("absurdres")

    def test_format_with_ar_ignored(self):
        """NAI format does not append AR."""
        adapter = NovelAIAdapter()
        result = adapter.format(SAMPLE_INTERMEDIATE, ar="16:9")
        assert "--ar" not in result
