from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.schemas.issue import IssueCreate, IssueOut
from app.services.issues import create_issue, list_issues

router = APIRouter(prefix="/issues", tags=["Issues"])


@router.get("/", response_model=list[IssueOut])
def get_issues(db: Session = Depends(get_db)):
    return list_issues(db)


@router.post("/", response_model=IssueOut, status_code=status.HTTP_201_CREATED)
def post_issue(payload: IssueCreate, db: Session = Depends(get_db)):
    issue = create_issue(db, payload)
    if not issue:
        raise HTTPException(status_code=400, detail="Unable to create issue")
    return issue
