"""
Tests for comment functionality.

Requirements: 14.1, 14.2, 14.3
"""
import uuid
import pytest
from app.models import User, Report, Comment
from app.services.comment_service import CommentService


def test_create_comment(db_session):
    """Test creating a comment on a report."""
    # Create user and report
    user = User(email="test@example.com", phone="1234567890")
    user.set_password("password123")
    db_session.add(user)
    db_session.flush()  # Flush to get user.id
    
    report = Report(
        user_id=user.id,
        photo_url="http://example.com/photo.jpg",
        latitude=40.0,
        longitude=-111.0,
        category="Pothole",
        severity_score=5,
    )
    db_session.add(report)
    db_session.commit()
    
    # Create comment
    service = CommentService(db_session)
    comment = service.create_comment(
        report_id=report.id,
        user_id=user.id,
        text="This is a test comment",
    )
    
    assert comment.id is not None
    assert comment.report_id == report.id
    assert comment.user_id == user.id
    assert comment.text == "This is a test comment"
    assert comment.parent_comment_id is None
    assert comment.created_at is not None


def test_create_threaded_comment(db_session):
    """Test creating a threaded reply to a comment. Requirements: 14.3"""
    # Create user and report
    user = User(email="test@example.com", phone="1234567890")
    user.set_password("password123")
    db_session.add(user)
    db_session.flush()  # Flush to get user.id
    
    report = Report(
        user_id=user.id,
        photo_url="http://example.com/photo.jpg",
        latitude=40.0,
        longitude=-111.0,
        category="Pothole",
        severity_score=5,
    )
    db_session.add(report)
    db_session.commit()
    
    # Create parent comment
    service = CommentService(db_session)
    parent_comment = service.create_comment(
        report_id=report.id,
        user_id=user.id,
        text="Parent comment",
    )
    
    # Create reply
    reply = service.create_comment(
        report_id=report.id,
        user_id=user.id,
        text="Reply to parent",
        parent_comment_id=parent_comment.id,
    )
    
    assert reply.parent_comment_id == parent_comment.id
    assert reply.report_id == report.id


def test_get_comments_chronological_order(db_session):
    """Test that comments are returned in chronological order. Requirements: 14.1"""
    # Create user and report
    user = User(email="test@example.com", phone="1234567890")
    user.set_password("password123")
    db_session.add(user)
    db_session.flush()  # Flush to get user.id
    
    report = Report(
        user_id=user.id,
        photo_url="http://example.com/photo.jpg",
        latitude=40.0,
        longitude=-111.0,
        category="Pothole",
        severity_score=5,
    )
    db_session.add(report)
    db_session.commit()
    
    # Create multiple comments
    service = CommentService(db_session)
    comment1 = service.create_comment(report.id, user.id, "First comment")
    comment2 = service.create_comment(report.id, user.id, "Second comment")
    comment3 = service.create_comment(report.id, user.id, "Third comment")
    
    # Get comments
    comments = service.get_comments(report.id)
    
    assert len(comments) == 3
    assert comments[0].id == comment1.id
    assert comments[1].id == comment2.id
    assert comments[2].id == comment3.id
    # Verify chronological order
    assert comments[0].created_at <= comments[1].created_at
    assert comments[1].created_at <= comments[2].created_at


def test_create_comment_invalid_report(db_session):
    """Test that creating a comment on non-existent report fails."""
    user = User(email="test@example.com", phone="1234567890")
    user.set_password("password123")
    db_session.add(user)
    db_session.commit()
    
    service = CommentService(db_session)
    with pytest.raises(ValueError, match="Report not found"):
        service.create_comment(
            report_id=uuid.uuid4(),
            user_id=user.id,
            text="Comment on non-existent report",
        )


def test_create_comment_invalid_parent(db_session):
    """Test that creating a comment with invalid parent fails."""
    user = User(email="test@example.com", phone="1234567890")
    user.set_password("password123")
    db_session.add(user)
    db_session.flush()  # Flush to get user.id
    
    report = Report(
        user_id=user.id,
        photo_url="http://example.com/photo.jpg",
        latitude=40.0,
        longitude=-111.0,
        category="Pothole",
        severity_score=5,
    )
    db_session.add(report)
    db_session.commit()
    
    service = CommentService(db_session)
    with pytest.raises(ValueError, match="Parent comment not found"):
        service.create_comment(
            report_id=report.id,
            user_id=user.id,
            text="Reply to non-existent comment",
            parent_comment_id=uuid.uuid4(),
        )


# Note: API endpoint test removed - would require test image file
# The endpoints can be tested manually or with integration tests


def test_build_comment_tree_simple(db_session):
    """Test building a simple comment tree with top-level comments only."""
    # Create user and report
    user = User(email="test@example.com", phone="1234567890")
    user.set_password("password123")
    db_session.add(user)
    db_session.flush()
    
    report = Report(
        user_id=user.id,
        photo_url="http://example.com/photo.jpg",
        latitude=40.0,
        longitude=-111.0,
        category="Pothole",
        severity_score=5,
    )
    db_session.add(report)
    db_session.commit()
    
    # Create top-level comments
    service = CommentService(db_session)
    comment1 = service.create_comment(report.id, user.id, "First comment")
    comment2 = service.create_comment(report.id, user.id, "Second comment")
    
    # Build tree
    tree = service.build_comment_tree(report.id)
    
    assert len(tree) == 2
    assert tree[0]["id"] == comment1.id
    assert tree[0]["text"] == "First comment"
    assert tree[0]["replies"] == []
    assert tree[1]["id"] == comment2.id
    assert tree[1]["text"] == "Second comment"
    assert tree[1]["replies"] == []


def test_build_comment_tree_with_replies(db_session):
    """Test building a comment tree with nested replies. Requirements: 14.3"""
    # Create user and report
    user = User(email="test@example.com", phone="1234567890")
    user.set_password("password123")
    db_session.add(user)
    db_session.flush()
    
    report = Report(
        user_id=user.id,
        photo_url="http://example.com/photo.jpg",
        latitude=40.0,
        longitude=-111.0,
        category="Pothole",
        severity_score=5,
    )
    db_session.add(report)
    db_session.commit()
    
    # Create comment hierarchy
    service = CommentService(db_session)
    parent = service.create_comment(report.id, user.id, "Parent comment")
    reply1 = service.create_comment(report.id, user.id, "Reply 1", parent.id)
    reply2 = service.create_comment(report.id, user.id, "Reply 2", parent.id)
    nested_reply = service.create_comment(report.id, user.id, "Nested reply", reply1.id)
    
    # Build tree
    tree = service.build_comment_tree(report.id)
    
    # Verify structure
    assert len(tree) == 1  # One top-level comment
    assert tree[0]["id"] == parent.id
    assert tree[0]["text"] == "Parent comment"
    assert len(tree[0]["replies"]) == 2  # Two direct replies
    
    # Check first reply
    assert tree[0]["replies"][0]["id"] == reply1.id
    assert tree[0]["replies"][0]["text"] == "Reply 1"
    assert len(tree[0]["replies"][0]["replies"]) == 1  # One nested reply
    assert tree[0]["replies"][0]["replies"][0]["id"] == nested_reply.id
    assert tree[0]["replies"][0]["replies"][0]["text"] == "Nested reply"
    
    # Check second reply
    assert tree[0]["replies"][1]["id"] == reply2.id
    assert tree[0]["replies"][1]["text"] == "Reply 2"
    assert len(tree[0]["replies"][1]["replies"]) == 0  # No nested replies


def test_build_comment_tree_mixed(db_session):
    """Test building a comment tree with both top-level and nested comments."""
    # Create user and report
    user = User(email="test@example.com", phone="1234567890")
    user.set_password("password123")
    db_session.add(user)
    db_session.flush()
    
    report = Report(
        user_id=user.id,
        photo_url="http://example.com/photo.jpg",
        latitude=40.0,
        longitude=-111.0,
        category="Pothole",
        severity_score=5,
    )
    db_session.add(report)
    db_session.commit()
    
    # Create mixed hierarchy
    service = CommentService(db_session)
    top1 = service.create_comment(report.id, user.id, "Top comment 1")
    top2 = service.create_comment(report.id, user.id, "Top comment 2")
    reply_to_top1 = service.create_comment(report.id, user.id, "Reply to top 1", top1.id)
    
    # Build tree
    tree = service.build_comment_tree(report.id)
    
    # Verify structure
    assert len(tree) == 2  # Two top-level comments
    assert tree[0]["id"] == top1.id
    assert len(tree[0]["replies"]) == 1
    assert tree[0]["replies"][0]["id"] == reply_to_top1.id
    assert tree[1]["id"] == top2.id
    assert len(tree[1]["replies"]) == 0


def test_build_comment_tree_empty(db_session):
    """Test building a comment tree for a report with no comments."""
    # Create user and report
    user = User(email="test@example.com", phone="1234567890")
    user.set_password("password123")
    db_session.add(user)
    db_session.flush()
    
    report = Report(
        user_id=user.id,
        photo_url="http://example.com/photo.jpg",
        latitude=40.0,
        longitude=-111.0,
        category="Pothole",
        severity_score=5,
    )
    db_session.add(report)
    db_session.commit()
    
    # Build tree
    service = CommentService(db_session)
    tree = service.build_comment_tree(report.id)
    
    assert tree == []


def test_get_comment_replies(db_session):
    """Test getting direct replies to a comment. Requirements: 14.3"""
    # Create user and report
    user = User(email="test@example.com", phone="1234567890")
    user.set_password("password123")
    db_session.add(user)
    db_session.flush()
    
    report = Report(
        user_id=user.id,
        photo_url="http://example.com/photo.jpg",
        latitude=40.0,
        longitude=-111.0,
        category="Pothole",
        severity_score=5,
    )
    db_session.add(report)
    db_session.commit()
    
    # Create comment hierarchy
    service = CommentService(db_session)
    parent = service.create_comment(report.id, user.id, "Parent comment")
    reply1 = service.create_comment(report.id, user.id, "Reply 1", parent.id)
    reply2 = service.create_comment(report.id, user.id, "Reply 2", parent.id)
    nested_reply = service.create_comment(report.id, user.id, "Nested reply", reply1.id)
    
    # Get direct replies to parent
    replies = service.get_comment_replies(parent.id)
    
    assert len(replies) == 2
    assert replies[0].id == reply1.id
    assert replies[1].id == reply2.id
    
    # Get replies to reply1 (should include nested reply)
    nested_replies = service.get_comment_replies(reply1.id)
    assert len(nested_replies) == 1
    assert nested_replies[0].id == nested_reply.id
    
    # Get replies to reply2 (should be empty)
    no_replies = service.get_comment_replies(reply2.id)
    assert len(no_replies) == 0
