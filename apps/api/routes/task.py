from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.db.models import Task, TaskStatus, WorkflowStatus
from apps.api.db.deps import get_db

from datetime import datetime

router = APIRouter()


@router.get("/tasks/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)

    if not task:
        return {"error": "Task not found"}

    return task

@router.put("/tasks/{task_id}/status")
def update_task_status(
    task_id: int,
    status: TaskStatus,   # enforce enum
    result: str = None,
    db: Session = Depends(get_db)
):
    task = db.get(Task, task_id)

    if not task:
        return {"error": "Task not found"}

    task.status = status

    if result:
        task.result = result

    db.commit()

    # UPDATE WORKFLOW RUN
    run = task.workflow_run

    if status == TaskStatus.COMPLETED:
        all_tasks_done = all(
            t.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]
            for t in run.tasks
        )
        if all_tasks_done:
            run.status = WorkflowStatus.COMPLETED
            run.finished_at = datetime.utcnow()

    elif status == TaskStatus.FAILED:
        run.status = WorkflowStatus.FAILED
        run.finished_at = datetime.utcnow()

    db.commit()

    return {"status": "updated", "task_id": task.id}