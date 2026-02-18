"""
Comment service for managing report comments.

Requirements: 14.1, 14.2, 14.3
"""
import uuid
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

from app.models.comment import Comment
from app.models.report import Report


class CommentService:
    """Service for managing comments on reports."""

    def __init__(self, db: Session):
        self.db = db

    def create_comment(
        self,
        report_id: uuid.UUID,
        user_id: uuid.UUID,
        text: str,
        parent_comment_id: Optional[uuid.UUID] = None,
    ) -> Comment:
        """
        Create a new comment on a report.

        Args:
            report_id: UUID of the report
            user_id: UUID of the user creating the comment
            text: Comment text content
            parent_comment_id: Optional UUID of parent comment for threading

        Returns:
            Created Comment object

        Raises:
            ValueError: If report doesn't exist or parent comment is invalid
        """
        # Verify report exists
        report = self.db.query(Report).filter(Report.id == report_id).first()
        if not report:
            raise ValueError("Report not found")

        # Verify parent comment exists and belongs to same report if provided
        if parent_comment_id:
            parent = self.db.query(Comment).filter(Comment.id == parent_comment_id).first()
            if not parent:
                raise ValueError("Parent comment not found")
            if parent.report_id != report_id:
                raise ValueError("Parent comment does not belong to this report")

        comment = Comment(
            report_id=report_id,
            user_id=user_id,
            text=text,
            parent_comment_id=parent_comment_id,
        )
        self.db.add(comment)
        self.db.commit()
        self.db.refresh(comment)
        return comment

    def get_comments(self, report_id: uuid.UUID) -> List[Comment]:
        """
        Get all comments for a report in chronological order.

        Args:
            report_id: UUID of the report

        Returns:
            List of Comment objects sorted by created_at ascending

        Requirements: 14.1 - Comments displayed in chronological order
        """
        return (
            self.db.query(Comment)
            .filter(Comment.report_id == report_id)
            .order_by(Comment.created_at.asc())
            .all()
        )

    def get_comment(self, comment_id: uuid.UUID) -> Optional[Comment]:
        """
        Get a single comment by ID.

        Args:
            comment_id: UUID of the comment

        Returns:
            Comment object or None if not found
        """
        return self.db.query(Comment).filter(Comment.id == comment_id).first()

    def build_comment_tree(self, report_id: uuid.UUID) -> List[Dict[str, Any]]:
        """
        Build a hierarchical tree structure of comments for a report.
        
        Returns comments organized as a tree where each comment can have replies.
        Top-level comments (parent_comment_id is None) are at the root level,
        and replies are nested under their parent comments.

        Args:
            report_id: UUID of the report

        Returns:
            List of comment dictionaries with nested replies structure.
            Each comment dict contains:
            - id: Comment UUID
            - report_id: Report UUID
            - user_id: User UUID
            - parent_comment_id: Parent comment UUID or None
            - text: Comment text
            - created_at: Creation timestamp
            - updated_at: Update timestamp
            - replies: List of child comment dicts (recursive structure)

        Requirements: 14.3 - Support threaded discussions
        """
        # Get all comments for the report in chronological order
        comments = self.get_comments(report_id)
        
        # Build a map of comment_id -> comment for quick lookup
        comment_map: Dict[uuid.UUID, Dict[str, Any]] = {}
        
        # Convert comments to dictionaries and initialize replies list
        for comment in comments:
            comment_map[comment.id] = {
                "id": comment.id,
                "report_id": comment.report_id,
                "user_id": comment.user_id,
                "parent_comment_id": comment.parent_comment_id,
                "text": comment.text,
                "created_at": comment.created_at,
                "updated_at": comment.updated_at,
                "replies": [],
            }
        
        # Build the tree structure
        root_comments: List[Dict[str, Any]] = []
        
        for comment in comments:
            comment_dict = comment_map[comment.id]
            
            if comment.parent_comment_id is None:
                # Top-level comment
                root_comments.append(comment_dict)
            else:
                # Reply to another comment
                parent = comment_map.get(comment.parent_comment_id)
                if parent:
                    parent["replies"].append(comment_dict)
        
        return root_comments

    def get_comment_replies(self, comment_id: uuid.UUID) -> List[Comment]:
        """
        Get all direct replies to a specific comment.

        Args:
            comment_id: UUID of the parent comment

        Returns:
            List of Comment objects that are direct replies to the specified comment,
            sorted by created_at ascending

        Requirements: 14.3 - Support threaded discussions
        """
        return (
            self.db.query(Comment)
            .filter(Comment.parent_comment_id == comment_id)
            .order_by(Comment.created_at.asc())
            .all()
        )
