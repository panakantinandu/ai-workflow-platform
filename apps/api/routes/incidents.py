from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.db.models import Incident
from apps.api.db.deps import get_db
from apps.api.schemas.incident import IncidentCreate

router = APIRouter()


@router.post("/incidents")
def create_incident(
    payload: IncidentCreate,
    db: Session = Depends(get_db)
):

    incident = Incident(
        title=payload.title,
        severity=payload.severity,
        source=payload.source,
        logs=payload.logs
    )

    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident