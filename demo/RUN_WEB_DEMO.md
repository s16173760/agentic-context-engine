# 🎮 Bug Hunter Race - Visual Web Demo

An exciting visual race interface showing Baseline LLM vs ACE-Enhanced LLM side-by-side!

## 🚀 Quick Start

### 1. Set your API key:
```bash
export ANTHROPIC_API_KEY='your-anthropic-key-here'
```

### 2. (Optional) Disable OPIK logging:
```bash
export OPIK_PROJECT_NAME=""
```

### 3. Install additional requirements:
```bash
pip install fastapi uvicorn python-multipart
# Or with UV:
uv pip install fastapi uvicorn python-multipart
```

### 4. Start the server:
```bash
cd /Users/kyo/Dev/ef-builders-retreat/agentic-context-engine
python demo/api_server.py

# Or with UV:
uv run python demo/api_server.py
```

### 5. Open your browser:
```
http://localhost:8000
```

### 6. Click "Start Race! 🚀" and watch the magic!

---

## 🎯 What You'll See

### Visual Layout

```
┌──────────────────────────────────────────────────────────┐
│          🏁 Code Bug Hunter Race                         │
│        Baseline LLM vs ACE-Enhanced LLM                  │
│                                                           │
│   [Start Race! 🚀]         [Reset Race 🔄]             │
└──────────────────────────────────────────────────────────┘

┌─────────────────────────┬─────────────────────────────┐
│   🔍 Baseline LLM       │   🧠 ACE-Enhanced LLM      │
│   Time: 34.2s           │   Time: 21.3s               │
│   Tokens: 8,456         │   Tokens: 5,234             │
│   Quality: 72%          │   Quality: 87%              │
│                         │   📚 Strategies: 8          │
├─────────────────────────┼─────────────────────────────┤
│  Progress Track:        │  Progress Track:            │
│  ⚪ Sample 1            │  🟢 Sample 1 ✅ 87% ...   │
│  ⚪ Sample 2            │  🟢 Sample 2 ✅ 90% ...   │
│  ⚪ Sample 3            │  🟢 Sample 3 ✅ 85% ...   │
│  ...                    │  ...                         │
├─────────────────────────┼─────────────────────────────┤
│  Current Response:      │  Current Response:          │
│  [Bug detection text]   │  [Bug detection text]       │
└─────────────────────────┴─────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│          🏆 ACE WINS! 🎉                                │
│                                                           │
│  Token Savings: 38.1%  │  Time Savings: 37.7%         │
│  Quality +15.0%        │  High Quality: 10/10         │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│          📚 Learned Strategies                           │
│                                                           │
│  1. Check for edge cases first...                       │
│  2. Identify the bug type quickly...                    │
│  3. For Python bugs, focus on common patterns...        │
└──────────────────────────────────────────────────────────┘
```

---

## 🎨 Visual Features

### Real-Time Progress
- **Dots animate** as each sample is processed
- **⚪ → 🔵 → 🟢** progression (waiting → processing → complete)
- **Scrolls automatically** to current sample

