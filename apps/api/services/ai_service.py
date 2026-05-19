import os
from openai import OpenAI
from .ai_validator import validate_ai_response
import json
from core.metrics import ai_requests, ai_failures,ai_invalid
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_logs_with_ai(logs: str):

    ai_requests.inc()

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
    {
        "role": "user",
        "content": f"""
You are a senior SRE engineer.

Return ONLY valid JSON in EXACT format:

{{
  "root_cause": "string",
  "severity": "low | medium | high | critical",
  "recommendation": "string"
}}

NO extra text. ONLY JSON.

Logs:
{logs}
"""
    }
],
            temperature=0.2
        )

        content = response.choices[0].message.content

        try:
            parsed = json.loads(content)
            is_valid, error_message = validate_ai_response(parsed, "analyze_logs")
            if not is_valid:
                ai_invalid.inc()
                raise ValueError(f"Invalid AI response: {error_message}")
            return parsed
        except Exception:
            ai_invalid.inc()
            raise Exception("Invalid JSON from AI")
    except Exception:
        ai_failures.inc()

        # ONLY THIS FALLBACK EXISTS
        return {
            "root_cause": "AI unavailable",
            "severity": "high",
            "recommendation": "Fallback: Check system manually"
        }


def validate_analysis_with_ai(analysis: dict):

    ai_requests.inc()

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": f"""
You are a senior SRE reviewer.

Validate this analysis:

{json.dumps(analysis)}

Return ONLY JSON:
{{
  "valid": true/false,
  "issues": "string"
}}
"""
                }
            ],
            temperature=0.1
        )

        content = response.choices[0].message.content
        return json.loads(content)

    except Exception as e:
        ai_failures.inc()
        return {
            "valid": False,
            "issues": str(e)
        }

def analyze_logs_agent(logs: str):
    ai_requests.inc()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"""
Analyze logs and return JSON:
- root_cause
- severity

Logs:
{logs}
"""
        }],
        temperature=0.2
    )

    content = response.choices[0].message.content

    return json.loads(content)

def validate_analysis_agent(data: dict):
    ai_requests.inc()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"""
Check if this analysis is valid.

Return JSON:
- valid: true/false
- reason

Analysis:
{json.dumps(data)}
"""
        }],
        temperature=0
    )

    content = response.choices[0].message.content
    return json.loads(content)


def generate_recommendation_agent(data: dict):
    ai_requests.inc()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"""
Based on this analysis, give recommendation:

{json.dumps(data)}
"""
        }],
        temperature=0.3
    )

    return response.choices[0].message.content