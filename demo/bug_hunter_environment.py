"""
Custom environment for evaluating bug detection quality.
"""

from ace import TaskEnvironment, EnvironmentResult
from typing import Dict, Any
import re


class BugHunterEnvironment(TaskEnvironment):
    """
    Environment for evaluating bug detection and fixing.
    
    Checks if the response:
    1. Identifies the bug correctly
    2. Explains the issue clearly
    3. Provides a fix or solution
    """
    
    def evaluate(self, sample, generator_output) -> EnvironmentResult:
        """Evaluate the bug detection response."""
        response = generator_output.final_answer.lower()
        ground_truth = sample.ground_truth.lower()
        
        # Extract key terms from ground truth
        bug_keywords = self._extract_keywords(ground_truth)
        
        # Check if response mentions key concepts
        matches = sum(1 for keyword in bug_keywords if keyword in response)
        keyword_score = matches / len(bug_keywords) if bug_keywords else 0
        
        # Check for common quality indicators
        has_explanation = any(word in response for word in ['because', 'since', 'will', 'causes', 'results'])
        has_solution = any(word in response for word in ['should', 'use', 'fix', 'change', 'replace'])
        identifies_bug = any(word in response for word in ['bug', 'error', 'issue', 'problem', 'wrong'])
        
        # Calculate quality score
        quality_indicators = [has_explanation, has_solution, identifies_bug]
        quality_score = (sum(quality_indicators) / len(quality_indicators)) * 0.4
        
        # Overall accuracy (keyword matching is 60%, quality indicators 40%)
        accuracy = (keyword_score * 0.6) + quality_score
        
        # Generate feedback
        if accuracy >= 0.8:
            feedback = "Excellent bug detection! Identified the issue and provided clear solution."
        elif accuracy >= 0.6:
            feedback = "Good detection. Identified the bug but could be more specific or provide clearer fix."
        elif accuracy >= 0.4:
            feedback = "Partial detection. Mentioned some aspects but missed key details."
        else:
            feedback = "Poor detection. Failed to identify the core bug or provide useful guidance."
        
        return EnvironmentResult(
            feedback=feedback,
            ground_truth=sample.ground_truth,
            metrics={
                "accuracy": accuracy,
                "keyword_match": keyword_score,
                "has_explanation": float(has_explanation),
                "has_solution": float(has_solution),
                "identifies_bug": float(identifies_bug),
                "quality_score": accuracy  # For compatibility with existing code
            }
        )
    
    def _extract_keywords(self, text: str) -> list:
        """Extract important keywords from ground truth."""
        # Remove common words and split
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'is', 'are', 'be'}
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 3]
        return keywords[:10]  # Top 10 keywords

