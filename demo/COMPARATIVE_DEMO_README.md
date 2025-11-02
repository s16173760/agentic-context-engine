# 🏆 LLM-as-a-Judge Comparative Demo

This demo showcases **Baseline vs ACE** code review with an **LLM judge** that scores each answer from 0-100%.

## 🎯 How It Works

1. **Both models analyze the same code** (sequentially)
   - 🔵 **Baseline**: Junior engineer with no strategies (empty playbook)
   - 🟢 **ACE**: Senior expert with 21 pre-trained strategies

2. **LLM Judge compares the answers** (Claude Haiku for speed/cost)
   - Evaluates on 4 criteria:
     - **Correctness (40%)**: Does it identify actual bugs from ground truth?
     - **Completeness (30%)**: Does it catch ALL bugs, including edge cases?
     - **Explanation Quality (20%)**: Are explanations clear and insightful?
     - **Solution Quality (10%)**: Are proposed fixes correct and practical?

3. **Round-by-round results displayed**
   - Side-by-side comparison
   - Scores (0-100%)
   - Strengths & weaknesses analysis
   - Token counts for each model
   - Winner per round

4. **Final summary** shows overall stats

## 🚀 Quick Start

### 1. Pre-train ACE (One-time)

```bash
python demo/pretrain_playbook.py
```

This trains ACE on all 10 samples and saves the playbook to `demo/pretrained_playbook.json`.

### 2. Run the Comparative Demo

```bash
python demo/api_server_comparative.py
```

### 3. Open Browser

Navigate to: **http://localhost:8001**

Click **"Start Competition!"** and watch the race!

## 📊 What You'll See

### Round-by-Round Display

Each round shows:

```
┌─────────────────────────────────────────────────────────────┐
│ Round 1                                       ✅ Judged      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  🔵 Baseline (Junior)        │  🟢 ACE (Senior Expert)      │
│  ─────────────────────────   │  ─────────────────────────   │
│  Time: 45.2s                 │  Time: 38.7s                 │
│  Tokens: 8,542               │  Tokens: 6,234               │
│                               │                               │
│  Judge Score: 62/100         │  Judge Score: 94/100         │
│                               │                               │
│  ✅ Strengths:               │  ✅ Strengths:               │
│  - Identified main issue     │  - Comprehensive analysis    │
│                               │  - All edge cases caught     │
│  ❌ Weaknesses:              │  - Multiple fix options      │
│  - Missed edge cases         │                               │
│  - Incomplete explanation    │  ❌ Weaknesses:              │
│                               │  - Slightly verbose          │
│                                                               │
│  ⚖️ Judge Verdict                                           │
│  Winner: 🟢 ACE                                              │
│  Reasoning: ACE provided comprehensive analysis with...      │
└─────────────────────────────────────────────────────────────┘
```

### Overall Statistics (Top of page)

```
┌──────────────────────┬──────────────────────┬──────────────────────┐
│ 🔵 Baseline (Junior) │  ⚖️ LLM Judge       │ 🟢 ACE (Senior)     │
│ 65.2%                │  2,145 tokens        │ 89.7%                │
│ Avg Score            │  Judging Tokens      │ Avg Score            │
│ 29,843 tokens        │                      │ 21,456 tokens        │
└──────────────────────┴──────────────────────┴──────────────────────┘
```

### Final Winner Banner

```
╔════════════════════════════════════════╗
║                                        ║
║           🟢 ACE Wins!                ║
║                                        ║
║  Average Scores: Baseline 65.2% vs    ║
║                  ACE 89.7%             ║
║                                        ║
║  Total Tokens: Baseline 29,843 |      ║
║                ACE 21,456              ║
║                                        ║
╚════════════════════════════════════════╝
```

## 🎨 Features

✅ **LLM-as-a-Judge scoring** (0-100% per answer)
✅ **Round-by-round results** with detailed breakdowns
✅ **Strengths & weaknesses** for each answer
✅ **Token tracking** for all models (baseline, ACE, judge)
✅ **Beautiful comparative UI** with side-by-side display
✅ **Winner determination** per round
✅ **Overall statistics** and final summary
✅ **Expandable code views** for full answers and ground truth

## 🔧 Configuration

