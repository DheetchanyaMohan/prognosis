from app.llm.prompts import (
    EXPERIMENT_PLANNING_SYSTEM_PROMPT,
    HYPOTHESIS_GENERATION_SYSTEM_PROMPT,
    build_user_prompt,
)


def test_build_user_prompt_includes_query() -> None:
    prompt = build_user_prompt("why is my model overfitting?", [])
    assert "User question: why is my model overfitting?" == prompt


def test_build_user_prompt_includes_nonempty_sections() -> None:
    prompt = build_user_prompt("q", [("Diagnostics", "gap=0.5"), ("Knowledge", "overfitting docs")])
    assert "Diagnostics:\ngap=0.5" in prompt
    assert "Knowledge:\noverfitting docs" in prompt


def test_build_user_prompt_omits_empty_sections() -> None:
    prompt = build_user_prompt("q", [("Diagnostics", ""), ("Knowledge", "docs")])
    assert "Diagnostics" not in prompt
    assert "Knowledge:\ndocs" in prompt


def test_build_user_prompt_preserves_section_order() -> None:
    prompt = build_user_prompt("q", [("First", "a"), ("Second", "b")])
    assert prompt.index("First") < prompt.index("Second")


def test_system_prompts_request_json_array() -> None:
    assert "JSON array" in HYPOTHESIS_GENERATION_SYSTEM_PROMPT
    assert "JSON array" in EXPERIMENT_PLANNING_SYSTEM_PROMPT


def test_system_prompts_are_nonempty_strings() -> None:
    assert isinstance(HYPOTHESIS_GENERATION_SYSTEM_PROMPT, str)
    assert len(HYPOTHESIS_GENERATION_SYSTEM_PROMPT) > 50
    assert isinstance(EXPERIMENT_PLANNING_SYSTEM_PROMPT, str)
    assert len(EXPERIMENT_PLANNING_SYSTEM_PROMPT) > 50