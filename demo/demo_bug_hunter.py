#!/usr/bin/env python3
"""
Code Bug Hunter Demo - Baseline vs ACE Comparison

This demo shows ACE's ability to improve bug detection over time by:
1. Learning common bug patterns
2. Reducing token usage through learned strategies
3. Improving detection quality and speed

Usage:
    export ANTHROPIC_API_KEY="your-key"
    python demo/demo_bug_hunter.py
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ace import (
    Generator, Reflector, Curator, OfflineAdapter, Playbook, Sample
)
from ace.llm_providers import LiteLLMClient

from buggy_code_samples import BUGGY_SAMPLES
from bug_hunter_environment import BugHunterEnvironment


@dataclass
class BugHuntResult:
    """Results from bug detection."""
    sample_id: int
    mode: str  # "baseline" or "ace"
    response: str
    tokens_used: int
    time_seconds: float
    accuracy: float
    quality_metrics: Dict[str, float]


class MetricsTracker:
    """Track and display metrics in real-time."""
    
    def __init__(self):
        self.results = []
    
    def add_result(self, result: BugHuntResult):
        """Add a result and display progress."""
        self.results.append(result)
        
        # Print progress
        mode_emoji = "🔍" if result.mode == "baseline" else "🧠"
        quality_emoji = "✅" if result.accuracy >= 0.8 else "⚠️" if result.accuracy >= 0.6 else "❌"
        
        print(f"{mode_emoji} {result.mode.upper()} Sample #{result.sample_id}: "
              f"{quality_emoji} {result.accuracy:.1%} accuracy | "
              f"🪙 {result.tokens_used} tokens | "
              f"⏱️  {result.time_seconds:.1f}s")
    
    def get_summary(self, mode: str) -> Dict[str, Any]:
        """Get summary statistics for a mode."""
        mode_results = [r for r in self.results if r.mode == mode]
        
        if not mode_results:
            return {}
        
        total_tokens = sum(r.tokens_used for r in mode_results)
        total_time = sum(r.time_seconds for r in mode_results)
        avg_accuracy = sum(r.accuracy for r in mode_results) / len(mode_results)
        
        return {
            "total_samples": len(mode_results),
            "total_tokens": total_tokens,
            "avg_tokens": total_tokens / len(mode_results),
            "total_time": total_time,
            "avg_time": total_time / len(mode_results),
            "avg_accuracy": avg_accuracy,
            "high_quality_count": sum(1 for r in mode_results if r.accuracy >= 0.8),
        }
    
    def print_comparison(self):
        """Print side-by-side comparison."""
        baseline_summary = self.get_summary("baseline")
        ace_summary = self.get_summary("ace")
        
        if not baseline_summary or not ace_summary:
            print("⚠️  Not enough data for comparison")
            return
        
        print("\n" + "="*80)
        print("📊 FINAL COMPARISON: BASELINE vs ACE")
        print("="*80)
        
        # Tokens comparison
        token_savings = (1 - ace_summary["avg_tokens"] / baseline_summary["avg_tokens"]) * 100
        print(f"\n💰 TOKENS CONSUMED:")
        print(f"  Baseline: {baseline_summary['total_tokens']:,} total "
              f"({baseline_summary['avg_tokens']:.0f} avg/sample)")
        print(f"  ACE:      {ace_summary['total_tokens']:,} total "
              f"({ace_summary['avg_tokens']:.0f} avg/sample)")
        print(f"  💵 Savings: {token_savings:+.1f}% ({baseline_summary['total_tokens'] - ace_summary['total_tokens']:,} tokens)")
        
        # Time comparison
        time_savings = (1 - ace_summary["avg_time"] / baseline_summary["avg_time"]) * 100
        print(f"\n⚡ TIME TO COMPLETION:")
        print(f"  Baseline: {baseline_summary['total_time']:.1f}s total "
              f"({baseline_summary['avg_time']:.1f}s avg/sample)")
        print(f"  ACE:      {ace_summary['total_time']:.1f}s total "
              f"({ace_summary['avg_time']:.1f}s avg/sample)")
        print(f"  ⏱️  Savings: {time_savings:+.1f}% ({baseline_summary['total_time'] - ace_summary['total_time']:.1f}s faster)")
        
        # Quality comparison
        quality_improvement = (ace_summary["avg_accuracy"] - baseline_summary["avg_accuracy"]) * 100
        print(f"\n✨ QUALITY OUTPUT:")
        print(f"  Baseline: {baseline_summary['avg_accuracy']:.1%} avg accuracy "
              f"({baseline_summary['high_quality_count']}/{baseline_summary['total_samples']} high quality)")
        print(f"  ACE:      {ace_summary['avg_accuracy']:.1%} avg accuracy "
              f"({ace_summary['high_quality_count']}/{ace_summary['total_samples']} high quality)")
        print(f"  📈 Improvement: {quality_improvement:+.1f} percentage points")
        
        print("\n" + "="*80)


def run_baseline_detection(samples: List[Sample], client: LiteLLMClient, 
                          environment: BugHunterEnvironment, tracker: MetricsTracker):
    """Run baseline bug detection (no ACE)."""
    print("\n" + "="*80)
    print("🔍 RUNNING BASELINE BUG DETECTION (No ACE)")
    print("="*80 + "\n")
    
    generator = Generator(client)
    playbook = Playbook()  # Empty playbook
    
    for sample in samples:
        start_time = time.time()
        
        # Generate response
        output = generator.generate(
            question=f"Analyze this code and identify any bugs:\n\n{sample.question}",
            context="You are a code reviewer. Identify bugs, explain the issue, and suggest a fix.",
            playbook=playbook
        )
        
        elapsed = time.time() - start_time
        
        # Evaluate
        env_result = environment.evaluate(sample, output)
        
        # Track result
        result = BugHuntResult(
            sample_id=sample.metadata.get("id", 0),
            mode="baseline",
            response=output.final_answer,
            tokens_used=output.usage.total_tokens if output.usage else 0,
            time_seconds=elapsed,
            accuracy=env_result.metrics.get("accuracy", 0),
            quality_metrics=env_result.metrics
        )
        tracker.add_result(result)


def run_ace_detection(samples: List[Sample], client: LiteLLMClient,
                     environment: BugHunterEnvironment, tracker: MetricsTracker):
    """Run ACE-enhanced bug detection with learning."""
    print("\n" + "="*80)
    print("🧠 RUNNING ACE BUG DETECTION (With Learning)")
    print("="*80 + "\n")
    
    generator = Generator(client)
    reflector = Reflector(client)
    curator = Curator(client)
    
    adapter = OfflineAdapter(
        playbook=Playbook(),
        generator=generator,
        reflector=reflector,
        curator=curator,
        max_refinement_rounds=1,
        enable_observability=False  # Disable to avoid OPIK errors
    )
    
    # Run ACE adaptation
    print("🔄 ACE is learning from samples...")
    adaptation_results = adapter.run(samples, environment, epochs=1)
    
    # Track results
    for step in adaptation_results:
        elapsed = step.environment_result.metadata.get("time_elapsed", 0)
        
        result = BugHuntResult(
            sample_id=step.sample.metadata.get("id", 0),
            mode="ace",
            response=step.generator_output.final_answer,
            tokens_used=step.generator_output.usage.total_tokens if step.generator_output.usage else 0,
            time_seconds=elapsed if elapsed else 0,
            accuracy=step.environment_result.metrics.get("accuracy", 0),
            quality_metrics=step.environment_result.metrics
        )
        tracker.add_result(result)
    
    # Show learned strategies
    print("\n" + "="*80)
    print("📚 LEARNED STRATEGIES:")
    print("="*80)
    bullets = adapter.playbook.bullets()
    if bullets:
        for i, bullet in enumerate(bullets[:10], 1):  # Show top 10
            print(f"{i}. {bullet.content}")
            print(f"   Impact: +{bullet.helpful_count} helpful, -{bullet.harmful_count} harmful")
    else:
        print("  No strategies learned yet")
    print()


def main():
    """Run the demo."""
    print("\n" + "="*80)
    print("🎯 CODE BUG HUNTER DEMO: BASELINE vs ACE")
    print("="*80)
    print("\nThis demo compares:")
    print("  • Token consumption")
    print("  • Time to completion")
    print("  • Bug detection quality")
    print("\nUsing 10 buggy code samples with Claude Sonnet 4.5")
    print("="*80 + "\n")
    
    # Check API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        print("   Please run: export ANTHROPIC_API_KEY='your-key'")
        sys.exit(1)
    
    # Initialize
    client = LiteLLMClient(
        model="claude-sonnet-4-5-20250929",
        temperature=0.0,  # Deterministic for comparison
        max_tokens=1000
    )
    
    environment = BugHunterEnvironment()
    tracker = MetricsTracker()
    
    # Convert samples to ACE format
    samples = [
        Sample(
            question=sample["code"],
            ground_truth=sample["ground_truth"],
            context=f"Language: {sample['language']}, Bug Type: {sample['bug_type']}",
            metadata={"id": sample["id"], "severity": sample["severity"]}
        )
        for sample in BUGGY_SAMPLES
    ]
    
    # Run both modes
    try:
        run_baseline_detection(samples, client, environment, tracker)
        run_ace_detection(samples, client, environment, tracker)
        
        # Show final comparison
        tracker.print_comparison()
        
        # Save results
        output_dir = ROOT / "demo" / "results"
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"bug_hunter_results_{timestamp}.txt"
        
        with open(output_file, "w") as f:
            f.write("CODE BUG HUNTER DEMO RESULTS\n")
            f.write("="*80 + "\n\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Model: claude-sonnet-4-5-20250929\n")
            f.write(f"Samples: {len(samples)}\n\n")
            
            baseline_summary = tracker.get_summary("baseline")
            ace_summary = tracker.get_summary("ace")
            
            f.write("BASELINE RESULTS:\n")
            f.write(f"  Total Tokens: {baseline_summary['total_tokens']:,}\n")
            f.write(f"  Total Time: {baseline_summary['total_time']:.1f}s\n")
            f.write(f"  Avg Accuracy: {baseline_summary['avg_accuracy']:.1%}\n\n")
            
            f.write("ACE RESULTS:\n")
            f.write(f"  Total Tokens: {ace_summary['total_tokens']:,}\n")
            f.write(f"  Total Time: {ace_summary['total_time']:.1f}s\n")
            f.write(f"  Avg Accuracy: {ace_summary['avg_accuracy']:.1%}\n\n")
            
            token_savings = (1 - ace_summary["avg_tokens"] / baseline_summary["avg_tokens"]) * 100
            time_savings = (1 - ace_summary["avg_time"] / baseline_summary["avg_time"]) * 100
            quality_improvement = (ace_summary["avg_accuracy"] - baseline_summary["avg_accuracy"]) * 100
            
            f.write("IMPROVEMENTS:\n")
            f.write(f"  Token Savings: {token_savings:.1f}%\n")
            f.write(f"  Time Savings: {time_savings:.1f}%\n")
            f.write(f"  Quality Improvement: {quality_improvement:+.1f} percentage points\n")
        
        print(f"\n💾 Results saved to: {output_file}")
        print("\n✅ Demo completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

