from .base import BaseAdapter


class MidjourneyAdapter(BaseAdapter):
    """MidJourney format: natural language with --parameters."""

    name = "midjourney"

    PARAMETERS = "--style raw --s 250 --v 6"

    def format(self, intermediate: str, lang: str = "zh", ar: str = "") -> str:
        blocks = self._parse_blocks(intermediate)

        # MJ favours flowing natural language over tag-lists
        sentences = []
        for key, value in blocks.items():
            if key == "OUTPUT":
                label = self._normalize_punct(value, lang)
                sentences.append(f"Presented as {label}")
            elif key == "EXPRESSIONS":
                sentences.append(f"Expression sheet showing: {value}")
            elif key == "BREAKDOWN_LAYERS":
                sentences.append(f"Layered breakdown: {value}")
            else:
                sentences.append(value)

        prompt = ". ".join(sentences)
        prompt = self._normalize_punct(prompt, lang)
        ar_param = f" --ar {ar}" if ar else " --ar 3:4"
        return f"{prompt} {self.PARAMETERS}{ar_param}"
