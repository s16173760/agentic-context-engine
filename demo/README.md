# Code Bug Hunter Demo

This demo showcases ACE's performance improvements by comparing baseline LLM vs ACE-enhanced LLM on bug detection tasks.

## Overview

The demo runs **10 buggy code samples** through both baseline and ACE modes, measuring:

- **💰 Tokens Consumed**: How efficiently the model uses tokens
- **⚡ Time to Completion**: Speed of bug detection
- **✨ Quality Output**: Accuracy and completeness of bug detection

## Quick Start

### 1. Set your Anthropic API key:
```bash
export ANTHROPIC_API_KEY='your-anthropic-api-key-here'
```

### 2. Run the demo:
```bash
# From the project root
python demo/demo_bug_hunter.py

# Or with UV
uv run python demo/demo_bug_hunter.py
```

### 3. (Optional) Disable OPIK logging if you get errors:
```bash
export OPIK_PROJECT_NAME=""
```

## What to Expect

The demo will:

1. **🔍 Run Baseline Mode**: Process all 10 samples without ACE learning
2. **🧠 Run ACE Mode**: Process samples with learning enabled
3. **📊 Show Comparison**: Display side-by-side metrics
4. **📚 Show Learned Strategies**: Display what ACE learned

### Sample Output:
```
🔍 BASELINE Sample #1: ✅ 85.0% accuracy | 🪙 874 tokens | ⏱️ 3.2s
🔍 BASELINE Sample #2: ⚠️ 65.0% accuracy | 🪙 892 tokens | ⏱️ 3.5s
...
🧠 ACE Sample #1: ✅ 90.0% accuracy | 🪙 654 tokens | ⏱️ 2.1s
🧠 ACE Sample #2: ✅ 88.0% accuracy | 🪙 621 tokens | ⏱️ 1.9s
...

📊 FINAL COMPARISON: BASELINE vs ACE
================================================================================

💰 TOKENS CONSUMED:
  Baseline: 8,456 total (845 avg/sample)
  ACE:      5,234 total (523 avg/sample)
  💵 Savings: -38.1% (3,222 tokens)

⚡ TIME TO COMPLETION:
  Baseline: 32.5s total (3.2s avg/sample)
  ACE:      19.8s total (2.0s avg/sample)
  ⏱️ Savings: -39.1% (12.7s faster)

✨ QUALITY OUTPUT:
  Baseline: 72.5% avg accuracy (6/10 high quality)
  ACE:      87.3% avg accuracy (9/10 high quality)
  📈 Improvement: +14.8 percentage points
```

## Files in this Demo

- `demo_bug_hunter.py` - Main demo script with parallel comparison
- `buggy_code_samples.py` - 10 code samples with various bug types
- `bug_hunter_environment.py` - Custom evaluation environment
- `results/` - Directory for saved results (created automatically)

## Bug Types Covered

1. Division by zero
2. Off-by-one errors
3. Mutation bugs
4. Performance issues (O(n²))
5. Logic errors (== vs =)
6. Missing error handling
7. Missing edge cases
8. Unit confusion
9. Overly broad exceptions
10. Iterator modification

## Customization

### Change the model:
Edit `demo_bug_hunter.py`:
```python
client = LiteLLMClient(
    model="claude-3-5-sonnet-20241022",  # Use different model
    temperature=0.0,
    max_tokens=1000
)
```

### Add more samples:
Edit `buggy_code_samples.py` and append to `BUGGY_SAMPLES` list.

### Adjust evaluation:
Edit `bug_hunter_environment.py` to change quality scoring.

## Tips for Presentation

1. **Run once before demo** to warm up and check it works
2. **Use split terminal** to show both modes side-by-side in real-time
3. **Highlight learned strategies** at the end - they're impressive!
4. **Compare token costs** using OpenAI/Anthropic pricing
5. **Show the results file** for documentation

## Troubleshooting

**OPIK Errors:**
```bash
export OPIK_PROJECT_NAME=""
```

**API Key Issues:**
```bash
echo $ANTHROPIC_API_KEY  # Should show your key
```

**Import Errors:**
```bash
# Make sure you're in the project root
cd /path/to/agentic-context-engine
python demo/demo_bug_hunter.py
```

## Next Steps

After running this demo, you can:
- Save the learned playbook for future use
- Try with different models (GPT-4, Claude Opus, etc.)
- Add more complex bug samples
- Create similar demos for other use cases

---

**Built with the ACE Framework** 🚀

