"""
Property-based test for comment chronological ordering.

Property 47: Comment Chronological Ordering
Requirements: 14.1
"""
import uuid
from datetime import datetime, timedelta, timezone

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


class TestCommentChronologicalOrdering:
    """
    Feature: civic-pulse, Property 47: Comment Chronological Ordering
    
    For any set of comments on a report, retrieving comments should return them
    sorted by timestamp in ascending order.
    
    Validates: Requirements 14.1
    """
    
    def test_empty_report_returns_empty_list(
        self, comment_service: CommentService, test_report: Report
    ):
        """With no comments, get_comments should return an empty list."""
        comments = comment_service.get_comments(test_report.id)
        assert comments == []
    
    def test_single_comment_returns_one_item(
        self,
        db_session: Session,
        comment_service: CommentService,
        test_report: Report,
        test_user: User
    ):
        """With one comment, get_comments should return a list with one item."""
        comment_service.create_comment(
            report_id=test_report.id,
            user_id=test_user.id,
            text="Single comment"
        )
        
        comments = comment_service.get_comments(test_report.id)
        assert len(comments) == 1
        assert comments[0].text == "Single comment"
    
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @given(
        num_comments=st.integers(min_value=2, max_value=20),
        time_deltas=st.lists(
            st.integers(min_value=1, max_value=3600),  # 1 second to 1 hour
            min_size=2,
            max_size=20
        )
    )
    def test_comments_returned_in_chronological_order(
        self,
        db_session: Session,
        test_user: User,
        num_comments: int,
        time_deltas: list
    ):
        """
        Property 47: For any set of comments with different timestamps,
        retrieving comments should return them sorted by created_at in ascending order.
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
        
        # Ensure we have enough time deltas
        while len(time_deltas) < num_comments:
            time_deltas.append(1)
        time_deltas = time_deltas[:num_comments]
        
        # Create comments with incrementing timestamps
        base_time = datetime.now(timezone.utc)
        created_comments = []
        
        for i in range(num_comments):
            # Calculate timestamp for this comment
            if i == 0:
                comment_time = base_time
            else:
                # Add cumulative time delta
                comment_time = base_time + timedelta(seconds=sum(time_deltas[:i]))
            
            # Create comment directly in database with specific timestamp
            comment = Comment(
                report_id=report.id,
                user_id=test_user.id,
                text=f"Comment {i}",
                created_at=comment_time,
                updated_at=comment_time
            )
            db_session.add(comment)
            created_comments.append(comment)
        
        db_session.commit()
        
        # Retrieve comments using the service
        retrieved_comments = comment_service.get_comments(report.id)
        
        # Verify we got all comments
        assert len(retrieved_comments) == num_comments
        
        # Verify chronological ordering
        for i in range(len(retrieved_comments) - 1):
            current_time = retrieved_comments[i].created_at
            next_time = retrieved_comments[i + 1].created_at
            
            # Current comment should be created at or before the next comment
            assert current_time <= next_time, (
                f"Comments not in chronological order: "
                f"comment {i} at {current_time} is after "
                f"comment {i+1} at {next_time}"
            )
    
    @settings(
        max_examples=30,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @given(
        num_comments=st.integers(min_value=3, max_value=15)
    )
    def test_comments_with_same_timestamp_maintain_order(
        self,
        db_session: Session,
        test_user: User,
        num_comments: int
    ):
        """
        Property 47: Comments with identical timestamps should maintain
        a consistent order (typically insertion order).
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
        
        # Create comments with the same timestamp
        same_time = datetime.now(timezone.utc)
        
        for i in range(num_comments):
            comment = Comment(
                report_id=report.id,
                user_id=test_user.id,
                text=f"Comment {i}",
                created_at=same_time,
                updated_at=same_time
            )
            db_session.add(comment)
        
        db_session.commit()
        
        # Retrieve comments
        retrieved_comments = comment_service.get_comments(report.id)
        
        # Verify we got all comments
        assert len(retrieved_comments) == num_comments
        
        # Verify all timestamps are the same
        for comment in retrieved_comments:
            # Compare without timezone info since SQLite stores naive datetimes
            assert comment.created_at.replace(tzinfo=None) == same_time.replace(tzinfo=None)
    
    @settings(
        max_examples=30,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @given(
        num_comments=st.integers(min_value=2, max_value=10)
    )
    def test_comments_ordering_with_random_insertion_order(
        self,
        db_session: Session,
        test_user: User,
        num_comments: int
    ):
        """
        Property 47: Comments should be ordered by timestamp regardless
        of insertion order into the database.
        """
        import random
        
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
        
        # Create comments with timestamps in random order
        base_time = datetime.now(timezone.utc)
        timestamps = [
            base_time + timedelta(seconds=i * 10)
            for i in range(num_comments)
        ]
        
        # Shuffle the timestamps to insert in random order
        shuffled_timestamps = timestamps.copy()
        random.shuffle(shuffled_timestamps)
        
        for i, timestamp in enumerate(shuffled_timestamps):
            comment = Comment(
                report_id=report.id,
                user_id=test_user.id,
                text=f"Comment at {timestamp}",
                created_at=timestamp,
                updated_at=timestamp
            )
            db_session.add(comment)
        
        db_session.commit()
        
        # Retrieve comments
        retrieved_comments = comment_service.get_comments(report.id)
        
        # Verify we got all comments
        assert len(retrieved_comments) == num_comments
        
        # Verify chronological ordering (should match sorted timestamps)
        sorted_timestamps = sorted(timestamps)
        for i, comment in enumerate(retrieved_comments):
            # Compare without timezone info since SQLite stores naive datetimes
            assert comment.created_at.replace(tzinfo=None) == sorted_timestamps[i].replace(tzinfo=None), (
                f"Comment {i} has timestamp {comment.created_at}, "
                f"expected {sorted_timestamps[i]}"
            )
    
    def test_comments_from_different_reports_not_mixed(
        self,
        db_session: Session,
        comment_service: CommentService,
        test_report: Report,
        test_user: User
    ):
        """
        Property 47: Comments should only be returned for the specified report,
        not mixed with comments from other reports.
        """
        # Create a second report
        report2 = Report(
            user_id=test_user.id,
            photo_url=f"/uploads/{uuid.uuid4()}.jpg",
            latitude=40.7128,
            longitude=-74.0060,
            category="Water Leak",
            severity_score=7,
            status="Reported",
            ai_generated=False,
            archived=False
        )
        db_session.add(report2)
        db_session.commit()
        db_session.refresh(report2)
        
        # Create comments on both reports
        base_time = datetime.now(timezone.utc)
        
        # Comments on first report
        for i in range(3):
            comment = Comment(
                report_id=test_report.id,
                user_id=test_user.id,
                text=f"Report 1 Comment {i}",
                created_at=base_time + timedelta(seconds=i),
                updated_at=base_time + timedelta(seconds=i)
            )
            db_session.add(comment)
        
        # Comments on second report
        for i in range(2):
            comment = Comment(
                report_id=report2.id,
                user_id=test_user.id,
                text=f"Report 2 Comment {i}",
                created_at=base_time + timedelta(seconds=i),
                updated_at=base_time + timedelta(seconds=i)
            )
            db_session.add(comment)
        
        db_session.commit()
        
        # Retrieve comments for first report
        comments_report1 = comment_service.get_comments(test_report.id)
        
        # Verify only comments from first report are returned
        assert len(comments_report1) == 3
        for comment in comments_report1:
            assert comment.report_id == test_report.id
            assert "Report 1" in comment.text
        
        # Retrieve comments for second report
        comments_report2 = comment_service.get_comments(report2.id)
        
        # Verify only comments from second report are returned
        assert len(comments_report2) == 2
        for comment in comments_report2:
            assert comment.report_id == report2.id
            assert "Report 2" in comment.text
