#!/usr/bin/env python3
"""
ACE Browser Agent (WITH ACE)

Browser automation agent with learning capabilities using ACE framework.
Compare this with baseline_browser_use.py to see ACE's value.
"""

import asyncio
import json
from typing import List, Dict
from dotenv import load_dotenv
import argparse

from browser_use import Agent, Browser, ChatOpenAI

from ace import (
    LiteLLMClient,
    Generator,
    Reflector,
    Curator,
    OnlineAdapter,
    Sample,
    TaskEnvironment,
    EnvironmentResult,
    Playbook,
)
load_dotenv()

from utils import print_history_details
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler


import os
os.environ["BROWSER_USE_LOGGING_LEVEL"] = "critical"
os.environ["ANONYMIZED_TELEMETRY"] = "false"

def _start_http_server(port: int = 8765) -> threading.Thread:
    """Start HTTP server in background thread."""
    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

    server = HTTPServer(("127.0.0.1", port), QuietHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"Started HTTP server on http://127.0.0.1:{port}")
    return f"http://127.0.0.1:{port}/form.html"






class BrowserUseEnvironment(TaskEnvironment):
    """Environment that evaluates browser automation performance."""

    def __init__(self, headless: bool = True, model: str = "gpt-4o-mini", local_port: int = None):
        self.headless = headless
        self.model = model
        if local_port:
            self.form_uri = _start_http_server(local_port)

    def evaluate(self, sample: Sample, generator_output):
        """Run browser automation and evaluate the result."""

        task = sample.context

        print("GENERATOR OUTPUT: ", generator_output)


        # Extract action plan - handle both dict and string formats
        action_plan = {}
        action_plan_source = generator_output.final_answer
        
        # If final_answer is already a dict, use it directly
        if isinstance(action_plan_source, dict):
            action_plan = action_plan_source
        # If it's a string, try to parse it as JSON
        elif isinstance(action_plan_source, str):
            try:
                action_plan = json.loads(action_plan_source)
            except json.JSONDecodeError:
                # If parsing fails, try getting from raw
                action_plan_raw = generator_output.raw.get('final_answer', '{}') if hasattr(generator_output, 'raw') else '{}'
                if isinstance(action_plan_raw, dict):
                    action_plan = action_plan_raw
                elif isinstance(action_plan_raw, str):
                    try:
                        action_plan = json.loads(action_plan_raw)
                    except json.JSONDecodeError as e:
                        print("ERROR PARSING ACTION PLAN: ", e)
                        action_plan = {}
        # Fallback: try raw if available
        elif hasattr(generator_output, 'raw'):
            action_plan_raw = generator_output.raw.get('final_answer', '{}')
            if isinstance(action_plan_raw, dict):
                action_plan = action_plan_raw
            elif isinstance(action_plan_raw, str):
                try:
                    action_plan = json.loads(action_plan_raw)
                except json.JSONDecodeError as e:
                    print("ERROR PARSING ACTION PLAN: ", e)
                    action_plan = {}

        num_steps = len(action_plan.keys())
        action_plan = "\n".join([f"{step_number}: {step_description}" for step_number, step_description in action_plan.items()])

        browser_use_prompt = f"""
        {task}

        Follow these steps:
        {action_plan}
        """

        # Run browser automation
        result = asyncio.run(self._run_browser_task(browser_use_prompt))

        print_history_details(result)


        # Success case - result is a history object
        model_outputs = result.model_outputs() if hasattr(result, "model_outputs") else None
        final_result = result.final_result() if hasattr(result, "final_result") else ""
        is_done = result.is_done() if hasattr(result, "is_done") else False
        is_successful = result.is_successful() if hasattr(result, "is_successful") else False
        has_errors = result.has_errors() if hasattr(result, "has_errors") else False
        number_of_steps = result.number_of_steps() if hasattr(result, "number_of_steps") else 0

    
      
        # Build steps text outside f-string to avoid backslash issue
        model_outputs_text = "\n".join([str(output) for output in model_outputs]) if model_outputs else "No model outputs recorded"
        done_text = "" if is_done else "not "
        successful_text = "" if is_successful else "not "
        errors_text = "" if has_errors else "no "

        feedback = f"""
        The task was {done_text}finished.
        The task was {successful_text}successful.
        The browser use agent had {errors_text}errors.
        Browser use agent took {number_of_steps} steps.

        These are the outputs of the agent while executing the task:
        {model_outputs_text}

        The final result was: {final_result}
        """

        status = "SUCCESS" if is_successful else "ERROR"
        success = is_successful
        efficient = number_of_steps <= 15  # Consider efficient if <= max_steps

        print("FEEDBACK: ", feedback)


        return EnvironmentResult(
            feedback=feedback,
            ground_truth=None,  # No ground truth available for form filling
            metrics={
                "success": success,
                "efficient": efficient,
                "steps": number_of_steps,
                "status": status,
            }
        )


    async def _run_browser_task(self, browser_use_prompt: str):
        """Run browser task without any learning."""
        
        browser = None
        try:
            # Start browser
            browser = Browser(headless=self.headless)
            await browser.start()

            # Create agent with basic task (no learning, no strategy optimization)
            llm = ChatOpenAI(model=self.model, temperature=0.0)

            agent = Agent(
                task=browser_use_prompt,
                llm=llm,
                browser=browser,
                max_actions_per_step=10,
                max_steps=10
            )

            # Run with timeout
            history = await asyncio.wait_for(agent.run(), timeout=240.0)
            return history
        except asyncio.TimeoutError:
            # Try to get steps from history if it exists
            number_of_steps = 25  # default to max_steps
            try:
                if 'history' in locals() and history is not None:
                    number_of_steps = history.number_of_steps() if hasattr(history, "number_of_steps") else 25
            except:
                pass
            return {"is_done": False, "is_successful": False, "has_errors": True, "number_of_steps": number_of_steps, "final_result": "Timeout"}
        except Exception as e:
            # Try to get steps from history if it exists
            number_of_steps = 0
            try:
                if 'history' in locals() and history is not None:
                    number_of_steps = history.number_of_steps() if hasattr(history, "number_of_steps") else 0
            except:
                pass
            return {"is_done": False, "is_successful": False, "has_errors": True, "number_of_steps": number_of_steps, "final_result": str(e)}

        finally:
            if browser:
                try:
                    await browser.stop()
                except:
                    pass


