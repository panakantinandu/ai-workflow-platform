from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any
from datetime import datetime
from apps.api.db.models import TaskStatus

class TaskResponse(BaseModel):
    id: int
    workflow_run_id: int
    task_type: str
    status: TaskStatus
    payload: str
    result: Optional[str] = None
    retry_count: int
    max_retries: int
    next_retry_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PaginatedTaskResponse(BaseModel):
    items: List[TaskResponse]
    total: int
    skip: int
    limit: int
