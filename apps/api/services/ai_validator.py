def validate_ai_response(response: dict, task_type: str):

    if task_type == "analyze_logs":
        required_fields = ["root_cause", "severity", "recommendation"]

        for field in required_fields:
            if field not in response:
                return False, f"Missing field: {field}"

        if response["severity"] not in ["low", "medium", "high", "critical"]:
            return False, "Invalid severity value"

        return True, None

    elif task_type == "generate_recommendation":
        if "recommendation" not in response:
            return False, "Missing field: recommendation"

        return True, None

    return False, f"Unknown task type: {task_type}"