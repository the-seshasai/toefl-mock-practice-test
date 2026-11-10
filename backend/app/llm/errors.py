class LLMError(Exception):
    """Base class for provider failures."""


class LLMConfigError(LLMError):
    """Missing key or unknown provider."""


class LLMRateLimitError(LLMError):
    """Provider kept returning 429 after all retries."""


class LLMParseError(LLMError):
    """Output was not valid JSON / did not match the schema after all attempts."""
