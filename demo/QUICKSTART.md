# 🚀 Bug Hunter Demo - Quick Start Guide

## One-Time Setup (Pre-Training)

### 1. Set your API key:
```bash
export ANTHROPIC_API_KEY='your-anthropic-key-here'
```

### 2. Run the pre-training script:
```bash
cd /Users/kyo/Dev/ef-builders-retreat/agentic-context-engine
python demo/pretrain_playbook.py
```

**What this does:**
- Trains ACE on 6 bug-finding samples
- Learns 8-10 strategies for detecting bugs
- Saves the playbook to `demo/pretrained_playbook.json`
- Takes ~30 seconds

**Output you'll see:**
```
🧠 ACE Pre-Training Script
============================================================
📚 Training samples: 6
🏁 Test samples: 4

🔧 Initializing ACE components...
✅ Ready to train on 6 samples

📚 Training ACE...
------------------------------------------------------------

[1/6] Training on sample 1...
    Bug Type: Division by zero
    ✓ Learned strategies: 2

[2/6] Training on sample 2...
    Bug Type: Off-by-one error
    ✓ Learned strategies: 4

...

✅ Training complete! Learned 8 strategies
💾 Saved playbook to: demo/pretrained_playbook.json

📚 Learned Strategies:
------------------------------------------------------------
1. Check for empty input validation before operations
2. Verify loop bounds to avoid off-by-one errors
3. Use .copy() to avoid mutating original dictionaries
...

🎉 Pre-training complete!
```

---

## Running the Demo (Every Time)

### 1. Start the server:
```bash
python demo/api_server.py
```

**Output:**
```
✅ Loaded pre-trained playbook with 8 strategies
🚀 Starting Bug Hunter Demo Server...
📊 Training: 6 samples | Testing: 4 samples
🌐 Open http://localhost:8000 in your browser
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 2. Open your browser:
```
http://localhost:8000
```

### 3. Click "Start Race! 🚀"

### 4. Watch the race:
- ✅ Message appears: "Using pre-trained playbook (8 strategies)"
- 🏁 Race begins immediately (no pre-training wait!)
- ⏱️  Timers tick in parallel
- 📝 Response boxes update in real-time
- 🎉 Winner announced after ~25 seconds

---

## What You'll See

### Race Layout:
```
┌─────────────────────────────────────────────────────────┐
│  🔍 Baseline LLM          🧠 ACE-Enhanced LLM          │
│  Time: 23.4s              Time: 15.2s                   │
│  Tokens: 3,245            Tokens: 1,987  📚 8 strategies│
│  Quality: 68%             Quality: 84%                   │
│                                                          │
│  Progress:                Progress:                      │
│  🟢 🟢 🟢 🔵 ⚪           🟢 🟢 🟢 🟢 ✅                │
│                                                          │
│  [Response box updates]   [Response box updates]        │
└─────────────────────────────────────────────────────────┘

            🎉 ACE-Enhanced LLM WINS! 🎉
            
            Token Savings: 38.8%
            Time Savings: 35.0%
            Quality Gain: +16.0%
```

### Learned Strategies Panel:
```
📚 Learned Strategies
────────────────────────────────────────────
1. Check for empty input validation...
2. Verify loop bounds to avoid off-by-one...
3. Use .copy() to avoid mutating original...
4. Use sets for O(1) lookups instead of O(n)...
5. Use assignment (=) not comparison (==)...
...
```

---

## Re-Training (Optional)

If you want to re-train with different settings:

```bash
# Remove old playbook
rm demo/pretrained_playbook.json

# Run pre-training again
python demo/pretrain_playbook.py
```

---

## Troubleshooting

### "No pre-trained playbook found"
**Problem:** Demo says playbook is missing  
**Solution:** Run `python demo/pretrain_playbook.py` first

### "ANTHROPIC_API_KEY not set"
**Problem:** API key not configured  
**Solution:** `export ANTHROPIC_API_KEY='your-key'`

### Pre-training is too slow
**Problem:** Takes longer than expected  
**Solution:** This is normal. It's doing real LLM calls to learn. Only needs to be done once!

### Want to use different model
**Problem:** Want to try different LLM  
**Solution:** Edit `pretrain_playbook.py` line 37:
```python
model="claude-3-5-sonnet-20241022",  # Change this
```

---

## File Structure

```
demo/
├── pretrain_playbook.py           ← Run this once
├── pretrained_playbook.json       ← Generated playbook (git ignored)
├── api_server.py                  ← Run this for demo
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── buggy_code_samples.py          ← The 10 bug samples
├── bug_hunter_environment.py      ← Evaluation logic
└── QUICKSTART.md                  ← This file
```

---

## Tips for Presentations

1. **Pre-train before your presentation**
   - Do this on reliable WiFi
   - Verify `pretrained_playbook.json` exists
   - Test the demo once to confirm it works

2. **During presentation**
   - Start server: `python demo/api_server.py`
   - Open browser to http://localhost:8000
   - Click "Start Race!" and narrate what's happening

3. **What to highlight**
   - "ACE pre-trained on 6 samples"
   - "Now testing on 4 new samples"
   - Point to real-time metrics
   - Emphasize the 35-40% savings
   - Show learned strategies at the end

4. **Backup plan**
   - Take a screen recording beforehand
   - Have screenshots ready
   - Keep terminal logs from pre-training

---

## Performance Metrics

**Typical Results:**
- **Token Savings:** 30-40%
- **Time Savings:** 30-40%
- **Quality Improvement:** 10-20 percentage points
- **Learned Strategies:** 8-12 strategies
- **Cost:** ~$0.02-0.04 for pre-training (one-time)

**Race Duration:**
- Pre-training: 25-35 seconds (one-time)
- Race: 20-30 seconds (every time)
- Total demo: ~30 seconds after pre-training

---

## Ready? Let's Go!

```bash
# 1. Pre-train (once)
export ANTHROPIC_API_KEY='your-key'
python demo/pretrain_playbook.py

# 2. Run demo (every time)
python demo/api_server.py

# 3. Open browser
open http://localhost:8000

# 4. Click "Start Race! 🚀"
```

Enjoy the show! 🎉

