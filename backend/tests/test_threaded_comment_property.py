"""
Property-based test for threaded comment association.

Property 49: Threaded Comment Association
Requirements: 14.3
"""
import uuid
from typing import List

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


class TestThreadedCommentAssociation:
    """
    Feature: civic-pulse, Property 49: Threaded Comment Association
    
    For any comment with a parent comment ID, the parent-child relationship
    should be correctly maintained and retrievable.
    
    Validates: Requirements 14.3
    """
    
    def test_simple_parent_child_relationship(
        self,
        comment_service: CommentService,
        test_report: Report,
        test_user: User
    ):
        """Test that a simple parent-child relationship is maintained."""
        # Create parent comment
        parent = comment_service.create_comment(
            report_id=test_report.id,
            user_id=test_user.id,
            text="Parent comment"
        )
        
        # Create child comment
        child = comment_service.create_comment(
            report_id=test_report.id,
            user_id=test_user.id,
            text="Child comment",
            parent_comment_id=parent.id
        )
        
        # Verify relationship
        assert child.parent_comment_id == parent.id
        
        # Retrieve and verify relationship is maintained
        retrieved_child = comment_service.get_comment(child.id)
        assert retrieved_child.parent_comment_id == parent.id
        
        # Verify parent can be retrieved
        retrieved_parent = comment_service.get_comment(parent.id)
        assert retrieved_parent.id == parent.id
    
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @given(
        num_replies=st.integers(min_value=1, max_value=10)
    )
    def test_multiple_replies_to_parent(
        self,
        db_session: Session,
        test_user: User,
        num_replies: int
    ):
        """
        Property 49: For any number of replies to a parent comment,
        all parent-child relationships should be correctly maintained.
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
        
        comment_service = CommentService(db_session)
        
        # Create parent comment
        parent = comment_service.create_comment(
            report_id=report.id,
            user_id=test_user.id,
            text="Parent comment"
        )
        
        # Create multiple replies
        replies = []
        for i in range(num_replies):
            reply = comment_service.create_comment(
                report_id=report.id,
                user_id=test_user.id,
                text=f"Reply {i}",
                parent_comment_id=parent.id
            )
            replies.append(reply)
        
        # Verify all replies have correct parent
        for reply in replies:
            assert reply.parent_comment_id == parent.id
            
            # Retrieve and verify relationship is maintained
            retrieved_reply = comment_service.get_comment(reply.id)
            assert retrieved_reply.parent_comment_id == parent.id
        
        # Verify get_comment_replies returns all replies
        retrieved_replies = comment_service.get_comment_replies(parent.id)
        assert len(retrieved_replies) == num_replies
        
        # Verify all retrieved replies have correct parent
        for retrieved_reply in retrieved_replies:
            assert retrieved_reply.parent_comment_id == parent.id
    
    @settings(
        max_examples=30,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @given(
        depth=st.integers(min_value=2, max_value=5)
    )
    def test_nested_comment_hierarchy(
        self,
        db_session: Session,
        test_user: User,
        depth: int
    ):
        """
        Property 49: For any depth of nested comments,
        all parent-child relationships should be correctly maintained
        throughout the hierarchy.
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
        
        comment_service = CommentService(db_session)
        
        # Create nested hierarchy
        comments = []
        parent_id = None
        
        for i in range(depth):
            comment = comment_service.create_comment(
                report_id=report.id,
                user_id=test_user.id,
                text=f"Comment at depth {i}",
                parent_comment_id=parent_id
            )
            comments.append(comment)
            parent_id = comment.id
        
        # Verify each comment has correct parent
        for i, comment in enumerate(comments):
            if i == 0:
                # First comment should have no parent
                assert comment.parent_comment_id is None
            else:
                # Each subsequent comment should have previous as parent
                assert comment.parent_comment_id == comments[i - 1].id
                
                # Retrieve and verify relationship is maintained
                retrieved = comment_service.get_comment(comment.id)
                assert retrieved.parent_comment_id == comments[i - 1].id
    
    def test_comment_tree_structure(
        self,
        comment_service: CommentService,
        test_report: Report,
        test_user: User
    ):
        """
        Property 49: The build_comment_tree method should correctly
        represent parent-child relationships in a hierarchical structure.
        """
        # Create a comment hierarchy
        parent1 = comment_service.create_comment(
            test_report.id, test_user.id, "Parent 1"
        )
        parent2 = comment_service.create_comment(
            test_report.id, test_user.id, "Parent 2"
        )
        child1_1 = comment_service.create_comment(
            test_report.id, test_user.id, "Child 1.1", parent1.id
        )
        child1_2 = comment_service.create_comment(
            test_report.id, test_user.id, "Child 1.2", parent1.id
        )
        grandchild1_1_1 = comment_service.create_comment(
            test_report.id, test_user.id, "Grandchild 1.1.1", child1_1.id
        )
        
        # Build tree
        tree = comment_service.build_comment_tree(test_report.id)
        
        # Verify tree structure
        assert len(tree) == 2  # Two top-level comments
        
        # Find parent1 in tree
        parent1_node = next(c for c in tree if c["id"] == parent1.id)
        assert len(parent1_node["replies"]) == 2
        
        # Verify child relationships
        child1_1_node = next(c for c in parent1_node["replies"] if c["id"] == child1_1.id)
        assert child1_1_node["parent_comment_id"] == parent1.id
        assert len(child1_1_node["replies"]) == 1
        
        # Verify grandchild relationship
        grandchild_node = child1_1_node["replies"][0]
        assert grandchild_node["id"] == grandchild1_1_1.id
        assert grandchild_node["parent_comment_id"] == child1_1.id
        
        # Verify parent2 has no replies
        parent2_node = next(c for c in tree if c["id"] == parent2.id)
        assert len(parent2_node["replies"]) == 0
    
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @given(
        num_top_level=st.integers(min_value=1, max_value=5),
        replies_per_parent=st.integers(min_value=0, max_value=3)
    )
    def test_tree_structure_with_multiple_branches(
        self,
        db_session: Session,
        test_user: User,
        num_top_level: int,
        replies_per_parent: int
    ):
        """
        Property 49: For any tree structure with multiple top-level comments
        and varying numbers of replies, all parent-child relationships
        should be correctly represented in the tree.
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
        
        comment_service = CommentService(db_session)
        
        # Create top-level comments
        top_level_comments = []
        for i in range(num_top_level):
            comment = comment_service.create_comment(
                report.id, test_user.id, f"Top level {i}"
            )
            top_level_comments.append(comment)
        
        # Create replies for each top-level comment
        all_replies = {}
        for parent in top_level_comments:
            replies = []
            for j in range(replies_per_parent):
                reply = comment_service.create_comment(
                    report.id, test_user.id, f"Reply to {parent.text}", parent.id
                )
                replies.append(reply)
            all_replies[parent.id] = replies
        
        # Build tree
        tree = comment_service.build_comment_tree(report.id)
        
        # Verify tree structure
        assert len(tree) == num_top_level
        
        # Verify each top-level comment and its replies
        for parent in top_level_comments:
            parent_node = next(c for c in tree if c["id"] == parent.id)
            assert parent_node["parent_comment_id"] is None
            assert len(parent_node["replies"]) == replies_per_parent
            
            # Verify all replies have correct parent
            for reply_node in parent_node["replies"]:
                assert reply_node["parent_comment_id"] == parent.id
    
    def test_orphaned_comment_handling(
        self,
        db_session: Session,
        comment_service: CommentService,
        test_report: Report,
        test_user: User
    ):
        """
        Property 49: If a comment references a non-existent parent,
        the system should handle it gracefully (reject creation).
        """
        # Try to create a comment with non-existent parent
        with pytest.raises(ValueError, match="Parent comment not found"):
            comment_service.create_comment(
                report_id=test_report.id,
                user_id=test_user.id,
                text="Orphaned comment",
                parent_comment_id=uuid.uuid4()
            )
    
    def test_cross_report_parent_rejection(
        self,
        db_session: Session,
        test_user: User
    ):
        """
        Property 49: A comment cannot have a parent from a different report.
        The parent-child relationship must be within the same report.
        """
        # Create two reports
        report1 = Report(
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
        report2 = Report(
            user_id=test_user.id,
            photo_url=f"/uploads/{uuid.uuid4()}.jpg",
            latitude=40.7128,
            longitude=-74.0060,
            category="Water Leak",
            severity_score=6,
            status="Reported",
            ai_generated=False,
            archived=False
        )
        db_session.add_all([report1, report2])
        db_session.commit()
        
        comment_service = CommentService(db_session)
        
        # Create comment on report1
        comment_on_report1 = comment_service.create_comment(
            report1.id, test_user.id, "Comment on report 1"
        )
        
        # Try to create reply on report2 with parent from report1
        with pytest.raises(ValueError, match="Parent comment does not belong to this report"):
            comment_service.create_comment(
                report_id=report2.id,
                user_id=test_user.id,
                text="Cross-report reply",
                parent_comment_id=comment_on_report1.id
            )
    
    @settings(
        max_examples=30,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @given(
        num_siblings=st.integers(min_value=2, max_value=8)
    )
    def test_sibling_comments_independence(
        self,
        db_session: Session,
        test_user: User,
        num_siblings: int
    ):
        """
        Property 49: Multiple comments with the same parent (siblings)
        should each maintain their independent relationship with the parent.
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
        
        comment_service = CommentService(db_session)
        
        # Create parent
        parent = comment_service.create_comment(
            report.id, test_user.id, "Parent comment"
        )
        
        # Create sibling comments
        siblings = []
        for i in range(num_siblings):
            sibling = comment_service.create_comment(
                report.id, test_user.id, f"Sibling {i}", parent.id
            )
            siblings.append(sibling)
        
        # Verify each sibling has correct parent
        for sibling in siblings:
            assert sibling.parent_comment_id == parent.id
            
            # Retrieve and verify
            retrieved = comment_service.get_comment(sibling.id)
            assert retrieved.parent_comment_id == parent.id
        
        # Verify get_comment_replies returns all siblings
        replies = comment_service.get_comment_replies(parent.id)
        assert len(replies) == num_siblings
        
        # Verify all replies are in the siblings list
        reply_ids = {r.id for r in replies}
        sibling_ids = {s.id for s in siblings}
        assert reply_ids == sibling_ids
    
    def test_comment_tree_chronological_order_within_level(
        self,
        comment_service: CommentService,
        test_report: Report,
        test_user: User
    ):
        """
        Property 49: Within the tree structure, comments at the same level
        should maintain chronological order while preserving parent-child
        relationships.
        """
        # Create parent
        parent = comment_service.create_comment(
            test_report.id, test_user.id, "Parent"
        )
        
        # Create replies in order
        reply1 = comment_service.create_comment(
            test_report.id, test_user.id, "Reply 1", parent.id
        )
        reply2 = comment_service.create_comment(
            test_report.id, test_user.id, "Reply 2", parent.id
        )
        reply3 = comment_service.create_comment(
            test_report.id, test_user.id, "Reply 3", parent.id
        )
        
        # Build tree
        tree = comment_service.build_comment_tree(test_report.id)
        
        # Find parent node
        parent_node = tree[0]
        assert parent_node["id"] == parent.id
        
        # Verify replies are in chronological order
        replies = parent_node["replies"]
        assert len(replies) == 3
        assert replies[0]["id"] == reply1.id
        assert replies[1]["id"] == reply2.id
        assert replies[2]["id"] == reply3.id
        
        # Verify timestamps are in order
        assert replies[0]["created_at"] <= replies[1]["created_at"]
        assert replies[1]["created_at"] <= replies[2]["created_at"]
