import os
import json
import logging
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
logger = logging.getLogger(__name__)

def evaluate_ai_response(analysis: dict, logs: str) -> dict:
    """
    Evaluates an AI analysis against the original logs based on relevance,
    specificity, consistency, and recommendation quality.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # Use strong model for evaluation and critique
            messages=[{
                "role": "system",
                "content": (
                    "You are an elite QA and SRE Evaluation System.\n"
                    "Your task is to critique an AI's log analysis based on the original logs.\n\n"
                    "CRITERIA:\n"
                    "1. RELEVANCE: Does the root_cause specifically match the logs? Penalize generic answers.\n"
                    "2. SPECIFICITY: Is the explanation detailed? Penalize vague 'system issues'.\n"
                    "3. CONSISTENCY: Does severity align with the logs (e.g., 95% CPU spike is NOT low).\n"
                    "4. RECOMMENDATION QUALITY: Is the recommendation actionable? Penalize 'check logs' or 'restart server' unless justified.\n\n"
                    "You MUST output exactly in the following JSON format:\n"
                    "{\n"
                    "  \"score\": <number 0-100>,\n"
                    "  \"confidence\": \"low\" | \"medium\" | \"high\",\n"
                    "  \"issues\": [\"list of specific problems or 'none'\"],\n"
                    "  \"reasoning\": \"detailed explanation of why this score was given\"\n"
                    "}"
                )
            },
            {
                "role": "user",
                "content": f"LOGS:\n{logs}\n\nAI ANALYSIS TO EVALUATE:\n{json.dumps(analysis, indent=2)}"
            }],
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        result = json.loads(content)
        
        return {
            "score": result.get("score", 0),
            "confidence": result.get("confidence", "low"),
            "issues": result.get("issues", []),
            "reasoning": result.get("reasoning", "No reasoning provided")
        }
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        return {
            "score": 0,
            "confidence": "low",
            "issues": ["Failed to evaluate AI response", str(e)],
            "reasoning": "Evaluation service encountered an error."
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    test_cases = [
        {
            "logs": "CPU usage spiked to 95%",
            "analysis": {
                "root_cause": "A heavy process is consuming excessive CPU cycles leading to a 95% spike.",
                "severity": "high",
                "recommendation": "Identify the specific heavy process using tools like htop or top, and terminate or throttle it."
            }
        },
        {
            "logs": "Memory leak detected",
            "analysis": {
                "root_cause": "System issue.",
                "severity": "low",
                "recommendation": "Check the logs."
            }
        },
        {
            "logs": "Database timeout",
            "analysis": {
                "root_cause": "Network latency causing API failure",
                "severity": "medium",
                "recommendation": "Add a load balancer"
            }
        }
    ]

    for idx, tc in enumerate(test_cases, 1):
        print(f"\n--- TEST CASE {idx} ---")
        print(f"LOGS: {tc['logs']}")
        print(f"ANALYSIS: {json.dumps(tc['analysis'])}")
        
        evaluation = evaluate_ai_response(tc['analysis'], tc['logs'])
        print("EVALUATION:")
        print(json.dumps(evaluation, indent=2))