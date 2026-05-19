import os
import time
import json
from datetime import timedelta, datetime
from sqlalchemy.orm import Session
from sqlalchemy import select
from apps.api.db.models import Task, TaskStatus, DeadLetterTask
from apps.api.db.database import SessionLocal
from apps.api.core.logger import get_logger
from apps.api.services.ai_validator import validate_ai_response
# [REMOVED] from .ai_service import analyze_logs_agent, validate_analysis_agent, generate_recommendation_agent
# OpenAI dependency bypassed — mock mode active (re-enable when quota is restored)
# [REMOVED] from .ai_evaluator import evaluate_ai_response
from apps.api.core.metrics import (
    tasks_processed,
    task_failures,
    task_duration,
    dlq_tasks,
    retry_count,
    workers_online,
    task_status_counter,
    ai_invalid,
    ai_errors,
    ai_evaluation_score,
    ai_low_quality
)

logger = get_logger(__name__)

# Unique ID per worker process (useful when running multiple workers)
WORKER_ID = str(os.getpid())


# ─────────────────────────────────────────────────────────────
# FETCH
# ─────────────────────────────────────────────────────────────

def fetch_next_task(db: Session):
    """Grab the next QUEUED task that is ready to run (respects next_retry_at)."""
    now = datetime.utcnow()

    stmt = (
        select(Task)
        .where(
            Task.status == TaskStatus.QUEUED,
            (Task.next_retry_at == None) | (Task.next_retry_at <= now)
        )
        .order_by(Task.id)
        .with_for_update(skip_locked=True)
        .limit(1)
    )

    return db.execute(stmt).scalars().first()


# ─────────────────────────────────────────────────────────────
# WORKER LOOP
# ─────────────────────────────────────────────────────────────

def run_worker():
    print(f"🚀 Worker started (pid={WORKER_ID})")

    # FIX #3 — register this worker as online
    workers_online.labels(worker_id=WORKER_ID).set(1)

    try:
        while True:
            db = SessionLocal()
            try:
                db.begin()
                task = fetch_next_task(db)

                if not task:
                    db.commit()
                    time.sleep(2)
                    continue

                logger.info(
                    "Task started",
                    extra={
                        "extra_data": {
                            "event": "task_started",
                            "task_id": task.id,
                            "task_type": task.task_type,
                        }
                    }
                )

                task.status = TaskStatus.RUNNING
                # FIX #2 — status label matches TaskStatus enum: lowercase "running"
                task_status_counter.labels(
                    status=task.status.value,          # "running"
                    task_type=task.task_type
                ).inc()
                db.commit()

                execute_task(task, db)

            except Exception as e:
                db.rollback()
                logger.error(f"Worker loop error: {e}")

            finally:
                db.close()
    finally:
        # FIX #3 — mark worker offline on exit / crash
        workers_online.labels(worker_id=WORKER_ID).set(0)
        print(f"💀 Worker {WORKER_ID} stopped")


# ─────────────────────────────────────────────────────────────
# TASK EXECUTION
# ─────────────────────────────────────────────────────────────

