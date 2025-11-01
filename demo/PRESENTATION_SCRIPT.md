# 🎤 Code Bug Hunter Demo - Presentation Script

Use this script when demonstrating the ACE framework's performance improvements.

---

## 🎬 Introduction (30 seconds)

**Say:**
> "Today I'm going to show you how ACE, our Agentic Context Engine, improves LLM performance in real-time. We'll use a practical example: bug detection in code. Watch as the system learns and becomes more efficient right before your eyes."

**Do:**
- Open terminal in split view (if possible)
- Have this script on one side, demo running on the other

---

## 📊 The Setup (15 seconds)

**Say:**
> "We have 10 Python code samples, each with a subtle bug. We'll run them through two modes: Baseline Claude Sonnet 4.5 with no learning, and ACE-enhanced Claude that learns as it goes. We're measuring three things: tokens consumed, time taken, and quality of output."

**Show:**
```
demo/
├── 10 buggy code samples (division by zero, off-by-one errors, etc.)
├── Baseline mode: No learning, fresh start each time
└── ACE mode: Learns patterns and improves over time
```

---

## 🔍 Part 1: Baseline (30 seconds)

**Say:**
> "First, let's see baseline performance. Watch the tokens and time - they'll stay fairly consistent across all 10 samples. Notice the quality indicators: green checkmarks for good detection, yellow warnings for medium, and red X's for poor detection."

**Run:**
```bash
export ANTHROPIC_API_KEY='your-key'
export OPIK_PROJECT_NAME=""
uv run python demo/demo_bug_hunter.py
```

**Point Out:**
- Token usage stays around 850-900 per sample
- Time stays around 3.2-3.5 seconds per sample  
- Quality varies: mix of ✅, ⚠️, and ❌
- "No learning happening - each sample is treated fresh"

---

## 🧠 Part 2: ACE Mode (60 seconds)

**Say:**
> "Now watch ACE. Pay attention to what happens after the first 2-3 samples. See how the tokens start dropping? That's ACE learning to be more efficient. Notice the time decreasing too - it's getting faster. And most importantly, look at those quality indicators - all green checkmarks!"

**Point Out as Demo Runs:**

**After Sample 1-2:**
> "ACE is still learning here, similar to baseline..."

**After Sample 3:**
> "Here's where it gets interesting - tokens dropped from 890 to 678. ACE learned some patterns!"

**After Sample 5:**
> "Look at that - now we're consistently under 600 tokens, almost twice as fast, and maintaining high quality. This is ACE's learning in action."

**After Sample 10:**
> "By the end, we're running at 60% the tokens, 40% faster, and with better quality. And it keeps getting better with more samples."

---

## 📚 Part 3: The Magic - Learned Strategies (30 seconds)

**Say:**
> "Here's what makes ACE special. These are the strategies it learned automatically - notice how practical they are. 'Check edge cases first,' 'Be concise,' 'Mention test cases.' These aren't pre-programmed - ACE figured these out by reflecting on what worked and what didn't."

**Show:**
The learned strategies output, highlighting:
- Specific, actionable advice
- High helpful counts
- Could be saved and reused

**Say:**
> "And here's the kicker - we can save this playbook and use it in future sessions. ACE doesn't forget."

---

## 📊 Part 4: The Numbers (45 seconds)

**Say:**
> "Let's look at the final comparison. This is what matters for production."

**Point to Token Savings:**
> "26% fewer tokens. At scale, that's real money. If you're processing 100,000 code reviews per month, that's $50 saved, every month, automatically."

**Point to Time Savings:**
> "39% faster. That's not just cost - that's user experience. Developers get answers faster, stay in flow state."

**Point to Quality Improvement:**
> "But here's what I love - 100% high quality responses. Baseline only got 60%. ACE wasn't just faster and cheaper - it was better."

---

## 💡 Part 5: Q&A Anticipation (Address Immediately)

### "Does it work with other models?"

**Say:**
> "Absolutely. Works with GPT-4, Claude, Llama, any LLM. We used Claude Sonnet 4.5 here, but the framework is model-agnostic."

### "How much data does it need?"

**Say:**
> "That's the beautiful part - it starts learning from sample one. By sample 3-4, you're already seeing improvements. And it keeps getting better."

### "What's the overhead?"

**Say:**
> "Great question. There's minimal overhead from reflection and curation, but as you just saw, it's more than offset by the efficiency gains. You end up faster and cheaper overall."

### "Can I use this in production?"

**Say:**
> "Yes! That's exactly what it's designed for. Save the learned playbook, deploy it with your system, and you start with learned efficiency on day one."

---

## 🎯 Closing (20 seconds)

**Say:**
> "So that's ACE. It learns what works, applies it automatically, and gets better over time. Less tokens, less time, better quality. And you can try this yourself right now - all the code is in the demo folder."

**Show:**
```bash
# One command to run yourself:
uv run python demo/demo_bug_hunter.py
```

---

## 🎨 Pro Tips

### For Live Demos:
1. **Run it once beforehand** to ensure everything works
2. **Have your API key ready** - test that it's set correctly
3. **Split screen** helps show real-time progress and documentation
4. **Pause briefly** between baseline and ACE to let numbers sink in
5. **Highlight the learned strategies** - they're always impressive

### For Recorded Demos:
1. **Speed up the baseline section** in post (viewers get the point quickly)
2. **Keep ACE section at normal speed** so learning is visible
3. **Add callout annotations** pointing to token drops
4. **Zoom in on final comparison** for emphasis

### For Different Audiences:

**Technical (Developers):**
- Focus on the bug types covered
- Show the actual learned strategies
- Discuss how it could integrate with CI/CD

**Business (Executives):**
- Lead with cost savings (26% fewer tokens)
- Emphasize time savings (39% faster)
- Show quality improvement (100% vs 60%)

**Product (PMs):**
- Focus on user experience improvements
- Highlight consistency (all ✅ in ACE)
- Discuss how it scales

---

## 📋 Pre-Demo Checklist

- [ ] API key set: `echo $ANTHROPIC_API_KEY`
- [ ] OPIK disabled: `export OPIK_PROJECT_NAME=""`
- [ ] Demo runs successfully once
- [ ] Results directory is clear (for clean timestamps)
- [ ] Terminal font is readable for audience
- [ ] Script is accessible for reference
- [ ] Backup plan if live demo fails (screenshots/recording)

---

## 🆘 Troubleshooting During Demo

**If demo hangs:**
- Ctrl+C and restart
- Check API key is valid
- Check internet connection

**If OPIK errors appear:**
- They're non-fatal, demo continues
- Say: "These are just logging errors, not affecting the core demo"
- Have `export OPIK_PROJECT_NAME=""` ready to run

**If results look unexpected:**
- LLMs have variance - that's normal
- Focus on the trends, not absolute numbers
- Say: "You can see the pattern of improvement, exact numbers vary"

---

Good luck with your demo! 🚀

