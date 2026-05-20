import os
import json
import logging
from openai import OpenAI
from .ai_validator import validate_ai_response
from apps.api.core.metrics import ai_requests, ai_failures, ai_invalid
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
logger = logging.getLogger(__name__)

def analyze_logs_with_ai(logs: str) -> dict:
    ai_requests.inc()
    
    logger.info(f"Sending logs to AI for analysis. Log snippet: {logs[:100]}...")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an elite Site Reliability Engineer (SRE) and AI diagnostic system. "
                        "Your task is to analyze application and infrastructure logs, identify the precise root cause, "
                        "and provide highly specific, actionable recommendations.\n\n"
                        "CRITICAL INSTRUCTIONS:\n"
                        "1. Output MUST be ONLY valid JSON.\n"
                        "2. Output MUST vary depending directly on the input logs.\n"
                        "3. PENALTY: Do NOT give generic responses (e.g., 'Scale DB connection pool') unless explicitly indicated by the logs.\n"
                        "4. PENALTY: Do NOT hallucinate metrics or services not present in the logs.\n\n"
                        "JSON FORMAT:\n"
                        "{\n"
                        "  \"root_cause\": \"Detailed, log-specific explanation of the failure.\",\n"
                        "  \"severity\": \"low | medium | high | critical\",\n"
                        "  \"recommendation\": \"Specific, actionable step to resolve the exact issue found in the logs.\"\n"
                        "}"
                    )
                },
                {
                    "role": "user",
                    "content": f"Logs to analyze:\n{logs}"
                }
            ],
            temperature=0.5,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        logger.info(f"AI Response received: {content}")

        try:
            parsed = json.loads(content)
            if not all(k in parsed for k in ["root_cause", "severity", "recommendation"]):
                raise ValueError("Missing required JSON fields")
            return parsed
        except Exception as e:
            ai_invalid.inc()
            logger.error(f"Failed to parse AI JSON: {e} | Content: {content}")
            raise Exception("Invalid JSON from AI")
            
    except Exception as e:
        ai_failures.inc()
        logger.error(f"AI Service Failure: {e}")
        return {
            "root_cause": "AI analysis service unavailable or failed.",
            "severity": "high",
            "recommendation": "Fallback: Check system health and logs manually."
        }

def validate_analysis_with_ai(analysis: dict):
    ai_requests.inc()
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": f"You are a senior SRE reviewer. Validate this analysis:\n\n{json.dumps(analysis)}\n\nReturn ONLY JSON:\n{{\n  \"valid\": true/false,\n  \"issues\": \"string\"\n}}"
                }
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        ai_failures.inc()
        return {"valid": False, "issues": str(e)}

# --- TEST CASES ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    test_cases = [
        "CPU usage spiked to 95%",
        "Database connection timeout",
        "Memory leak detected"
    ]
    
    for idx, logs in enumerate(test_cases, 1):
        print(f"\n--- TEST CASE {idx} ---")
        print(f"INPUT LOGS: {logs}")
        result = analyze_logs_with_ai(logs)
        print("OUTPUT:")
        print(json.dumps(result, indent=2))