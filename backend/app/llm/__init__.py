"""LLM service layer.

Encapsulates all interaction with language models — the only part of the
codebase that imports a provider SDK directly, builds a prompt string,
or parses raw LLM output. LangGraph nodes depend on ChatModel /
get_chat_model, the prompt constants/builder in app.llm.prompts, and
generate_structured_list / generate_structured_object — never on a
provider SDK or ad hoc JSON parsing.
"""

from app.llm.client import AnthropicChatModel, ChatModel, LLMProviderError, get_chat_model
from app.llm.models import EffortLevel, Hypothesis, Recommendation
from app.llm.prompts import (
    EXPERIMENT_PLANNING_SYSTEM_PROMPT,
    HYPOTHESIS_GENERATION_SYSTEM_PROMPT,
    build_user_prompt,
)
from app.llm.structured_output import (
    StructuredOutputError,
    generate_structured_list,
    generate_structured_object,
)

__all__ = [
    "ChatModel",
    "AnthropicChatModel",
    "get_chat_model",
    "LLMProviderError",
    "Hypothesis",
    "Recommendation",
    "EffortLevel",
    "build_user_prompt",
    "HYPOTHESIS_GENERATION_SYSTEM_PROMPT",
    "EXPERIMENT_PLANNING_SYSTEM_PROMPT",
    "generate_structured_list",
    "generate_structured_object",
    "StructuredOutputError",
]