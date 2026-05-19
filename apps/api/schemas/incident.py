from pydantic import BaseModel


class IncidentCreate(BaseModel):

    title: str
    severity: str
    source: str
    logs: str