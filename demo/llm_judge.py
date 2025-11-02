"""
LLM-as-a-Judge for comparing code review quality.

Uses an LLM to compare baseline vs ACE answers and provide quality scores.
"""

from ace.llm_providers import LiteLLMClient
from typing import Dict, Any
import json
import re


class LLMJudge:
    """LLM-based judge for comparing code review quality."""
    
    def __init__(self, model: str = "claude-3-5-haiku-20241022"):
        """
        Initialize LLM judge.
        
        Args:
            model: Model to use for judging (default: Claude Haiku for speed/cost)
        """
        self.client = LiteLLMClient(
            model=model,
            temperature=0.0,  # Deterministic judging
            max_tokens=2000
        )
        self.model = model
    
    def compare_answers(
        self,
        question: str,
        ground_truth: str,
        baseline_answer: str,
        ace_answer: str,
        sample_id: int
    ) -> Dict[str, Any]:
        """
        Compare baseline and ACE answers using LLM as judge.
        
        Args:
            question: The code to analyze
            ground_truth: Expected bug description
            baseline_answer: Baseline LLM's answer
            ace_answer: ACE's answer
            sample_id: Sample number
            
        Returns:
            Dictionary with scores and reasoning
        """
        
        prompt = f"""You are an expert code reviewer evaluating two bug analysis responses.

**CODE TO ANALYZE:**
```python
{question}
```

**GROUND TRUTH (What the bugs actually are):**
{ground_truth}

**BASELINE ANSWER (Junior Engineer):**
{baseline_answer}

**ACE ANSWER (Senior Expert with Playbook):**
{ace_answer}

---

**YOUR TASK:**
Compare both answers against the ground truth and evaluate their quality on these criteria:

1. **Correctness (40%)**: Does it identify the actual bugs from ground truth?
2. **Completeness (30%)**: Does it catch ALL the bugs, including edge cases?
3. **Explanation Quality (20%)**: Are explanations clear, accurate, and insightful?
4. **Solution Quality (10%)**: Are the proposed fixes correct and practical?

**OUTPUT FORMAT (JSON):**
```json
{{
  "baseline_score": <0-100 integer>,
  "ace_score": <0-100 integer>,
  "baseline_strengths": "<brief bullet points>",
  "baseline_weaknesses": "<brief bullet points>",
  "ace_strengths": "<brief bullet points>",
  "ace_weaknesses": "<brief bullet points>",
  "winner": "baseline|ace|tie",
  "reasoning": "<2-3 sentences explaining the verdict>"
}}
```

Be objective and fair. Focus on which answer better identifies and explains the actual bugs from ground truth.
"""

        try:
            # Call judge LLM
            response = self.client.completion(
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.choices[0].message.content
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                # Fallback if JSON extraction fails
                result = {
                    "baseline_score": 50,
                    "ace_score": 50,
                    "baseline_strengths": "Unable to parse",
                    "baseline_weaknesses": "Unable to parse",
                    "ace_strengths": "Unable to parse",
                    "ace_weaknesses": "Unable to parse",
                    "winner": "tie",
                    "reasoning": "Failed to parse judge response"
                }
            
            # Extract token usage
            tokens_used = 0
            if hasattr(response, 'usage'):
                tokens_used = response.usage.total_tokens
            
            result["judge_tokens"] = tokens_used
            result["sample_id"] = sample_id
            
            return result
            
        except Exception as e:
            print(f"⚠️  LLM Judge error: {e}")
            # Return neutral scores on error
            return {
                "baseline_score": 50,
                "ace_score": 50,
                "baseline_strengths": "Error during judging",
                "baseline_weaknesses": "Error during judging",
                "ace_strengths": "Error during judging",
                "ace_weaknesses": "Error during judging",
                "winner": "tie",
                "reasoning": f"Judge error: {str(e)}",
                "judge_tokens": 0,
                "sample_id": sample_id
            }

