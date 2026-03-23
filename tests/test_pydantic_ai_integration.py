"""Integration tests for PydanticAI-backed ACE roles with real API calls.

Requires AWS credentials for Bedrock access.
Run with: uv run pytest tests/test_pydantic_ai_integration.py -v -s --no-cov
"""

from __future__ import annotations

import os

import pytest
from dotenv import load_dotenv

load_dotenv()

# Skip entire module if no AWS credentials
pytestmark = pytest.mark.requires_api

try:
    import boto3
    sts = boto3.client("sts")
    sts.get_caller_identity()
    HAS_AWS = True
except Exception:
    HAS_AWS = False

if not HAS_AWS:
    pytest.skip("AWS credentials not available", allow_module_level=True)

from ace_next.core.outputs import (
    AgentOutput,
    ExtractedLearning,
    ReflectorOutput,
    SkillManagerOutput,
    SkillTag,
)
from ace_next.core.skillbook import Skillbook, UpdateBatch
from ace_next.implementations import Agent, Reflector, SkillManager
from ace_next.runners.litellm import ACELiteLLM
from ace_next.core.environments import Sample, SimpleEnvironment


MODEL = "bedrock/eu.anthropic.claude-haiku-4-5-20251001-v1:0"


class TestAgentRole:
    """Test Agent role produces valid structured output."""

    def test_basic_question(self):
        agent = Agent(MODEL)
        sb = Skillbook()
        output = agent.generate(
            question="What is the capital of France?",
            context="Answer in one word.",
            skillbook=sb,
        )

        assert isinstance(output, AgentOutput)
        assert len(output.reasoning) > 0, "reasoning should be non-empty"
        assert len(output.final_answer) > 0, "final_answer should be non-empty"
        assert "paris" in output.final_answer.lower(), (
            f"Expected 'Paris' in answer, got: {output.final_answer}"
        )
        assert isinstance(output.skill_ids, list)
        assert "usage" in output.raw, f"raw should contain usage, got: {output.raw}"
        assert output.raw["usage"]["prompt_tokens"] > 0
        assert output.raw["usage"]["completion_tokens"] > 0
        print(f"\n  Agent answer: {output.final_answer}")
        print(f"  Usage: {output.raw['usage']}")

    def test_with_skillbook(self):
        agent = Agent(MODEL)
        sb = Skillbook()
        sb.add_skill(
            "math",
            "Use decomposition: break large multiplications into (a*10 + b) parts",
            skill_id="math-001",
        )

        output = agent.generate(
            question="What is 17 × 23?",
            context="Show your work step by step.",
            skillbook=sb,
        )

        assert isinstance(output, AgentOutput)
        assert len(output.final_answer) > 0
        assert "391" in output.final_answer, (
            f"Expected '391' in answer, got: {output.final_answer}"
        )
        print(f"\n  Agent answer: {output.final_answer}")
        print(f"  Reasoning excerpt: {output.reasoning[:300]}...")
        print(f"  Cited skills: {output.skill_ids}")

    def test_with_reflection(self):
        agent = Agent(MODEL)
        sb = Skillbook()
        sb.add_skill("science", "State precise numerical values with units", skill_id="sci-001")

        output = agent.generate(
            question="What is the boiling point of water in Fahrenheit?",
            context="Give only the numerical answer with units.",
            skillbook=sb,
            reflection="Previous answer was wrong. Water boils at 212°F at sea level.",
        )

        assert isinstance(output, AgentOutput)
        assert len(output.final_answer) > 0
        # The reflection explicitly states 212°F — verify the model uses it
        assert "212" in output.final_answer or "212" in output.reasoning, (
            f"Expected '212' somewhere in output, got answer: {output.final_answer}"
        )
        print(f"\n  Agent answer with reflection: {output.final_answer}")


class TestReflectorRole:
    """Test Reflector role produces valid structured analysis."""

    def test_correct_answer_reflection(self):
        reflector = Reflector(MODEL)
        sb = Skillbook()
        sb.add_skill("math", "Break down multiplication", skill_id="math-001")

        agent_output = AgentOutput(
            reasoning="Following [math-001], I decomposed 15×24 as 15×20 + 15×4 = 300 + 60 = 360",
            final_answer="360",
            skill_ids=["math-001"],
        )

        output = reflector.reflect(
            question="What is 15 × 24?",
            agent_output=agent_output,
            skillbook=sb,
            ground_truth="360",
            feedback="Correct!",
        )

        assert isinstance(output, ReflectorOutput)
        assert len(output.reasoning) > 0
        assert len(output.correct_approach) > 0
        assert len(output.key_insight) > 0
        assert "usage" in output.raw
        print(f"\n  Key insight: {output.key_insight}")
        print(f"  Skill tags: {[(t.id, t.tag) for t in output.skill_tags]}")

    def test_wrong_answer_reflection(self):
        reflector = Reflector(MODEL)
        sb = Skillbook()

        agent_output = AgentOutput(
            reasoning="I calculated 15×24 = 15×20 + 15×4 = 310 + 60 = 370",
            final_answer="370",
        )

        output = reflector.reflect(
            question="What is 15 × 24?",
            agent_output=agent_output,
            skillbook=sb,
            ground_truth="360",
            feedback="Incorrect. The answer is 360.",
        )

        assert isinstance(output, ReflectorOutput)
        assert len(output.error_identification) > 0, "Should identify the error"
        assert len(output.root_cause_analysis) > 0, "Should analyze root cause"
        print(f"\n  Error identified: {output.error_identification[:200]}")
        print(f"  Root cause: {output.root_cause_analysis[:200]}")
        print(f"  Learnings: {len(output.extracted_learnings)}")

    def test_extracted_learnings_structure(self):
        reflector = Reflector(MODEL)
        sb = Skillbook()

        agent_output = AgentOutput(
            reasoning="I tried to answer directly without checking",
            final_answer="I don't know",
        )

        output = reflector.reflect(
            question="What is the population of Tokyo metropolitan area?",
            agent_output=agent_output,
            skillbook=sb,
            ground_truth="approximately 37 million",
            feedback="Incorrect. Should have provided the answer.",
        )

        assert isinstance(output, ReflectorOutput)
        for learning in output.extracted_learnings:
            assert isinstance(learning, ExtractedLearning)
            assert len(learning.learning) > 0
            assert 0.0 <= learning.atomicity_score <= 1.0
        print(f"\n  Extracted {len(output.extracted_learnings)} learnings")
        for i, l in enumerate(output.extracted_learnings):
            print(f"    [{i}] {l.learning} (atomicity: {l.atomicity_score})")


class TestSkillManagerRole:
    """Test SkillManager role produces valid skillbook updates."""

    def test_add_new_skill(self):
        sm = SkillManager(MODEL)
        sb = Skillbook()

        reflection = ReflectorOutput(
            reasoning="The agent failed because it didn't decompose the problem",
            error_identification="Tried to multiply directly without decomposition",
            root_cause_analysis="Missing strategy for breaking down multiplication",
            correct_approach="Use decomposition: 15×24 = 15×(20+4) = 300+60 = 360",
            key_insight="Break large multiplications into manageable parts",
            extracted_learnings=[
                ExtractedLearning(
                    learning="Decompose multi-digit multiplication using distributive property",
                    atomicity_score=0.95,
                    evidence="15×24 = 15×20 + 15×4 = 360",
                ),
            ],
        )

        output = sm.update_skills(
            reflections=(reflection,),
            skillbook=sb,
            question_context="Mental arithmetic",
            progress="0/1 correct",
        )

        assert isinstance(output, SkillManagerOutput)
        assert isinstance(output.update, UpdateBatch)
        assert len(output.update.reasoning) > 0
        assert "usage" in output.raw
        print(f"\n  Reasoning: {output.update.reasoning[:200]}")
        print(f"  Operations: {len(output.update.operations)}")
        for op in output.update.operations:
            print(f"    {op.type}: {op.content[:80] if op.content else 'N/A'}")

    def test_tag_existing_skill(self):
        sm = SkillManager(MODEL)
        sb = Skillbook()
        sb.add_skill(
            "math",
            "Use decomposition for multiplication",
            skill_id="math-001",
        )

        reflection = ReflectorOutput(
            reasoning="The agent correctly applied decomposition strategy",
            correct_approach="Decomposition worked well",
            key_insight="Decomposition strategy is effective",
            skill_tags=[SkillTag(id="math-001", tag="helpful")],
        )

        output = sm.update_skills(
            reflections=(reflection,),
            skillbook=sb,
            question_context="Mental arithmetic",
            progress="1/1 correct",
        )

        assert isinstance(output, SkillManagerOutput)
        print(f"\n  Operations: {len(output.update.operations)}")
        for op in output.update.operations:
            print(
                f"    {op.type} {op.skill_id or ''}: "
                f"{op.content or op.metadata}"
            )


class TestACELiteLLMIntegration:
    """Test the full ACELiteLLM flow with real API calls."""

    def test_ask(self):
        ace = ACELiteLLM.from_model(MODEL)
        answer = ace.ask("What is 2 + 2?")
        assert "4" in answer, f"Expected '4' in answer, got: {answer}"
        print(f"\n  ask() answer: {answer}")

    def test_ask_and_learn_from_feedback(self):
        ace = ACELiteLLM.from_model(MODEL)

        answer = ace.ask("What is the chemical symbol for gold?")
        print(f"\n  Answer: {answer}")
        assert len(answer) > 0

        result = ace.learn_from_feedback(
            feedback="Correct! Gold's symbol Au comes from the Latin 'aurum'.",
            ground_truth="Au",
        )
        assert result is True, "learn_from_feedback should return True"
        print(f"  Skills after learning: {len(ace.skillbook.skills())}")
        for skill in ace.skillbook.skills():
            print(f"    [{skill.id}] {skill.content[:80]}")

    def test_full_learning_pipeline(self):
        """End-to-end: learn from samples, verify skillbook grows."""
        ace = ACELiteLLM.from_model(MODEL)
        env = SimpleEnvironment()

        samples = [
            Sample(
                question="What is the speed of light in km/s?",
                ground_truth="approximately 300,000 km/s",
            ),
        ]

        results = ace.learn(samples, environment=env)
        assert len(results) == 1
        assert results[0].error is None, f"Pipeline error: {results[0].error}"
        print(f"\n  Pipeline completed. Skills: {len(ace.skillbook.skills())}")
        for skill in ace.skillbook.skills():
            print(f"    [{skill.id}] {skill.content[:80]}")

    def test_save_and_load_after_learning(self, tmp_path):
        """Skills survive save/load cycle."""
        ace = ACELiteLLM.from_model(MODEL)
        answer = ace.ask("What is H2O?")
        ace.learn_from_feedback("Correct!", ground_truth="Water")

        path = str(tmp_path / "skillbook.json")
        skills_before = len(ace.skillbook.skills())
        ace.save(path)

        ace2 = ACELiteLLM.from_model(MODEL, skillbook_path=path)
        assert len(ace2.skillbook.skills()) == skills_before
        print(f"\n  Saved and loaded {skills_before} skills successfully")


class TestRetryAndConsistency:
    """Test structured output consistency across multiple calls."""

    def test_structured_output_consistency(self):
        """Multiple calls should always produce valid structured output."""
        agent = Agent(MODEL)
        sb = Skillbook()

        questions = [
            ("What is 7 × 8?", "56"),
            ("What is the capital of Japan?", "Tokyo"),
            ("Who wrote Romeo and Juliet?", "Shakespeare"),
        ]

        for q, expected in questions:
            output = agent.generate(
                question=q,
                context="Answer concisely.",
                skillbook=sb,
            )
            assert isinstance(output, AgentOutput), f"Wrong type for '{q}'"
            assert len(output.reasoning) > 0, f"Empty reasoning for '{q}'"
            assert len(output.final_answer) > 0, f"Empty answer for '{q}'"
            assert isinstance(output.raw, dict), f"raw not dict for '{q}'"
            assert "usage" in output.raw, f"No usage in raw for '{q}'"
            assert expected.lower() in output.final_answer.lower(), (
                f"Expected '{expected}' in answer for '{q}', got: {output.final_answer}"
            )
            print(f"\n  Q: {q} -> A: {output.final_answer}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--no-cov"])
