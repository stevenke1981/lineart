import json

from .base import BaseAdapter

_AR_DIMENSIONS: dict[str, tuple[int, int]] = {
    "3:4": (832, 1216),
    "1:1": (1024, 1024),
    "4:3": (1216, 832),
    "16:9": (1344, 768),
    "9:16": (768, 1344),
    "21:9": (1536, 640),
    "9:21": (640, 1536),
}


class ComfyUIAdapter(BaseAdapter):
    """ComfyUI format: JSON workflow snippet for CLIP Text Encode nodes."""

    name: str = "comfyui"

    NEGATIVE_PROMPT: str = "low quality, blurry, watermark, text, logo"

    def format(self, intermediate: str, lang: str = "zh", ar: str = "") -> str:
        blocks: dict[str, str] = self._parse_blocks(intermediate)
        positive = ", ".join(v for v in blocks.values() if v)
        positive = self._normalize_punct(positive, lang)
        width, height = _AR_DIMENSIONS.get(ar or "3:4", (832, 1216))

        payload = {
            "nodes": {
                "clip_positive": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {"text": positive},
                },
                "clip_negative": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {"text": self.NEGATIVE_PROMPT},
                },
                "empty_latent": {
                    "class_type": "EmptyLatentImage",
                    "inputs": {"width": width, "height": height, "batch_size": 1},
                },
            },
            "meta": {"format": "comfyui", "aspect_ratio": ar or "3:4"},
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)