def execute_task(task: Task, db: Session):
    start_time = time.time()

    try:
        if task.task_type == "analyze_logs":
            data = json.loads(task.payload)
            logs = data.get("logs", "")
            analysis = {
                "root_cause": "Database timeout",
                "severity": "high"
            }
            
            # [MOCK] validate_analysis_agent replaced — always passes in mock mode
            validation = {"valid": True, "reason": "mock validation — OpenAI bypassed"}
            
            # next step - evaluation
            evaluation = {
                "score": 75,
                "confidence": "high",
                "issues": []
            }
            score = evaluation.get("score", 0)

            # metrics
            ai_evaluation_score.labels(type=task.task_type).observe(score)

            # reject low quality responses
            if score < 60:
                ai_low_quality.inc()
                raise Exception(f"Low quality AI output: score={score}")

            # [MOCK] generate_recommendation_agent replaced — deterministic output
            recommendation = (
                "Increase DB connection pool size and add a circuit breaker "
                "around the DB client to prevent cascading timeouts."
            )

            result = {"analysis": analysis, "recommendation": recommendation, "evaluation": evaluation}
        elif task.task_type == "generate_recommendation":
            result = generate_recommendation(task.payload)
            is_valid, error_message = validate_ai_response(result, task.task_type)
            if not is_valid:
                raise ValueError(f"Invalid AI response: {error_message}")
        else:
            raise ValueError(f"Unknown task type: {task.task_type!r}")
        # ── SUCCESS ──────────────────────────────────────────
        duration = time.time() - start_time
        task.status = TaskStatus.COMPLETED
        task.result = json.dumps(result)

        tasks_processed.inc()

        # FIX #2 — lowercase "completed" matches enum value
        task_status_counter.labels(
            status=task.status.value,               # "completed"
            task_type=task.task_type
        ).inc()

        # FIX — latency labelled by task_type AND outcome
        task_duration.labels(
            task_type=task.task_type,
            status="completed"
        ).observe(duration)


    except Exception as e:
        duration = time.time() - start_time
        task.retry_count += 1

        error_str = str(e)

        error_type = "unknown"

        # classify error type
        if "insufficient_quota" in error_str or "429" in error_str:
            error_type = "quota"
        elif "validation" in error_str.lower():
            error_type = "validation"
        elif "timeout" in error_str.lower():
            error_type = "timeout"
        else:
            error_type = "other"

        ai_errors.labels(type=error_type).inc()
        # classify retryable vs non-retryable
        if error_type == "quota":
            is_retryable = False
        else:
            is_retryable = True

        if not is_retryable or task.retry_count >= task.max_retries:
            # ── DLQ ──────────────────────
            dlq_task = DeadLetterTask(
                original_task_id=task.id,
                task_type=task.task_type,
                payload=task.payload,
                error_message=error_str,
                retry_count=task.retry_count,
            )
            db.add(dlq_task)

            task.status = TaskStatus.FAILED
            task.result = f"Moved to DLQ: {error_str}"

            task_failures.inc()
            dlq_tasks.labels(reason="non_retryable" if not is_retryable else "max_retries").inc()

            task_status_counter.labels(
                status=task.status.value,
                task_type=task.task_type
            ).inc()

            task_duration.labels(
                task_type=task.task_type,
                status="failed"
            ).observe(duration)

            logger.error(
                "Task moved to DLQ",
                extra={"extra_data": {
                    "event": "task_dlq",
                    "task_id": task.id,
                    "error": error_str
                }}
            )

        else:
            # ── RETRY ─────────────────────
            backoff = 2 ** task.retry_count
            task.status = TaskStatus.QUEUED
            task.next_retry_at = datetime.utcnow() + timedelta(seconds=backoff)
            task.result = f"Retry {task.retry_count}/{task.max_retries}: {error_str}"

            retry_count.labels(
                task_type=task.task_type,
                attempt=str(task.retry_count)
            ).inc()

            task_status_counter.labels(
                status="queued",
                task_type=task.task_type
            ).inc()

            logger.warning(
                "Task scheduled for retry",
                extra={"extra_data": {
                    "event": "task_retry",
                    "task_id": task.id,
                    "retry_count": task.retry_count,
                    "error": error_str
                }}
            )

            print(f"🔁 Retrying task {task.id} ({task.task_type}) in {backoff}s "
                  f"[attempt {task.retry_count}/{task.max_retries}]")

    db.commit()


# ─────────────────────────────────────────────────────────────
# TASK IMPLEMENTATIONS
# ─────────────────────────────────────────────────────────────

def analyze_logs(payload: str, task_id: int):
    import random

    time.sleep(1)

    # 70 % failure rate to exercise retry/DLQ paths during development
    if random.random() < 0.7:
        raise RuntimeError("Simulated failure in analyze_logs")

    logger.info(
        "analyze_logs completed",
        extra={
            "extra_data": {
                "event": "analyze_logs_completed",
                "task_id": task_id,
                "severity": "high",
            }
        }
    )
    return {"summary": "Logs analyzed successfully", "severity": "high"}


def generate_recommendation(payload: str):
    data = json.loads(payload)
    time.sleep(2)
    return {
        "analysis": {
            "root_cause": "Service connection pool exhausted under sustained load",
            "severity": "medium",
        },
        "recommendation": (
            "Scale the DB connection pool from 5 → 20, enable TCP keep-alive, "
            "and wrap the DB client with a circuit breaker (exponential backoff, "
            "max 3 retries) to prevent cascading failures under load."
        ),
        "evaluation": {
            "score": 82,
            "confidence": "high",
            "issues": [],
        },
    }