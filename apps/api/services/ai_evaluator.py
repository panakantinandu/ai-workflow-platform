from openai import OpenAI
import json
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def evaluate_ai_response(analysis: dict):

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"""
You are an AI evaluator.

Evaluate the following analysis:

{json.dumps(analysis)}

Return JSON with:
- score (0-100)
- confidence (low, medium, high)
- issues (list of problems if any)

Only return JSON.
"""
        }],
        temperature=0
    )

    content = response.choices[0].message.content

    try:
        return json.loads(content)
    except:
        return {
            "score": 0,
            "confidence": "low",
            "issues": ["Invalid evaluation response"]
        }