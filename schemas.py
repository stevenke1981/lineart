"""Pydantic schemas for character data validation."""

from pydantic import BaseModel


class BilingualField(BaseModel):
    """A field with zh/en translations."""

    zh: str
    en: str


class CharacterOutput(BaseModel):
    """Definition of an output type for a character."""

    label: BilingualField
    style: BilingualField
    variants: list[dict] | None = None


class Character(BaseModel):
    """Full character definition schema."""

    id: str
    label: BilingualField
    gender: BilingualField | None = None
    base_style: BilingualField
    components: dict
    outputs: dict[str, CharacterOutput]
