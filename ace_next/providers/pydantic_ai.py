"""PydanticAI model resolution helpers.

Converts ACE model identifiers (which follow LiteLLM conventions) into
PydanticAI model strings.

Resolution strategy (see ``resolve_model`` for details):

1. Already has a PydanticAI provider prefix (``openai:gpt-4o``) → pass through.
2. Starts with a LiteLLM prefix that has a PydanticAI native equivalent
   (``bedrock/model``) → rewrite to ``bedrock:model``.
3. Everything else → prepend ``litellm:`` for the LiteLLM proxy provider.

Why not always use ``litellm:``?  PydanticAI's LiteLLM provider is an
OpenAI-compatible HTTP client.  Providers that aren't OpenAI-compatible
(Bedrock via SigV4, Anthropic's native API, etc.) need PydanticAI's
native provider instead.
"""

from __future__ import annotations

from pydantic_ai.settings import ModelSettings

from .config import ModelConfig

# PydanticAI provider names accepted as ``<provider>:<model>`` prefixes.
_PYDANTIC_AI_PROVIDERS: frozenset[str] = frozenset(
    {
        "anthropic",
        "azure",
        "bedrock",
        "cerebras",
        "cohere",
        "deepseek",
        "google",
        "google-gla",
        "google-vertex",
        "grok",
        "groq",
        "litellm",
        "mistral",
        "openai",
        "openai-chat",
        "openai-responses",
        "openrouter",
        "vercel",
        "vertexai",
    }
)

# LiteLLM uses ``provider/model`` while PydanticAI uses ``provider:model``.
# When the first path segment of a LiteLLM string matches a PydanticAI
# native provider, we rewrite ``/`` → ``:`` so PydanticAI uses its own
# provider (with proper auth, API format, etc.) instead of the generic
# OpenAI-compatible LiteLLM proxy.
_LITELLM_PREFIX_TO_NATIVE: frozenset[str] = frozenset(
    {
        "anthropic",
        "azure",
        "azure_ai",
        "bedrock",
        "cohere",
        "deepseek",
        "groq",
        "mistral",
        "openrouter",
        "vertex_ai",
    }
)


def resolve_model(model: str) -> str:
    """Resolve an ACE/LiteLLM model string for PydanticAI.

    Three resolution paths:

    1. **PydanticAI-native prefix** — If the string already starts with
       a known PydanticAI provider prefix (e.g. ``openai:gpt-4o``,
       ``bedrock:model-id``), it is returned unchanged.

    2. **LiteLLM prefix with native equivalent** — If the first path
       segment matches a PydanticAI native provider (e.g.
       ``bedrock/model-id:0``), the ``/`` is rewritten to ``:`` so
       PydanticAI uses its own provider with proper auth and API
       format.

    3. **Fallback** — Everything else is prefixed with ``litellm:``
       for the LiteLLM proxy provider.

    Examples::

        resolve_model("gpt-4o-mini")
        # → "litellm:gpt-4o-mini"

        resolve_model("bedrock/anthropic.claude-haiku-4-5-20251001-v1:0")
        # → "bedrock:anthropic.claude-haiku-4-5-20251001-v1:0"

        resolve_model("openrouter/anthropic/claude-3.5-sonnet")
        # → "openrouter:anthropic/claude-3.5-sonnet"

        resolve_model("openai:gpt-4o")
        # → "openai:gpt-4o"  (unchanged)

    Args:
        model: Model identifier — LiteLLM convention
            (``"gpt-4o-mini"``, ``"bedrock/model-id:0"``) or
            PydanticAI convention (``"openai:gpt-4o"``).

    Returns:
        PydanticAI model string.
    """
    # Path 1: already has a PydanticAI provider prefix
    if ":" in model:
        prefix = model.split(":", 1)[0]
        if prefix in _PYDANTIC_AI_PROVIDERS:
            return model

    # Path 2: LiteLLM prefix with a native PydanticAI equivalent
    if "/" in model:
        litellm_prefix = model.split("/", 1)[0]
        if litellm_prefix in _LITELLM_PREFIX_TO_NATIVE:
            rest = model.split("/", 1)[1]
            pydantic_prefix = litellm_prefix
            # Normalize LiteLLM aliases to PydanticAI names
            if litellm_prefix == "vertex_ai":
                pydantic_prefix = "google-vertex"
            elif litellm_prefix == "azure_ai":
                pydantic_prefix = "azure"
            return f"{pydantic_prefix}:{rest}"

    # Path 3: no recognized prefix → route through LiteLLM provider
    return f"litellm:{model}"


def settings_from_config(config: ModelConfig) -> ModelSettings:
    """Create ``ModelSettings`` from a ``ModelConfig``.

    Maps ACE configuration (temperature, max_tokens) to PydanticAI's
    model settings.

    Args:
        config: ACE model configuration.

    Returns:
        PydanticAI ``ModelSettings`` with temperature and max_tokens.
    """
    return ModelSettings(
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )
