#!/usr/bin/env python3
"""
Quick start example using LiteLLM with ACELiteLLM integration.

This shows how to use ACELiteLLM with various providers for
self-improving AI agents. The agent learns from examples and
improves its responses over time.

Requires:
- API key for at least one provider (OpenAI, Anthropic, Google, etc.)
- litellm package installed

Features demonstrated:
- Creating ACELiteLLM agent with different providers
- Learning from training samples
- Testing before/after learning
- Saving learned strategies for reuse
- Playbook persistence across runs
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from ace.integrations import ACELiteLLM
from ace import Sample, SimpleEnvironment

# Load environment variables from .env file
load_dotenv()


def check_api_keys():
    """Check which API keys are available."""
    providers = {
        "OpenAI (GPT)": os.getenv("OPENAI_API_KEY"),
        "Anthropic (Claude)": os.getenv("ANTHROPIC_API_KEY"),
        "Google (Gemini)": os.getenv("GOOGLE_API_KEY"),
        "Cohere": os.getenv("COHERE_API_KEY"),
    }

    available = {name: bool(key) for name, key in providers.items()}
    return available


def get_recommended_model(available_providers):
    """Get a recommended model based on available API keys."""
    if available_providers.get("OpenAI (GPT)"):
        return "gpt-4o-mini", "OpenAI GPT-4o Mini (fast, cost-effective)"
    elif available_providers.get("Anthropic (Claude)"):
        return "claude-3-haiku-20240307", "Anthropic Claude 3 Haiku (fast)"
    elif available_providers.get("Google (Gemini)"):
        return "gemini/gemini-1.5-flash", "Google Gemini 1.5 Flash"
    elif available_providers.get("Cohere"):
        return "command-r", "Cohere Command R"
    else:
        return None, None


def example_openai():
    """Example using OpenAI GPT models."""
    print("\n=== OpenAI GPT Example ===")

    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Please set OPENAI_API_KEY in your .env file")
        return None

    playbook_path = Path(__file__).parent / "openai_learned_strategies.json"

    print("🤖 Creating ACELiteLLM agent with OpenAI...")
    agent = ACELiteLLM(
        model="gpt-4o-mini",
        max_tokens=1024,
        temperature=0.2,
        is_learning=True,
        playbook_path=str(playbook_path) if playbook_path.exists() else None
    )

    if playbook_path.exists():
        print(f"📚 Loaded {len(agent.playbook.bullets())} existing strategies")
    else:
        print("🆕 Starting with empty playbook")

    return agent, playbook_path


def example_anthropic():
    """Example using Anthropic Claude models."""
    print("\n=== Anthropic Claude Example ===")

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Please set ANTHROPIC_API_KEY in your .env file")
        return None

    playbook_path = Path(__file__).parent / "claude_learned_strategies.json"

    print("🤖 Creating ACELiteLLM agent with Claude...")
    agent = ACELiteLLM(
        model="claude-3-haiku-20240307",
        max_tokens=1024,
        temperature=0.2,
        is_learning=True,
        playbook_path=str(playbook_path) if playbook_path.exists() else None
    )

    if playbook_path.exists():
        print(f"📚 Loaded {len(agent.playbook.bullets())} existing strategies")
    else:
        print("🆕 Starting with empty playbook")

    return agent, playbook_path


def example_google():
    """Example using Google Gemini models."""
    print("\n=== Google Gemini Example ===")

    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Please set GOOGLE_API_KEY in your .env file")
        return None

    playbook_path = Path(__file__).parent / "gemini_learned_strategies.json"

    print("🤖 Creating ACELiteLLM agent with Gemini...")
    agent = ACELiteLLM(
        model="gemini/gemini-1.5-flash",
        max_tokens=1024,
        temperature=0.2,
        is_learning=True,
        playbook_path=str(playbook_path) if playbook_path.exists() else None
    )

    if playbook_path.exists():
        print(f"📚 Loaded {len(agent.playbook.bullets())} existing strategies")
    else:
        print("🆕 Starting with empty playbook")

    return agent, playbook_path


def run_learning_demo(agent, playbook_path, provider_name):
    """Run the learning demonstration with any agent."""
    print(f"\n🧪 Testing {provider_name} agent before learning:")

    # Test before learning
    test_questions = [
        "What is 2+2?",
        "What color is the sky?",
        "What is the capital of France?"
    ]

    print("📋 Pre-learning responses:")
    for question in test_questions[:1]:  # Just test one before learning
        answer = agent.ask(question)
        print(f"Q: {question}")
        print(f"A: {answer}")

    # Create training samples
    samples = [
        Sample(question="What is 2+2?", ground_truth="4"),
        Sample(question="What color is the sky?", ground_truth="blue"),
        Sample(question="What is the capital of France?", ground_truth="Paris"),
        Sample(question="What is the largest planet?", ground_truth="Jupiter"),
        Sample(question="Who wrote Romeo and Juliet?", ground_truth="Shakespeare"),
    ]

    print(f"\n🚀 Running ACE learning with {provider_name}...")
    environment = SimpleEnvironment()

    try:
        results = agent.learn(samples, environment, epochs=1)
        successful_samples = len([r for r in results if r.success])
        print(f"✅ Successfully processed {successful_samples}/{len(results)} samples")
    except Exception as e:
        print(f"❌ Learning failed: {e}")
        results = []

    # Show results
    print(f"\n📊 Training results:")
    print(f"  • Processed: {len(results)} samples")
    print(f"  • Playbook size: {len(agent.playbook.bullets())} strategies")

    # Test after learning
    print(f"\n🧠 Testing {provider_name} agent after learning:")
    for question in ["What is 3+3?", "What color is grass?", "Capital of Italy?"]:
        answer = agent.ask(question)
        print(f"Q: {question}")
        print(f"A: {answer}")

    # Show learned strategies
    if agent.playbook.bullets():
        print(f"\n💡 Recent learned strategies:")
        recent_bullets = agent.playbook.bullets()[-3:]  # Last 3
        for bullet in recent_bullets:
            helpful = bullet.helpful
            harmful = bullet.harmful
            score = f"(+{helpful}/-{harmful})"
            print(f"  • {bullet.content[:70]}... {score}")

    # Save strategies
    agent.save_playbook(str(playbook_path))
    print(f"\n💾 Saved learned strategies to {playbook_path}")
    print("🔄 Next run will automatically load these strategies!")


def main():
    """Run the quickstart demo with available providers."""
    print("=" * 60)
    print("🚀 ACELiteLLM Quickstart Demo")
    print("Self-improving AI agents with LiteLLM")
    print("=" * 60)

    # Check available providers
    available = check_api_keys()
    print("\n🔑 Available API providers:")

    has_any_key = False
    for provider, available_status in available.items():
        status = "✅" if available_status else "❌"
        print(f"  {status} {provider}")
        if available_status:
            has_any_key = True

    if not has_any_key:
        print("\n❌ No API keys found!")
        print("Please copy .env.example to .env and add your API keys.")
        print("\nSupported providers:")
        print("  - OPENAI_API_KEY (for GPT models)")
        print("  - ANTHROPIC_API_KEY (for Claude models)")
        print("  - GOOGLE_API_KEY (for Gemini models)")
        print("  - COHERE_API_KEY (for Cohere models)")
        return

    # Get recommended model
    model, description = get_recommended_model(available)
    print(f"\n🎯 Using: {description}")

    # Run example based on available provider
    agent = None
    playbook_path = None
    provider_name = None

    if available.get("OpenAI (GPT)"):
        result = example_openai()
        if result:
            agent, playbook_path = result
            provider_name = "OpenAI GPT"
    elif available.get("Anthropic (Claude)"):
        result = example_anthropic()
        if result:
            agent, playbook_path = result
            provider_name = "Anthropic Claude"
    elif available.get("Google (Gemini)"):
        result = example_google()
        if result:
            agent, playbook_path = result
            provider_name = "Google Gemini"

    if agent:
        run_learning_demo(agent, playbook_path, provider_name)
    else:
        print("❌ Failed to create agent with available providers")
        return

    print("\n" + "=" * 60)
    print("✅ Quickstart demo completed!")
    print("=" * 60)
    print("\n💡 Next steps:")
    print("  • Run this script again to see incremental learning")
    print("  • Try different models by changing the model parameter")
    print("  • Add more training samples to improve performance")
    print("  • Check other examples in the examples/ directory")


if __name__ == "__main__":
    main()