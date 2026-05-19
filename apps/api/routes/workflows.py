from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.db.models import Workflow, WorkflowRun, Incident
from apps.api.db.deps import get_db
from apps.api.schemas.workflow import WorkflowCreate
from apps.api.db.models import Task, TaskStatus, WorkflowStatus
from datetime import datetime
import json

router = APIRouter()


@router.post("/workflows")
def create_workflow(
    payload: WorkflowCreate,
    db: Session = Depends(get_db)
):
    workflow = Workflow(name=payload.name)

    db.add(workflow)
    db.commit()
    db.refresh(workflow)

    return workflow

@router.post("/workflows/{workflow_id}/run/{incident_id}")
def run_workflow(
    workflow_id: int,
    incident_id: int,
    db: Session = Depends(get_db)
):
    workflow = db.get(Workflow, workflow_id)
    incident = db.get(Incident, incident_id)

    if not workflow or not incident:
        return {"error": "Invalid workflow or incident"}

    run = WorkflowRun(
        workflow_id=workflow.id,
        incident_id=incident.id,
        status=WorkflowStatus.RUNNING
    )

    db.add(run)
    db.commit()
    db.refresh(run)

     # CREATE TASKS (THIS IS YOUR ENGINE)
    tasks = [
        Task(
            workflow_run_id=run.id,
            task_type="analyze_logs",
            status=TaskStatus.QUEUED,
            payload=json.dumps({"logs": incident.logs})
        ),
        Task(
            workflow_run_id=run.id,
            task_type="generate_recommendation",
            status=TaskStatus.QUEUED,
            payload=json.dumps({"incident_id": incident.id})
        )
    ]

    db.add_all(tasks)
    db.commit()

    return {"run": run.id, "tasks_created": len(tasks)}