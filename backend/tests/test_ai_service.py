"""
Tests for AI Vision API integration.

Properties validated:
- Property 4: AI Response Parsing
- Property 5: AI Analysis Persistence
- Property 6: User Category Override (additional coverage)

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6
"""
import json
import uuid
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given, settings as h_settings, HealthCheck
from hypothesis import strategies as st

from app.models.report import VALID_CATEGORIES
from app.services.ai_service import (
    AIService,
    AIAnalysis,
    DEFAULT_CATEGORY,
    DEFAULT_SEVERITY,
    MAX_RETRIES,
)
from app.services.report_service import ReportService


# ---------- Property 4: AI Response Parsing ----------

class TestAIResponseParsing:
    """Property 4: For any valid AI response, extract category from predefined
    list and severity 1-10 inclusive."""

    @given(
        category=st.sampled_from(VALID_CATEGORIES),
        severity=st.integers(min_value=1, max_value=10),
    )
    @h_settings(deadline=None)
    def test_valid_response_parses_correctly(self, category, severity):
        """Valid JSON with known category and severity parses correctly."""
        response = {"category": category, "severity_score": severity}
        assert AIService.extract_category(response) == category
        assert AIService.extract_severity(response) == severity

    @given(category=st.text(min_size=1, max_size=50).filter(lambda x: x not in VALID_CATEGORIES))
    @h_settings(deadline=None)
    def test_unknown_category_defaults_to_other(self, category):
        """Unknown category strings fall back to 'Other'."""
        response = {"category": category, "severity_score": 5}
        assert AIService.extract_category(response) == DEFAULT_CATEGORY

    @given(severity=st.integers(min_value=11, max_value=1000))
    @h_settings(deadline=None)
    def test_severity_above_10_clamped(self, severity):
        """Severity above 10 is clamped to 10."""
        response = {"severity_score": severity}
        assert AIService.extract_severity(response) == 10

    @given(severity=st.integers(min_value=-1000, max_value=0))
    @h_settings(deadline=None)
    def test_severity_below_1_clamped(self, severity):
        """Severity below 1 is clamped to 1."""
        response = {"severity_score": severity}
        assert AIService.extract_severity(response) == 1

    def test_missing_category_defaults(self):
        """Missing category key returns default."""
        assert AIService.extract_category({}) == DEFAULT_CATEGORY

    def test_missing_severity_defaults(self):
        """Missing severity key returns default."""
        assert AIService.extract_severity({}) == DEFAULT_SEVERITY

    def test_non_numeric_severity_defaults(self):
        """Non-numeric severity returns default."""
        assert AIService.extract_severity({"severity_score": "high"}) == DEFAULT_SEVERITY

    def test_parse_valid_json_response(self):
        """Full _parse_response flow with valid JSON."""
        service = AIService(api_key="fake")
        response = {"content": '{"category": "Pothole", "severity_score": 8}', "request_id": "r1"}
        result = service._parse_response(response, "r1")
        assert result.category == "Pothole"
        assert result.severity_score == 8
        assert result.ai_generated is True

    def test_parse_markdown_fenced_json(self):
        """AI sometimes wraps JSON in markdown code fences."""
        service = AIService(api_key="fake")
        content = '```json\n{"category": "Water Leak", "severity_score": 6}\n```'
        response = {"content": content, "request_id": "r2"}
        result = service._parse_response(response, "r2")
        assert result.category == "Water Leak"
        assert result.severity_score == 6

    def test_parse_invalid_json_returns_defaults(self):
        """Invalid JSON falls back to defaults."""
        service = AIService(api_key="fake")
        response = {"content": "not json at all", "request_id": "r3"}
        result = service._parse_response(response, "r3")
        assert result.category == DEFAULT_CATEGORY
        assert result.severity_score == DEFAULT_SEVERITY
        assert result.ai_generated is False


# ---------- Error Handling & Retry (Req 2.4) ----------

