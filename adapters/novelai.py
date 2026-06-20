from .base import BaseAdapter


class NovelAIAdapter(BaseAdapter):
    """NovelAI format: curly-brace weighted tags, quality tags appended."""

    name: str = "novelai"

    QUALITY_TAGS: str = "best quality, amazing quality, very aesthetic, absurdres"

    def format(self, intermediate: str, lang: str = "zh", ar: str = "") -> str:
        blocks: dict[str, str] = self._parse_blocks(intermediate)
        parts: list[str] = []

        for key, value in blocks.items():
            if key in ("BASE", "FACE", "OUTPUT"):
                parts.append(f"{{{value}}}")
            else:
                parts.append(value)

        # NAI uses English tags for quality
        result: str = ", ".join(parts)
        result = self._normalize_punct(result, lang)
        return f"{result}, {self.QUALITY_TAGS}"
