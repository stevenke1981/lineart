from .base import BaseAdapter
from .stable_diffusion import StableDiffusionAdapter
from .midjourney import MidjourneyAdapter
from .novelai import NovelAIAdapter

ADAPTERS = {
    "sd": StableDiffusionAdapter,
    "stable_diffusion": StableDiffusionAdapter,
    "mj": MidjourneyAdapter,
    "midjourney": MidjourneyAdapter,
    "nai": NovelAIAdapter,
    "novelai": NovelAIAdapter,
}

def get_adapter(model: str) -> BaseAdapter:
    model = model.lower().strip()
    if model not in ADAPTERS:
        raise ValueError(f"Unknown model '{model}'. Available: {list(ADAPTERS.keys())}")
    return ADAPTERS[model]()
