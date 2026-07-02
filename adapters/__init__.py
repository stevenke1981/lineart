from exceptions import ModelNotSupportedError

from .base import BaseAdapter
from .comfyui import ComfyUIAdapter
from .dalle import DalleAdapter
from .midjourney import MidjourneyAdapter
from .novelai import NovelAIAdapter
from .stable_diffusion import StableDiffusionAdapter

ADAPTERS = {
    "sd": StableDiffusionAdapter,
    "stable_diffusion": StableDiffusionAdapter,
    "mj": MidjourneyAdapter,
    "midjourney": MidjourneyAdapter,
    "nai": NovelAIAdapter,
    "novelai": NovelAIAdapter,
    "dalle": DalleAdapter,
    "dall-e": DalleAdapter,
    "dall_e": DalleAdapter,
    "comfyui": ComfyUIAdapter,
    "comfy": ComfyUIAdapter,
}


def get_adapter(model: str) -> BaseAdapter:
    model = model.lower().strip()
    if model not in ADAPTERS:
        raise ModelNotSupportedError(f"Unknown model '{model}'. Available: {list(ADAPTERS.keys())}")
    return ADAPTERS[model]()
