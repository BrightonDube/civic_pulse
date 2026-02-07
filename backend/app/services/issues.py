from sqlalchemy.orm import Session

from app.models.issue import Issue
from app.schemas.issue import IssueCreate


def list_issues(db: Session) -> list[Issue]:
    return db.query(Issue).order_by(Issue.created_at.desc()).all()


def create_issue(db: Session, payload: IssueCreate) -> Issue:
    issue = Issue(
        title=payload.title,
        description=payload.description,
        category=payload.category,
        location=payload.location,
    )
    db.add(issue)
    db.commit()
    db.refresh(issue)
    return issue