### Live Metrics
- **Time counter** updates in real-time (shows who's faster)
- **Token counter** increments per sample (shows efficiency)
- **Quality percentage** updates with running average
- **Strategies count** (ACE only) shows learning progress

### Visual Indicators
- **✅ Green** = High quality (≥80% accuracy)
- **⚠️ Yellow** = Medium quality (60-79%)
- **❌ Red** = Low quality (<60%)
- **Glowing border** on active lane during processing

### Winner Announcement
- **Animated banner** slides down when race completes
- **Side-by-side comparison** of final metrics
- **Percentage improvements** highlighted
- **Learned strategies** displayed in dedicated panel

---

## 🔧 Technical Details

### Architecture

**Backend (FastAPI)**
- `/api/stream/baseline` - Server-Sent Events for baseline progress
- `/api/stream/ace` - Server-Sent Events for ACE progress
- `/api/samples` - Get bug samples metadata
- Real-time streaming with async generators

**Frontend (Vanilla JS)**
- EventSource API for SSE connections
- Parallel race execution (both run simultaneously)
- Real-time DOM updates without page refresh
- Responsive design (works on mobile too)

### Event Stream Format

```javascript
// Progress event
{ type: "progress", sample_id: 1, status: "processing" }

// Result event
{ 
  type: "result", 
  sample_id: 1, 
  accuracy: 0.85,
  tokens: 654,
  time: 2.1,
  total_tokens: 654,
  total_time: 2.1,
  response: "Bug found: ..."
}

// Strategies event (ACE only)
{
  type: "strategies",
  strategies: [
    { content: "...", helpful: 7, harmful: 0 },
    ...
  ]
}

// Complete event
{ type: "complete", total_tokens: 5234, total_time: 21.3 }
```

---

## 🎭 Presentation Tips

### For Live Demos

1. **Before Demo**:
   - Clear browser cache
   - Test API key is working
   - Have terminal ready with server running
   - Open browser to http://localhost:8000

2. **During Demo**:
   - "Watch the progress dots fill up in real-time"
   - "Notice how ACE's tokens start dropping after sample 2-3"
   - "See the quality indicators - more green on ACE side"
   - "Look at the time - ACE is consistently faster"

3. **After Race**:
   - Point to winner banner: "38% token savings!"
   - Highlight strategies: "These were learned automatically"
   - Explain reusability: "Can save and reuse these"

### For Recorded Demos

1. **Screen Recording Tips**:
   - Record at 1920x1080 for clarity
   - Use Chrome DevTools to show Network tab (optional)
   - Add cursor highlighting for better visibility
   - Consider picture-in-picture with your face

2. **Video Editing**:
   - Speed up to 1.5x if too slow
   - Add callout arrows to metrics
   - Highlight token drop moments
   - Zoom in on winner banner

### For Screenshots/Slides

1. **Key Screenshots to Capture**:
   - Initial state (before race)
   - Mid-race (showing progress dots)
   - Winner banner (with metrics)
   - Learned strategies panel

2. **Slide Sequence**:
   - Slide 1: Problem statement
   - Slide 2: Race in progress (side-by-side)
   - Slide 3: Final results comparison
   - Slide 4: Learned strategies

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Find process on port 8000
lsof -i :8000

# Kill it
kill -9 <PID>

# Or use different port
uvicorn demo.api_server:app --port 8001
```

### API Connection Fails
```bash
# Check server is running
curl http://localhost:8000/api/samples

# Check browser console for errors
# Check CORS is enabled (should be automatic)
```

### Streaming Stops/Hangs
- Check API key is valid
- Check internet connection
- Refresh browser and try again
- Check server terminal for errors

### OPIK Errors
```bash
# Disable OPIK completely
export OPIK_PROJECT_NAME=""
unset OPIK_URL_OVERRIDE
unset OPIK_BASE_URL
```

---

## 📊 Expected Performance

**Typical Results:**
- **Duration**: 2-3 minutes total
- **Token Savings**: 25-40%
- **Time Savings**: 35-45%
- **Quality Improvement**: 10-20 percentage points
- **Cost**: $0.02-0.04 per race

**What Makes a Good Demo:**
- Clear visual progression
- Obvious metric differences
- Engaging "race" feel
- Learned strategies are impressive

---

## 🎯 Customization

### Change Model
Edit `demo/api_server.py`:
```python
client = LiteLLMClient(
    model="claude-3-5-sonnet-20241022",  # Different model
    temperature=0.0,
    max_tokens=1000
)
```

### Adjust Sample Count
Edit `demo/buggy_code_samples.py` to add/remove samples.

### Modify Styling
Edit `demo/frontend/styles.css` to customize colors, fonts, layout.

### Add More Metrics
Edit `demo/frontend/app.js` to track additional metrics.

---

## 🌟 Advanced Features

### Save Race Results
The server logs all results. Add endpoint to save:
```python
@app.post("/api/save-results")
async def save_results(data: dict):
    # Save to file or database
    pass
```

### Multiple Races
Modify frontend to show history of multiple races.

### Compare Different Models
Add dropdown to select different models for comparison.

### Real-Time Charts
Integrate Chart.js for live metric visualizations.

---

## 📝 Files Structure

```
demo/
├── api_server.py           - FastAPI backend with streaming
├── frontend/
│   ├── index.html         - Main UI layout
│   ├── styles.css         - Visual styling (dark theme)
│   └── app.js             - Race logic and SSE handling
├── bug_hunter_environment.py  - Evaluation logic
├── buggy_code_samples.py     - Bug samples
├── requirements.txt          - Additional dependencies
└── RUN_WEB_DEMO.md          - This file
```

---

## 🚀 Ready to Race!

Just run:
```bash
export ANTHROPIC_API_KEY='your-key'
python demo/api_server.py
```

Then open: **http://localhost:8000**

Click **"Start Race! 🚀"** and enjoy the show! 🎉

---

**Questions?** Check the main demo/README.md or demo/PRESENTATION_SCRIPT.md

