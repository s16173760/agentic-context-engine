"""ACE LLM providers — client wrappers for LLM APIs.

- ``LiteLLMClient`` / ``LiteLLMConfig`` — LiteLLM integration (100+ providers)
- ``InstructorClient`` / ``wrap_with_instructor`` — Instructor structured outputs
- ``LangChainLiteLLMClient`` — LangChain + LiteLLM (optional)
- ``ClaudeCodeLLMClient`` / ``ClaudeCodeLLMConfig`` — Claude Code CLI (optional)

Heavy dependencies (litellm, instructor, openai) are lazily imported so that
lightweight consumers (e.g. the CLI) don't pay the startup cost.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

# Config is lightweight — always available eagerly.
from .config import ACEModelConfig, ModelConfig, load_config, save_config

if TYPE_CHECKING:
    from .instructor import InstructorClient, wrap_with_instructor
    from .litellm import LiteLLMClient, LiteLLMConfig, LLMResponse
    from .pydantic_ai import resolve_model, settings_from_config
    from .registry import ValidationResult, search_models, validate_connection

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    # LiteLLM
    "LiteLLMClient": ("ace.providers.litellm", "LiteLLMClient"),
    "LiteLLMConfig": ("ace.providers.litellm", "LiteLLMConfig"),
    "LLMResponse": ("ace.providers.litellm", "LLMResponse"),
    # Instructor
    "InstructorClient": ("ace.providers.instructor", "InstructorClient"),
    "wrap_with_instructor": ("ace.providers.instructor", "wrap_with_instructor"),
    # PydanticAI helpers
    "resolve_model": ("ace.providers.pydantic_ai", "resolve_model"),
    "settings_from_config": ("ace.providers.pydantic_ai", "settings_from_config"),
    # Registry
    "ValidationResult": ("ace.providers.registry", "ValidationResult"),
    "validate_connection": ("ace.providers.registry", "validate_connection"),
    "search_models": ("ace.providers.registry", "search_models"),
    # Optional: LangChain
    "LangChainLiteLLMClient": ("ace.providers.langchain", "LangChainLiteLLMClient"),
    # Optional: Claude Code
    "ClaudeCodeLLMClient": ("ace.providers.claude_code", "ClaudeCodeLLMClient"),
    "ClaudeCodeLLMConfig": ("ace.providers.claude_code", "ClaudeCodeLLMConfig"),
    "CLAUDE_CODE_CLI_AVAILABLE": ("ace.providers.claude_code", "CLAUDE_CODE_CLI_AVAILABLE"),
}


def __getattr__(name: str) -> object:
    if name in _LAZY_IMPORTS:
        module_path, attr = _LAZY_IMPORTS[name]
        import importlib

        try:
            module = importlib.import_module(module_path)
        except ImportError:
            # Optional providers (langchain, claude_code) may not be installed.
            return None
        value = getattr(module, attr)
        globals()[name] = value
        return value
    raise AttributeError(f"module 'ace.providers' has no attribute {name!r}")


__all__ = [
    # Config
    "ModelConfig",
    "ACEModelConfig",
    "load_config",
    "save_config",
    # PydanticAI helpers
    "resolve_model",
    "settings_from_config",
    # Registry
    "ValidationResult",
    "validate_connection",
    "search_models",
    # LiteLLM
    "LiteLLMClient",
    "LiteLLMConfig",
    "LLMResponse",
    # Instructor
    "InstructorClient",
    "wrap_with_instructor",
    # LangChain (optional)
    "LangChainLiteLLMClient",
    # Claude Code CLI (optional)
    "ClaudeCodeLLMClient",
    "ClaudeCodeLLMConfig",
    "CLAUDE_CODE_CLI_AVAILABLE",
]
