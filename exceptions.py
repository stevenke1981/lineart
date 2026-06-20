"""Custom exception hierarchy for Lineart."""


class LineartError(Exception):
    """Base exception for all Lineart errors."""


class CharacterNotFoundError(LineartError, FileNotFoundError):
    """Raised when a character YAML file is not found."""


class TemplateNotFoundError(LineartError, ValueError):
    """Raised when a template file is not found."""


class ModelNotSupportedError(LineartError, ValueError):
    """Raised when an unsupported model is requested."""


class LanguageNotFoundError(LineartError, FileNotFoundError):
    """Raised when an i18n language file is not found."""
