"""Session 1 baseline using Browser Use agent with GPT-4o-mini."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from browser_use import Agent, Browser, ChatOpenAI
from dotenv import load_dotenv


LOGGER = logging.getLogger("smart_form_filler.session1")

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"


def _load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _ensure_openai_key() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        LOGGER.error("OPENAI_API_KEY not found. Please set it in your environment or .env file.")
        sys.exit(1)


def _start_http_server(port: int = 8765) -> threading.Thread:
    """Start HTTP server in background thread."""
    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

    server = HTTPServer(("127.0.0.1", port), QuietHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    LOGGER.info(f"Started HTTP server on http://127.0.0.1:{port}")
    return thread


def _resolve_target_uri(config_path: Path, config: Dict[str, Any]) -> str:
    if config.get("target_form_url"):
        return str(config["target_form_url"])
    local_path = config.get("target_form_path")
    if not local_path:
        raise ValueError("Provide either target_form_url or target_form_path in config.yaml")
    form_file = (config_path.parent / local_path).resolve()
    if not form_file.exists():
        raise FileNotFoundError(f"Local form file not found: {form_file}")

    # Return localhost URL instead of file:// to avoid browser security blocks
    _start_http_server()
    return f"http://127.0.0.1:8765/{local_path}"


def _extract_json_blob(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


@dataclass
class AgentOutputs:
    steps: int = 0
    validation_events: Optional[Any] = None
    dom_hints: Optional[Any] = None
    final_status: str = "unknown"

    @classmethod
    def from_agent_summary(cls, summary: Dict[str, Any]) -> "AgentOutputs":
        return cls(
            steps=int(summary.get("steps", 0) or 0),
            validation_events=summary.get("validation_events"),
            dom_hints=summary.get("dom_hints"),
            final_status=str(summary.get("final_status", "unknown")),
        )


class BaselineRunner:
    def __init__(self, config_path: Path, payload_path: Path, headless: bool) -> None:
        self.config_path = config_path
        self.payload_path = payload_path
        self.headless = headless

        self.config = _load_yaml(config_path)
        self.payload = _load_json(payload_path)
        self.form_uri = _resolve_target_uri(config_path, self.config)

    def _build_task(self) -> str:
        payload_json = json.dumps(self.payload, indent=2)
        selectors_json = json.dumps(self.config.get("selectors", {}), indent=2)
        validation_selectors = json.dumps(self.config.get("validation_selectors", {}), indent=2)

        return f"""
URL: {self.form_uri}

Data: {payload_json}

Selectors: {selectors_json}

Instructions:
1. Navigate to URL
2. Fill: #first_name, #last_name, #email, #phone, #address1, #address2, #city, #state_region, #zip_postal, #country (select), #ship_date
3. Click #submit
4. Wait 2 seconds
5. Check .status-area for errors
6. Extract .error-message[data-error-active="true"] elements
7. Return JSON with keys: steps, final_status, validation_events, notes

STOP after step 7. Do NOT refill form. Do NOT retry.
"""

    async def run(self) -> Dict[str, Any]:
        load_dotenv()
        _ensure_openai_key()

        browser = Browser(headless=self.headless)
        await browser.start()

        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
        task = self._build_task()

        agent = Agent(
            task=task,
            llm=llm,
            browser=browser,
            max_steps=int(self.config.get("browser", {}).get("max_steps", 30)),
            context={
                "payload": self.payload,
                "selectors": self.config.get("selectors", {}),
                "validation_selectors": self.config.get("validation_selectors", {}),
            },
        )

        started_at = datetime.now(timezone.utc)
        start_perf = time.perf_counter()
        try:
            history = await asyncio.wait_for(
                agent.run(),
                timeout=float(self.config.get("browser", {}).get("timeout", 90)),
            )
        finally:
            await browser.stop()

        finished_at = datetime.now(timezone.utc)
        end_perf = time.perf_counter()

        summary: Dict[str, Any] = {}
        if history and hasattr(history, "final_result"):
            summary = _extract_json_blob(history.final_result()) or {}

        agent_outputs = AgentOutputs.from_agent_summary(summary)

        metrics: Dict[str, Any] = {
            "session": 1,
            "session_type": "baseline_without_ace",
            "form_url": self.form_uri,
            "start_time": started_at.isoformat(),
            "end_time": finished_at.isoformat(),
            "total_time_seconds": round(end_perf - start_perf, 2),
            "steps": agent_outputs.steps,
            "final_status": agent_outputs.final_status,
            "validation_error_count": len(agent_outputs.validation_events or []),
        }

        result = {
            "metadata": {
                "session": "Session 1 - Baseline",
                "description": "Browser Use agent filling raw payload (no normalization)",
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
            "metrics": metrics,
            "validation_events": agent_outputs.validation_events or [],
            "dom_hints": agent_outputs.dom_hints or {},
            "payload_used": self.payload,
            "agent_summary": summary,
        }

        return result


def _persist(result: Dict[str, Any]) -> Path:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = ARTIFACTS_DIR / f"session1_baseline_{timestamp}.json"
    with path.open("w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, ensure_ascii=False)
    return path


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run Session 1 baseline (Browser Use + GPT-4o-mini)")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    parser.add_argument("--payload", default="payload.json", help="Path to payload JSON")
    parser.add_argument("--headless", action="store_true", help="Launch the browser headlessly")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity",
    )

    args = parser.parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    runner = BaselineRunner(
        config_path=Path(args.config).resolve(),
        payload_path=Path(args.payload).resolve(),
        headless=args.headless,
    )

    try:
        result = await runner.run()
    except asyncio.TimeoutError:
        LOGGER.error("Baseline session timed out")
        sys.exit(1)
    except Exception as exc:  # pragma: no cover - defensive
        LOGGER.error("Baseline session failed: %s", exc, exc_info=True)
        sys.exit(1)

    artifact_path = _persist(result)
    LOGGER.info("Baseline artifact saved to %s", artifact_path)
    LOGGER.info(
        "Validation errors captured: %s",
        result["metrics"].get("validation_error_count", "unknown"),
    )


if __name__ == "__main__":
    asyncio.run(main())
