"""
Property-based test for comment data persistence.

Property 48: Comment Data Persistence
Requirements: 14.2
"""
import uuid
from datetime import datetime, timezone

import pytest
from hypothesis import given, settings, strategies as st, HealthCheck
from sqlalchemy.orm import Session

from app.models.comment import Comment
from app.models.report import Report
from app.models.user import User
from app.services.comment_service import CommentService


@pytest.fixture
def test_user(db_session: Session):
    """Create a test user."""
    user = User(
        email=f"test_{uuid.uuid4()}@example.com",
        password_hash="hashed",
        phone="+1234567890",
        role="user",
        email_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_report(db_session: Session, test_user: User):
    """Create a test report."""
    report = Report(
        user_id=test_user.id,
        photo_url=f"/uploads/{uuid.uuid4()}.jpg",
        latitude=40.7128,
        longitude=-74.0060,
        category="Pothole",
        severity_score=5,
        status="Reported",
        ai_generated=False,
        archived=False
    )
    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)
    return report


@pytest.fixture
def comment_service(db_session: Session):
    """Create a CommentService instance."""
    return CommentService(db_session)


class TestCommentDataPersistence:
    """
    Feature: civic-pulse, Property 48: Comment Data Persistence
    
    For any valid comment (report ID, user ID, text, optional parent comment ID),
    storing and retrieving the comment should return equivalent data.
    
    Validates: Requirements 14.2
    """
    
    def test_simple_comment_persistence(
        self,
        comment_service: CommentService,
        test_report: Report,
        test_user: User
    ):
        """Test that a simple comment can be stored and retrieved with equivalent data."""
        # Create a comment
        created_comment = comment_service.create_comment(
            report_id=test_report.id,
            user_id=test_user.id,
            text="This is a test comment"
        )
        
        # Retrieve the comment
        retrieved_comment = comment_service.get_comment(created_comment.id)
        
        # Verify data equivalence
        assert retrieved_comment is not None
        assert retrieved_comment.id == created_comment.id
        assert retrieved_comment.report_id == created_comment.report_id
        assert retrieved_comment.user_id == created_comment.user_id
        assert retrieved_comment.text == created_comment.text
        assert retrieved_comment.parent_comment_id == created_comment.parent_comment_id
        assert retrieved_comment.created_at == created_comment.created_at
        assert retrieved_comment.updated_at == created_comment.updated_at
    
    @settings(
        max_examples=100,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @given(
        comment_text=st.text(min_size=1, max_size=1000)
    )
    def test_comment_text_persistence(
        self,
        db_session: Session,
        test_user: User,
        comment_text: str
    ):
        """
        Property 48: For any valid comment text, storing and retrieving
        the comment should preserve the exact text content.
        """
        # Create a fresh report for this test iteration
        report = Report(
            user_id=test_user.id,
            photo_url=f"/uploads/{uuid.uuid4()}.jpg",
            latitude=40.7128,
            longitude=-74.0060,
            category="Pothole",
            severity_score=5,
            status="Reported",
            ai_generated=False,
            archived=False
        )
        db_session.add(report)
        db_session.commit()
        db_session.refresh(report)
        
        # Create a fresh service for this test iteration
        comment_service = CommentService(db_session)
        
        # Create comment with generated text
        created_comment = comment_service.create_comment(
            report_id=report.id,
            user_id=test_user.id,
            text=comment_text
        )
        
        # Retrieve the comment
        retrieved_comment = comment_service.get_comment(created_comment.id)
        
        # Verify text is preserved exactly
        assert retrieved_comment is not None
        assert retrieved_comment.text == comment_text
        assert retrieved_comment.text == created_comment.text
    
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @given(
        comment_text=st.text(min_size=1, max_size=500)
    )
    def test_comment_with_parent_persistence(
        self,
        db_session: Session,
        test_user: User,
        comment_text: str
    ):
        """
        Property 48: For any comment with a parent comment ID,
        storing and retrieving should preserve the parent-child relationship.
        """
        # Create a fresh report for this test iteration
        report = Report(
            user_id=test_user.id,
            photo_url=f"/uploads/{uuid.uuid4()}.jpg",
            latitude=40.7128,
            longitude=-74.0060,
            category="Pothole",
            severity_score=5,
            status="Reported",
            ai_generated=False,
            archived=False
        )
        db_session.add(report)
        db_session.commit()
        db_session.refresh(report)
        
        # Create a fresh service for this test iteration
        comment_service = CommentService(db_session)
        
        # Create parent comment
        parent_comment = comment_service.create_comment(
            report_id=report.id,
            user_id=test_user.id,
            text="Parent comment"
        )
        
        # Create child comment with generated text
        child_comment = comment_service.create_comment(
            report_id=report.id,
            user_id=test_user.id,
            text=comment_text,
            parent_comment_id=parent_comment.id
        )
        
        # Retrieve the child comment
        retrieved_comment = comment_service.get_comment(child_comment.id)
        
        # Verify all data is preserved
        assert retrieved_comment is not None
        assert retrieved_comment.id == child_comment.id
        assert retrieved_comment.report_id == child_comment.report_id
        assert retrieved_comment.user_id == child_comment.user_id
        assert retrieved_comment.text == comment_text
        assert retrieved_comment.parent_comment_id == parent_comment.id
        assert retrieved_comment.parent_comment_id == child_comment.parent_comment_id
    
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @given(
        num_comments=st.integers(min_value=1, max_value=10)
    )
    def test_multiple_comments_persistence(
        self,
        db_session: Session,
        test_user: User,
        num_comments: int
    ):
        """
        Property 48: For any number of comments on a report,
        each comment should be independently stored and retrievable
        with equivalent data.
        """
        # Create a fresh report for this test iteration
        report = Report(
            user_id=test_user.id,
            photo_url=f"/uploads/{uuid.uuid4()}.jpg",
            latitude=40.7128,
            longitude=-74.0060,
            category="Pothole",
            severity_score=5,
            status="Reported",
            ai_generated=False,
            archived=False
        )
        db_session.add(report)
        db_session.commit()
        db_session.refresh(report)
        
        # Create a fresh service for this test iteration
        comment_service = CommentService(db_session)
        
        # Create multiple comments
        created_comments = []
        for i in range(num_comments):
            comment = comment_service.create_comment(
                report_id=report.id,
                user_id=test_user.id,
                text=f"Comment number {i}"
            )
            created_comments.append(comment)
        
        # Retrieve each comment and verify data equivalence
        for created_comment in created_comments:
            retrieved_comment = comment_service.get_comment(created_comment.id)
            
            assert retrieved_comment is not None
            assert retrieved_comment.id == created_comment.id
            assert retrieved_comment.report_id == created_comment.report_id
            assert retrieved_comment.user_id == created_comment.user_id
            assert retrieved_comment.text == created_comment.text
            assert retrieved_comment.parent_comment_id == created_comment.parent_comment_id
    
    def test_comment_timestamps_preserved(
        self,
        comment_service: CommentService,
        test_report: Report,
        test_user: User
    ):
        """
        Property 48: Comment timestamps (created_at, updated_at)
        should be preserved during storage and retrieval.
        """
        # Create a comment
        created_comment = comment_service.create_comment(
            report_id=test_report.id,
            user_id=test_user.id,
            text="Test comment with timestamps"
        )
        
        # Store the original timestamps
        original_created_at = created_comment.created_at
        original_updated_at = created_comment.updated_at
        
        # Retrieve the comment
        retrieved_comment = comment_service.get_comment(created_comment.id)
        
        # Verify timestamps are preserved
        assert retrieved_comment is not None
        assert retrieved_comment.created_at == original_created_at
        assert retrieved_comment.updated_at == original_updated_at
    
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @given(
        comment_text=st.text(
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd', 'P', 'Zs'),
                min_codepoint=32,
                max_codepoint=126
            ),
            min_size=1,
            max_size=500
        )
    )
    def test_comment_special_characters_persistence(
        self,
        db_session: Session,
        test_user: User,
        comment_text: str
    ):
        """
        Property 48: Comments with special characters, punctuation,
        and various Unicode characters should be stored and retrieved
        without data loss or corruption.
        """
        # Create a fresh report for this test iteration
        report = Report(
            user_id=test_user.id,
            photo_url=f"/uploads/{uuid.uuid4()}.jpg",
            latitude=40.7128,
            longitude=-74.0060,
            category="Pothole",
            severity_score=5,
            status="Reported",
            ai_generated=False,
            archived=False
        )
        db_session.add(report)
        db_session.commit()
        db_session.refresh(report)
        
        # Create a fresh service for this test iteration
        comment_service = CommentService(db_session)
        
        # Create comment with special characters
        created_comment = comment_service.create_comment(
            report_id=report.id,
            user_id=test_user.id,
            text=comment_text
        )
        
        # Retrieve the comment
        retrieved_comment = comment_service.get_comment(created_comment.id)
        
        # Verify text is preserved exactly, including special characters
        assert retrieved_comment is not None
        assert retrieved_comment.text == comment_text
        assert len(retrieved_comment.text) == len(comment_text)
    
    def test_comment_retrieval_via_report_comments(
        self,
        comment_service: CommentService,
        test_report: Report,
        test_user: User
    ):
        """
        Property 48: Comments should be retrievable both individually
        and as part of a report's comment list, with equivalent data.
        """
        # Create a comment
        created_comment = comment_service.create_comment(
            report_id=test_report.id,
            user_id=test_user.id,
            text="Test comment for dual retrieval"
        )
        
        # Retrieve individually
        retrieved_individual = comment_service.get_comment(created_comment.id)
        
        # Retrieve as part of report comments
        report_comments = comment_service.get_comments(test_report.id)
        
        # Find the comment in the report comments list
        retrieved_from_list = next(
            (c for c in report_comments if c.id == created_comment.id),
            None
        )
        
        # Verify both retrieval methods return equivalent data
        assert retrieved_individual is not None
        assert retrieved_from_list is not None
        assert retrieved_individual.id == retrieved_from_list.id
        assert retrieved_individual.text == retrieved_from_list.text
        assert retrieved_individual.report_id == retrieved_from_list.report_id
        assert retrieved_individual.user_id == retrieved_from_list.user_id
        assert retrieved_individual.parent_comment_id == retrieved_from_list.parent_comment_id
    
    def test_comment_null_parent_persistence(
        self,
        comment_service: CommentService,
        test_report: Report,
        test_user: User
    ):
        """
        Property 48: Comments without a parent (parent_comment_id = None)
        should have this null value preserved during storage and retrieval.
        """
        # Create a comment without a parent
        created_comment = comment_service.create_comment(
            report_id=test_report.id,
            user_id=test_user.id,
            text="Top-level comment",
            parent_comment_id=None
        )
        
        # Retrieve the comment
        retrieved_comment = comment_service.get_comment(created_comment.id)
        
        # Verify parent_comment_id is None
        assert retrieved_comment is not None
        assert retrieved_comment.parent_comment_id is None
        assert created_comment.parent_comment_id is None