class TestAIErrorHandling:
    """Verify fallback behavior when AI API fails."""

    def test_handle_api_error_returns_defaults(self):
        """handle_api_error returns 'Other' and severity 5."""
        result = AIService.handle_api_error("req-123")
        assert result.category == DEFAULT_CATEGORY
        assert result.severity_score == DEFAULT_SEVERITY
        assert result.ai_generated is False
        assert result.request_id == "req-123"

    def test_no_api_key_returns_defaults(self):
        """When no API key configured, analyze_image returns defaults."""
        service = AIService(api_key="")
        # Force client to None
        service.client = None
        result = service.analyze_image(b"fake-photo")
        assert result.category == DEFAULT_CATEGORY
        assert result.severity_score == DEFAULT_SEVERITY
        assert result.ai_generated is False

    def test_retry_with_backoff_succeeds_on_third_attempt(self):
        """Retry logic succeeds when function passes on third attempt."""
        call_count = 0

        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("API down")
            return {"content": '{"category": "Pothole", "severity_score": 7}'}

        with patch("app.services.ai_service.time.sleep"):
            result = AIService.retry_with_backoff(flaky, max_retries=3)

        assert call_count == 3
        assert result["content"] is not None

    def test_retry_with_backoff_exhausted_raises(self):
        """After max retries, last exception is raised."""
        def always_fail():
            raise ConnectionError("API down")

        with patch("app.services.ai_service.time.sleep"):
            with pytest.raises(ConnectionError):
                AIService.retry_with_backoff(always_fail, max_retries=3)

    def test_analyze_image_api_failure_returns_defaults(self):
        """analyze_image returns defaults when API call fails all retries."""
        service = AIService(api_key="fake-key")
        service.client = MagicMock()
        service.client.chat.completions.create.side_effect = Exception("API Error")

        with patch("app.services.ai_service.time.sleep"):
            result = service.analyze_image(b"fake-photo")

        assert result.category == DEFAULT_CATEGORY
        assert result.severity_score == DEFAULT_SEVERITY
        assert result.ai_generated is False


# ---------- Property 5: AI Analysis Persistence ----------

class TestAIAnalysisPersistence:
    """Property 5: AI analysis results are stored with the report and retrievable."""

    def test_ai_analysis_stored_with_report(self, db_session):
        """AI category and severity are stored and retrievable."""
        from app.models.user import User

        user = User(
            email="ai_test@example.com",
            password_hash="$2b$12$LJ3m4ys3Lzgqoif3gk3sYuTTqXlPYRBJOT9.XCNpiKkVfMCfuIELe",
            phone="+1234567890",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        service = ReportService(db_session)
        report = service.create_report(
            user_id=user.id,
            photo_bytes=b"fake-photo",
            latitude=40.0,
            longitude=-111.0,
            category="Pothole",
            severity_score=8,
            ai_generated=True,
        )

        retrieved = service.get_report(report.id)
        assert retrieved is not None
        assert retrieved.category == "Pothole"
        assert retrieved.severity_score == 8
        assert retrieved.ai_generated is True

    def test_ai_analysis_persists_across_queries(self, db_session):
        """AI analysis is available in filtered queries."""
        from app.models.user import User

        user = User(
            email="persist@example.com",
            password_hash="$2b$12$LJ3m4ys3Lzgqoif3gk3sYuTTqXlPYRBJOT9.XCNpiKkVfMCfuIELe",
            phone="+1234567890",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        service = ReportService(db_session)
        service.create_report(
            user_id=user.id,
            photo_bytes=b"photo1",
            latitude=40.0,
            longitude=-111.0,
            category="Water Leak",
            severity_score=6,
            ai_generated=True,
        )

        reports = service.get_reports_filtered(category="Water Leak")
        assert len(reports) == 1
        assert reports[0].severity_score == 6
        assert reports[0].ai_generated is True


# ---------- Property 6: User Category Override (extra coverage) ----------

class TestUserCategoryOverrideAI:
    """Property 6: User can override AI-generated category."""

    def test_override_clears_ai_generated_flag(self, db_session):
        """Overriding category sets ai_generated to False."""
        from app.models.user import User

        user = User(
            email="override@example.com",
            password_hash="$2b$12$LJ3m4ys3Lzgqoif3gk3sYuTTqXlPYRBJOT9.XCNpiKkVfMCfuIELe",
            phone="+1234567890",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        service = ReportService(db_session)
        report = service.create_report(
            user_id=user.id,
            photo_bytes=b"ai-photo",
            latitude=40.0,
            longitude=-111.0,
            category="Pothole",
            severity_score=9,
            ai_generated=True,
        )
        assert report.ai_generated is True

        updated = service.update_category(report.id, "Vandalism")
        assert updated.category == "Vandalism"
        assert updated.ai_generated is False

    @given(category=st.sampled_from(VALID_CATEGORIES))
    @h_settings(
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_override_any_valid_category(self, db_session, category):
        """Any valid category can be set as an override."""
        from app.models.user import User

        user = User(
            email=f"cat-{uuid.uuid4().hex[:8]}@example.com",
            password_hash="$2b$12$LJ3m4ys3Lzgqoif3gk3sYuTTqXlPYRBJOT9.XCNpiKkVfMCfuIELe",
            phone="+1234567890",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        service = ReportService(db_session)
        report = service.create_report(
            user_id=user.id,
            photo_bytes=b"photo",
            latitude=40.0,
            longitude=-111.0,
            category="Other",
            severity_score=5,
            ai_generated=True,
        )

        updated = service.update_category(report.id, category)
        assert updated.category == category
