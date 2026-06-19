from .base import BaseAdapter


class NovelAIAdapter(BaseAdapter):
    """NovelAI format: curly-brace weighted tags, quality tags appended."""

    name = "novelai"

    QUALITY_TAGS = "best quality, amazing quality, very aesthetic, absurdres"

    def format(self, intermediate: str, lang: str = "zh") -> str:
        blocks = self._parse_blocks(intermediate)
        parts = []

        for key, value in blocks.items():
            if key in ("BASE", "FACE", "OUTPUT"):
                parts.append(f"{{{value}}}")
            else:
                parts.append(value)

        # NAI uses English tags for quality
        result = ", ".join(parts)
        result = self._normalize_punct(result, lang)
        return f"{result}, {self.QUALITY_TAGS}"
