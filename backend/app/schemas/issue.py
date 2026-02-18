from datetime import datetime
from pydantic import BaseModel


class IssueBase(BaseModel):
    title: str
    description: str
    category: str | None = None
    location: str | None = None


class IssueCreate(IssueBase):
    pass


class IssueOut(IssueBase):
    id: int
    status: str
    is_resolved: bool
    created_at: datetime

    class Config:
        from_attributes = True
