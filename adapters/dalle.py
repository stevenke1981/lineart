from .base import BaseAdapter


class DalleAdapter(BaseAdapter):
    """DALL·E 3 format: natural-language paragraph description."""

    name: str = "dalle"

    def format(self, intermediate: str, lang: str = "zh", ar: str = "") -> str:
        blocks: dict[str, str] = self._parse_blocks(intermediate)
        sentences: list[str] = []

        for key, value in blocks.items():
            text = self._normalize_punct(value, lang)
            if key == "OUTPUT":
                sentences.append(f"The final image should be {text}.")
            elif key == "EXPRESSIONS":
                sentences.append(f"Show an expression sheet with: {text}.")
            elif key == "BREAKDOWN_LAYERS":
                sentences.append(f"Include a layered breakdown showing: {text}.")
            else:
                sentences.append(text)

        prompt = " ".join(sentences)
        if ar:
            prompt += f" Aspect ratio: {ar}."
        return prompt