def main(task_file: str = "task1_flight_search.txt"):
    """Main function - browser automation with ACE learning.
    
    Args:
        task_file: Path to the task file containing the browser task description.
                  Defaults to "task1_flight_search.txt".
    """

    print("\n🤖 ACE Browser Agent (WITH ACE)")
    print("✨ Learning enabled - improves after each task")
    print("=" * 40)
    

    print("\n🔄 Starting browser task with learning...\n")

    # Read task from file
    with open(task_file, "r") as f:
        task_content = f.read()
    task_content = "Task:\n\n" + task_content

    results = []

    llm = LiteLLMClient(model="gpt-4o-mini", temperature=0.7)

    adapter = OnlineAdapter(
        playbook=Playbook(),
        generator=Generator(llm),
        reflector=Reflector(llm),
        curator=Curator(llm),
        max_refinement_rounds=2,
    )

    environment = BrowserUseEnvironment(
        headless=False,
        model="gpt-4o-mini",
        local_port=8765
    )

    
    question = """
    If you were a browser use agent, what would you do to fullfil the following task?

    How would your step by step action plan look like for this browser use task?
    Single steps should be atomic and self-contained.
    The action plan should be a list of steps.
    Single steps could be things like:
    - Click on a button
    - Fill out a form
    - Navigate to a website
    - Read a value from the screen
    - etc.

    Provide the plan as an overall answer in the final_answer field as a dictionary of steps, where the key is the step number and the value is the step description.
    Example: "final_answer": {
        "1": "Click on the \\"next\\" button",
        "2": "Fill out the Email field",
        "3": "Fill out the Password field",
        "4": "Click on the login button"
    }
    """


    samples = []
    for i in range(5):
        samples.append(Sample(
            question=question,
            ground_truth="SUCCESS",
            context=task_content
        ))


    results = adapter.run(samples, environment)

    # Note: Results from adapter.run are AdapterStepResult objects, not dicts
    # If you need to run an additional browser task outside the adapter,
    # you would need to create a separate standalone function or use the environment

    # Show final results
    print("=" * 40)
    print("📊 Results:")

    # Extract metrics from adapter results
    if results:
        successful = sum(1 for r in results if r.environment_result.metrics.get('success', False))
        total_steps = sum(r.environment_result.metrics.get('steps', 0) for r in results)
        avg_steps = total_steps / len(results) if results else 0

        print(f"\n✅ Success rate: {successful}/{len(results)} ({100*successful/len(results):.1f}%)")
        print(f"⚡ Average steps: {avg_steps:.1f}")
    else:
        print("\n⚠️ No results to display")
    
    print(f"✨ Learning enabled - improves after each task")

    print(f"\n💡 Compare with: python examples/browser-use/baseline_browser_use.py")
    print(f"   Baseline has no learning - same performance every time")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ACE Browser Use Agent")
    parser.add_argument("--task-file", type=str, default="task1_flight_search.txt", help="Path to the task file")
    args = parser.parse_args()  
    main(args.task_file)