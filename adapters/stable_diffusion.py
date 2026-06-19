from .base import BaseAdapter


class StableDiffusionAdapter(BaseAdapter):
    """Stable Diffusion format: comma-separated tags with weighting."""

    name = "stable_diffusion"

    # Blocks that get higher weight emphasis
    WEIGHT_BOOST = {"BASE", "FACE", "EXPRESSION", "OUTPUT"}
    BOOST_WEIGHT = 1.3

    def format(self, intermediate: str, lang: str = "zh") -> str:
        blocks = self._parse_blocks(intermediate)
        parts = []

        for key, value in blocks.items():
            if key in self.WEIGHT_BOOST:
                parts.append(f"({value}:{self.BOOST_WEIGHT})")
            else:
                parts.append(value)

        result = ", ".join(parts)
        return self._normalize_punct(result, lang)