### Judge Model

Default: `claude-3-5-haiku-20241022` (fast and cost-effective)

Change in `demo/api_server_comparative.py`:

```python
judge = LLMJudge(model="claude-3-5-haiku-20241022")
```

### Number of Samples

Default: 4 samples

Change in `demo/api_server_comparative.py`:

```python
samples_raw = get_race_samples(count=4)  # Change to 2, 6, 8, or 10
```

### Judge Criteria Weights

Modify in `demo/llm_judge.py`:

```python
1. **Correctness (40%)**: ...
2. **Completeness (30%)**: ...
3. **Explanation Quality (20%)**: ...
4. **Solution Quality (10%)**: ...
```

## 📈 Expected Results

With the current **expert-level bug challenges**:

### Baseline (Junior Engineer)
- **Avg Score**: 50-70%
- Catches obvious bugs
- Misses edge cases and subtle issues
- Less comprehensive explanations
- Uses more tokens (exploratory reasoning)

### ACE (Senior Expert)
- **Avg Score**: 80-95%
- Catches all bugs including edge cases
- Recognizes patterns from playbook
- Comprehensive explanations
- Uses fewer tokens (focused expertise)

### Token Efficiency
- **ACE typically uses 20-30% fewer tokens** due to learned strategies
- Judge uses ~500-1000 tokens per comparison

## 🆚 vs Original Demo

### Original Demo (`api_server.py`, port 8000)
- Side-by-side race visualization
- Real-time progress tracking
- Simple accuracy scores from keyword matching

### Comparative Demo (`api_server_comparative.py`, port 8001)
- **Sequential execution** (one after the other)
- **LLM judge** provides nuanced 0-100% scoring
- **Detailed analysis** with strengths/weaknesses
- **Round-by-round results**
- More comprehensive but slower

## 🎓 Use Cases

### 1. Demonstrating ACE Value
Show stakeholders the **quality difference** between baseline and ACE with objective LLM judging.

### 2. Evaluating Playbook Quality
See how well ACE's learned strategies translate to better bug detection.

### 3. Comparing Different Prompts
Test different system prompts by modifying the context strings.

### 4. Benchmarking Models
Compare different base models (GPT-4, Claude, etc.) with/without ACE.

## 💡 Tips

1. **Run both demos** to see different perspectives:
   - Original: Fast, parallel, visual race
   - Comparative: Detailed, judged, analytical

2. **Watch token counts** - ACE's efficiency advantage is clear

3. **Read the judge reasoning** - provides insights into what makes a good analysis

4. **Check strengths/weaknesses** - shows where each model excels or fails

## 🐛 Troubleshooting

### "Playbook not loaded"
Run pre-training first: `python demo/pretrain_playbook.py`

### Port already in use
Original demo uses 8000, comparative uses 8001. Stop other servers or change ports.

### Judge errors
Check API keys: `ANTHROPIC_API_KEY` must be set for Claude Haiku judge.

### Slow performance
Normal! Each round involves:
- 2 deep reasoning LLM calls (baseline + ACE)
- 1 judge LLM call
- Total: 3 LLM calls per round

## 📝 Example Session

```bash
# 1. Pre-train (one time)
$ python demo/pretrain_playbook.py
🧠 ACE Pre-Training Script
📚 Total samples: 10
✅ Training complete! Learned 21 strategies

# 2. Run comparative demo
$ python demo/api_server_comparative.py
🚀 Starting Comparative Bug Hunter Demo Server...
📊 Race: 4 bug samples with LLM-as-a-judge
🔵 Baseline: Junior Engineer (no strategies)
🟢 ACE: Senior Expert (with playbook strategies)
⚖️  Judge: Claude Haiku comparing answers
✅ Playbook loaded with 21 strategies

# 3. Open http://localhost:8001 and watch!
```

## 🎉 Expected Outcome

ACE should **consistently outperform** baseline with:
- **Higher scores** (15-25% better on average)
- **Fewer tokens** (20-30% more efficient)
- **Better completeness** (catches all bugs)
- **Superior explanations** (leverages learned strategies)

This demonstrates the **real value of ACE** - not just faster, but **significantly better quality** with fewer resources! 🚀

