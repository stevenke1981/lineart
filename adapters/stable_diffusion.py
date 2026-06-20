from .base import BaseAdapter


class StableDiffusionAdapter(BaseAdapter):
    """Stable Diffusion format: comma-separated tags with weighting."""

    name: str = "stable_diffusion"

    # Blocks that get higher weight emphasis
    WEIGHT_BOOST: set[str] = {"BASE", "FACE", "EXPRESSION", "OUTPUT"}
    BOOST_WEIGHT: float = 1.3

    def format(self, intermediate: str, lang: str = "zh", ar: str = "") -> str:
        blocks: dict[str, str] = self._parse_blocks(intermediate)
        parts: list[str] = []

        for key, value in blocks.items():
            if key in self.WEIGHT_BOOST:
                parts.append(f"({value}:{self.BOOST_WEIGHT})")
            else:
                parts.append(value)

        result: str = ", ".join(parts)
        result = self._normalize_punct(result, lang)
        if ar:
            result += f" --ar {ar}"
        return result
