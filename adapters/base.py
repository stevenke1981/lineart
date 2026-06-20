from abc import ABC, abstractmethod


class BaseAdapter(ABC):
    """Abstract base for model-specific prompt formatters."""

    name: str = "base"

    @abstractmethod
    def format(self, intermediate: str, lang: str = "zh", ar: str = "") -> str:
        """Convert intermediate format (###KEY### blocks) to model-specific prompt."""
        ...

    def _parse_blocks(self, text: str) -> dict[str, str]:
        """Parse intermediate format into labeled blocks."""
        blocks: dict[str, str] = {}
        current_key: str = "HEADER"
        current_lines: list[str] = []

        for line in text.splitlines():
            line_stripped: str = line.strip()
            if line_stripped.startswith("###") and line_stripped.endswith("###"):
                if current_lines:
                    blocks[current_key] = "\n".join(current_lines).strip()
                current_key = line_stripped.strip("#").strip()
                current_lines = []
            else:
                if line_stripped:
                    current_lines.append(line_stripped)

        if current_lines:
            blocks[current_key] = "\n".join(current_lines).strip()

        return blocks

    def _flatten_blocks(self, blocks: dict[str, str], sep: str = ", ") -> str:
        """Join all block values into a single string."""
        parts: list[str] = [v for v in blocks.values() if v]
        return sep.join(parts)

    def _normalize_punct(self, text: str, lang: str = "zh") -> str:
        """Normalize punctuation for language."""
        if lang == "en":
            text = text.replace("，", ", ")
            text = text.replace("。", ". ")
            text = text.replace("、", ", ")
            text = text.replace("「", '"')
            text = text.replace("」", '"')
        return text
