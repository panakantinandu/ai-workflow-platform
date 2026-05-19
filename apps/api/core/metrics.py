from prometheus_client import Counter, Histogram, Gauge


# ──────────────────────────────────────────────
# AI SERVICE METRICS
# ──────────────────────────────────────────────


ai_requests = Counter(
    "ai_requests_total",
    "Total AI calls"
)

ai_failures = Counter(
    "ai_failures_total",
    "AI failures"
)

ai_invalid = Counter(
    "ai_invalid_total",
    "Invalid AI Responses"
)

ai_errors = Counter(
    "ai_errors_total",
    "AI errors by type",
    ["type"]
)

ai_evaluation_score = Histogram(
    "ai_evaluation_score",
    "AI evaluation score by type",
    ["type"]
)

ai_low_quality = Counter(
    "ai_low_quality_total",
    "Low quality AI responses"
)

# ──────────────────────────────────────────────
# THROUGHPUT
# ──────────────────────────────────────────────

tasks_processed = Counter(
    "tasks_processed_total",
    "Total number of tasks successfully processed"
)

# ──────────────────────────────────────────────
# FAILURES & DLQ
# ──────────────────────────────────────────────

task_failures = Counter(
    "task_failures_total",
    "Total number of tasks that permanently failed (sent to DLQ)"
)

dlq_tasks = Counter(
    "dlq_tasks_total",
    "Number of tasks moved to Dead Letter Queue",
    ["reason"]   # e.g. 'max_retries_exceeded', 'unknown_error'
)

# ──────────────────────────────────────────────
# RETRIES
# ──────────────────────────────────────────────

retry_count = Counter(
    "retry_count_total",
    "Number of times tasks were scheduled for retry",
    ["task_type", "attempt"]  # track which task types retry most and times
)

# ──────────────────────────────────────────────
# LATENCY
# ──────────────────────────────────────────────

task_duration = Histogram(
    "task_duration_seconds",
    "End-to-end wall-clock time to process a task",
    ["task_type", "status"],   # distinguish success vs failure latency
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

# ──────────────────────────────────────────────
# WORKERS
# ──────────────────────────────────────────────

workers_online = Gauge(
    "workers_online_total",
    "Number of worker processes currently running",
    ["worker_id"]  # supports multi-worker deployments
)

# ──────────────────────────────────────────────
# TASK STATUS  (all lowercase — matches TaskStatus enum values)
# ──────────────────────────────────────────────

task_status_counter = Counter(
    "task_status_total",
    "Number of task status transitions",
    ["status", "task_type"]  # e.g. status=queued, task_type=analyze_logs
)
