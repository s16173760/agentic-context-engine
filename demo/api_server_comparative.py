"""
Comparative demo API server with LLM-as-a-judge.

Both baseline and ACE run in sequence, then LLM judge compares them.
Shows round-by-round results with token tracking.
"""

import sys
import json
import asyncio
import time
from pathlib import Path
from typing import AsyncGenerator, Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles

# Add demo directory to path
sys.path.insert(0, str(Path(__file__).parent))

from ace import Generator, Reflector, Curator, OfflineAdapter, Playbook, Sample
from ace.llm_providers import LiteLLMClient

# Import demo modules
sys.path.insert(0, str(Path(__file__).parent))
from buggy_code_samples import BUGGY_SAMPLES, get_all_samples, get_race_samples
from bug_hunter_environment import BugHunterEnvironment
from llm_judge import LLMJudge

app = FastAPI(title="Bug Hunter Comparative Demo API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
demo_state = {
    "training_complete": False,
    "ace_playbook": None,
    "current_round": 0,
    "baseline_results": [],
    "ace_results": [],
    "judge_results": []
}


# Load pre-trained playbook on startup
playbook_path = Path(__file__).parent / "pretrained_playbook.json"
if playbook_path.exists():
    try:
        demo_state["ace_playbook"] = Playbook.load_from_file(str(playbook_path))
        demo_state["training_complete"] = True
        print(f"✅ Loaded pre-trained playbook with {len(demo_state['ace_playbook'].bullets())} strategies")
    except Exception as e:
        print(f"⚠️  Failed to load playbook: {e}")


async def stream_comparative_race() -> AsyncGenerator[str, None]:
    """
    Run both baseline and ACE, then use LLM judge to compare.
    Stream results round-by-round.
    """
    try:
        if not demo_state["training_complete"] or demo_state["ace_playbook"] is None:
            yield f"data: {json.dumps({'type': 'error', 'message': 'ACE not pre-trained. Run pretrain_playbook.py first.'})}\n\n"
            return
        
        # Initialize components
        baseline_client = LiteLLMClient(
            model="claude-sonnet-4-5-20250929",
            temperature=1.0,
            max_tokens=16000
        )
        
        ace_client = LiteLLMClient(
            model="claude-sonnet-4-5-20250929",
            temperature=1.0,
            max_tokens=16000
        )
        
        baseline_generator = Generator(baseline_client)
        ace_generator = Generator(ace_client)
        judge = LLMJudge(model="claude-3-5-haiku-20241022")
        
        # Get race samples (4 samples)
        samples_raw = get_race_samples(count=4)
        samples = [
            Sample(
                question=s["code"],
                ground_truth=s["ground_truth"],
                context=f"Language: {s['language']}, Bug Type: {s['bug_type']}",
                metadata={"id": s["id"], "severity": s["severity"]}
            )
            for s in samples_raw
        ]
        
        # Send start event
        yield f"data: {json.dumps({'type': 'start', 'total': len(samples)})}\n\n"
        
        total_baseline_tokens = 0
        total_ace_tokens = 0
        total_judge_tokens = 0
        
        baseline_total_score = 0
        ace_total_score = 0
        
        # Process each round
        for round_num, (sample, sample_raw) in enumerate(zip(samples, samples_raw), 1):
            # Send round start
            yield f"data: {json.dumps({'type': 'round_start', 'round': round_num})}\n\n"
            await asyncio.sleep(0.1)
            
            # === BASELINE RUN ===
            yield f"data: {json.dumps({'type': 'baseline_start', 'round': round_num})}\n\n"
            
            baseline_start = time.time()
            baseline_output = baseline_generator.generate(
                question=f"Analyze this complex code and identify ALL bugs, edge cases, and subtle issues. Think deeply and systematically:\n\n{sample.question}",
                context="You are a junior software engineer with 1-2 years of experience. You're still learning and might miss subtle bugs or edge cases. Take your time to reason through the code carefully, considering performance, correctness, edge cases, and algorithmic complexity. Think step-by-step.",
                playbook=Playbook()  # Empty playbook
            )
            baseline_time = time.time() - baseline_start
            
            # Extract baseline tokens
            baseline_tokens = 0
            if hasattr(baseline_output, 'raw') and baseline_output.raw:
                if 'usage' in baseline_output.raw:
                    baseline_tokens = baseline_output.raw['usage'].get('total_tokens', 0)
            total_baseline_tokens += baseline_tokens
            
            yield f"data: {json.dumps({'type': 'baseline_complete', 'round': round_num, 'time': baseline_time, 'tokens': baseline_tokens})}\n\n"
            await asyncio.sleep(0.1)
            
            # === ACE RUN ===
            yield f"data: {json.dumps({'type': 'ace_start', 'round': round_num})}\n\n"
            
            ace_start = time.time()
            ace_output = ace_generator.generate(
                question=f"Analyze this complex code and identify ALL bugs, edge cases, and subtle issues. Think deeply and systematically:\n\n{sample.question}",
                context="You are a senior software engineer with 10+ years of experience and deep expertise in code review. You have mastered all the bug patterns, edge cases, and best practices documented in your playbook. Use your expert knowledge and the strategies in your playbook to systematically analyze this code. Think step-by-step about correctness, performance, edge cases, algorithmic complexity, and potential runtime issues.",
                playbook=demo_state["ace_playbook"]
            )
            ace_time = time.time() - ace_start
            
            # Extract ACE tokens
            ace_tokens = 0
            if hasattr(ace_output, 'raw') and ace_output.raw:
                if 'usage' in ace_output.raw:
                    ace_tokens = ace_output.raw['usage'].get('total_tokens', 0)
            total_ace_tokens += ace_tokens
            
            yield f"data: {json.dumps({'type': 'ace_complete', 'round': round_num, 'time': ace_time, 'tokens': ace_tokens})}\n\n"
            await asyncio.sleep(0.1)
            
            # === LLM JUDGE COMPARISON ===
            yield f"data: {json.dumps({'type': 'judging_start', 'round': round_num})}\n\n"
            
            judge_result = judge.compare_answers(
                question=sample.question,
                ground_truth=sample.ground_truth,
                baseline_answer=baseline_output.final_answer,
                ace_answer=ace_output.final_answer,
                sample_id=round_num
            )
            
            total_judge_tokens += judge_result.get("judge_tokens", 0)
            baseline_total_score += judge_result.get("baseline_score", 0)
            ace_total_score += judge_result.get("ace_score", 0)
            
            # Send round results
            round_result = {
                'type': 'round_complete',
                'round': round_num,
                'baseline': {
                    'time': baseline_time,
                    'tokens': baseline_tokens,
                    'score': judge_result.get("baseline_score", 0),
                    'strengths': judge_result.get("baseline_strengths", ""),
                    'weaknesses': judge_result.get("baseline_weaknesses", ""),
                    'answer': baseline_output.final_answer
                },
                'ace': {
                    'time': ace_time,
                    'tokens': ace_tokens,
                    'score': judge_result.get("ace_score", 0),
                    'strengths': judge_result.get("ace_strengths", ""),
                    'weaknesses': judge_result.get("ace_weaknesses", ""),
                    'answer': ace_output.final_answer
                },
                'judge': {
                    'winner': judge_result.get("winner", "tie"),
                    'reasoning': judge_result.get("reasoning", ""),
                    'tokens': judge_result.get("judge_tokens", 0)
                },
                'code_sample': sample_raw.get("code", ""),
                'ground_truth': sample_raw.get("ground_truth", "")
            }
            
            yield f"data: {json.dumps(round_result)}\n\n"
            await asyncio.sleep(0.5)
        
        # Send final summary
        num_rounds = len(samples)
        summary = {
            'type': 'final_summary',
            'baseline': {
                'total_tokens': total_baseline_tokens,
                'avg_score': baseline_total_score / num_rounds if num_rounds > 0 else 0
            },
            'ace': {
                'total_tokens': total_ace_tokens,
                'avg_score': ace_total_score / num_rounds if num_rounds > 0 else 0
            },
            'judge': {
                'total_tokens': total_judge_tokens
            }
        }
        
        yield f"data: {json.dumps(summary)}\n\n"
        
    except Exception as e:
        print(f"❌ Error in comparative race: {e}")
        import traceback
        traceback.print_exc()
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


@app.get("/api/stream/comparative")
async def stream_comparative():
    """Stream comparative race with LLM judge."""
    return StreamingResponse(
        stream_comparative_race(),
        media_type="text/event-stream"
    )


@app.get("/api/playbook/status")
async def playbook_status():
    """Check if playbook is loaded."""
    if demo_state["training_complete"] and demo_state["ace_playbook"]:
        return {
            "ready": True,
            "strategies": len(demo_state["ace_playbook"].bullets()),
            "message": "Playbook loaded and ready"
        }
    return {
        "ready": False,
        "message": "Playbook not loaded. Run pretrain_playbook.py first."
    }


@app.get("/")
async def root():
    """Serve the frontend."""
    return FileResponse("demo/frontend_comparative/index.html")


# Serve static files
app.mount("/static", StaticFiles(directory="demo/frontend_comparative"), name="static")


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Comparative Bug Hunter Demo Server...")
    print("📊 Race: 4 bug samples with LLM-as-a-judge")
    print("🔵 Baseline: Junior Engineer (no strategies)")
    print("🟢 ACE: Senior Expert (with playbook strategies)")
    print("⚖️  Judge: Claude Haiku comparing answers")
    
    if demo_state["training_complete"] and demo_state["ace_playbook"]:
        print(f"✅ Playbook loaded with {len(demo_state['ace_playbook'].bullets())} strategies")
    else:
        print("⚠️  No playbook found. Run: python demo/pretrain_playbook.py")
    
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")

