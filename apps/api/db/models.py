from sqlalchemy import String, Integer, Text, ForeignKey, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum

from .base import Base

# -----------------------------
# ENUMS (STRICT STATE CONTROL)
# -----------------------------

class WorkflowStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class TaskStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


# -----------------------------
# INCIDENT
# -----------------------------

class Incident(Base):

    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    title: Mapped[str] = mapped_column(String(255))

    severity: Mapped[str] = mapped_column(String(50))

    source: Mapped[str] = mapped_column(String(255))

    logs: Mapped[str] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    # relationship
    workflow_runs: Mapped[list["WorkflowRun"]] = relationship(
        back_populates="incident"
    )


# -----------------------------
# WORKFLOW (TEMPLATE)
# -----------------------------

class Workflow(Base):

    __tablename__ = "workflows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    # relationship
    runs: Mapped[list["WorkflowRun"]] = relationship(
        back_populates="workflow"
    )


# -----------------------------
# WORKFLOW RUN (IMPORTANT)
# -----------------------------

class WorkflowRun(Base):

    __tablename__ = "workflow_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    workflow_id: Mapped[int] = mapped_column(
        ForeignKey("workflows.id")
    )

    incident_id: Mapped[int] = mapped_column(
        ForeignKey("incidents.id")
    )

    status: Mapped[WorkflowStatus] = mapped_column(
        Enum(WorkflowStatus),
        default=WorkflowStatus.PENDING
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    finished_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True
    )

    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    # relationships
    workflow: Mapped["Workflow"] = relationship(
        back_populates="runs"
    )

    incident: Mapped["Incident"] = relationship(
        back_populates="workflow_runs"
    )

    tasks: Mapped[list["Task"]] = relationship(
        back_populates="workflow_run"
    )


# -----------------------------
# TASK (CORE EXECUTION UNIT)
# -----------------------------

class Task(Base):

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    workflow_run_id: Mapped[int] = mapped_column(
        ForeignKey("workflow_runs.id")
    )

    task_type: Mapped[str] = mapped_column(String(100))

    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus),
        default=TaskStatus.QUEUED
    )

    payload: Mapped[str] = mapped_column(Text)

    result: Mapped[str] = mapped_column(Text, nullable=True)

    # ADD THESE 3 FIELDS
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    max_retries: Mapped[int] = mapped_column(Integer, default=3)

    next_retry_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    workflow_run: Mapped["WorkflowRun"] = relationship(
        back_populates="tasks"
    )


# -----------------------------
# DEAD LETTER QUEUE (DLQ)
# -----------------------------

class DeadLetterTask(Base):

    __tablename__ = "dead_letter_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    original_task_id: Mapped[int] = mapped_column(Integer)

    task_type: Mapped[str] = mapped_column(String(100))

    payload: Mapped[str] = mapped_column(Text)

    error_message: Mapped[str] = mapped_column(Text)

    retry_count: Mapped[int] = mapped_column(Integer)

    failed_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )