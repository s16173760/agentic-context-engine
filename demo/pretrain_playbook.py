#!/usr/bin/env python3
"""
Pre-train ACE and save the playbook for later use in demos.

Run this once to generate the playbook, then the demo will load it automatically.
"""

import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ace import Generator, Reflector, Curator, OfflineAdapter, Playbook, Sample
from ace.llm_providers import LiteLLMClient

# Import demo modules
sys.path.insert(0, str(Path(__file__).parent))
from buggy_code_samples import get_train_test_split
from bug_hunter_environment import BugHunterEnvironment


def pretrain_and_save():
    """Pre-train ACE on training samples and save playbook."""
    print("🧠 ACE Pre-Training Script")
    print("=" * 60)
    
    # Get training samples
    train_samples_raw, test_samples_raw = get_train_test_split(train_size=6)
    print(f"📚 Training samples: {len(train_samples_raw)}")
    print(f"🏁 Test samples: {len(test_samples_raw)}")
    print()
    
    # Initialize ACE components
    print("🔧 Initializing ACE components...")
    client = LiteLLMClient(
        model="claude-sonnet-4-5-20250929",
        temperature=0.0,
        max_tokens=1000
    )
    
    generator = Generator(client)
    reflector = Reflector(client)
    curator = Curator(client)
    environment = BugHunterEnvironment()
    
    adapter = OfflineAdapter(
        playbook=Playbook(),
        generator=generator,
        reflector=reflector,
        curator=curator,
        max_refinement_rounds=1,
        enable_observability=False
    )
    
    # Convert to Sample objects
    train_samples = [
        Sample(
            question=sample["code"],
            ground_truth=sample["ground_truth"],
            context=f"Language: {sample['language']}, Bug Type: {sample['bug_type']}",
            metadata={"id": sample["id"], "severity": sample["severity"]}
        )
        for sample in train_samples_raw
    ]
    
    print(f"✅ Ready to train on {len(train_samples)} samples")
    print()
    
    # Train on each sample
    print("📚 Training ACE...")
    print("-" * 60)
    
    for i, sample in enumerate(train_samples, 1):
        print(f"\n[{i}/{len(train_samples)}] Training on sample {sample.metadata['id']}...")
        print(f"    Bug Type: {train_samples_raw[i-1]['bug_type']}")
        
        # Run adapter on single sample
        adapter.run([sample], environment, epochs=1)
        
        # Show current playbook size
        bullet_count = len(adapter.playbook.bullets())
        print(f"    ✓ Learned strategies: {bullet_count}")
    
    print()
    print("-" * 60)
    print(f"✅ Training complete! Learned {len(adapter.playbook.bullets())} strategies")
    print()
    
    # Save playbook
    playbook_path = Path(__file__).parent / "pretrained_playbook.json"
    adapter.playbook.save_to_file(str(playbook_path))
    print(f"💾 Saved playbook to: {playbook_path}")
    print()
    
    # Show learned strategies
    print("📚 Learned Strategies:")
    print("-" * 60)
    for i, bullet in enumerate(adapter.playbook.bullets(), 1):
        print(f"{i}. {bullet.content}")
        print(f"   (✓ {bullet.helpful} helpful, ✗ {bullet.harmful} harmful)")
    
    print()
    print("=" * 60)
    print("🎉 Pre-training complete!")
    print()
    print("Next steps:")
    print("  1. Run the demo: python demo/api_server.py")
    print("  2. Open: http://localhost:8000")
    print("  3. Click 'Start Race!' to see ACE in action")
    print()


if __name__ == "__main__":
    import os
    
    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("❌ Error: ANTHROPIC_API_KEY not set")
        print()
        print("Set your API key first:")
        print("  export ANTHROPIC_API_KEY='your-key-here'")
        sys.exit(1)
    
    # Disable OPIK for pre-training
    os.environ["OPIK_PROJECT_NAME"] = ""
    
    try:
        pretrain_and_save()
    except KeyboardInterrupt:
        print("\n\n⚠️  Pre-training interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error during pre-training: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

