"""
AI Vision API integration service.

Sends images to OpenAI Vision API for category/severity analysis.
Implements retry with exponential backoff and graceful fallback.

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
"""
import base64
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Callable, Optional

import openai

from app.core.config import settings
from app.models.report import VALID_CATEGORIES

logger = logging.getLogger(__name__)

DEFAULT_CATEGORY = "Other"
DEFAULT_SEVERITY = 5
MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0  # seconds


@dataclass
class AIAnalysis:
    """Result of AI image analysis."""
    category: str
    severity_score: int
    ai_generated: bool
    request_id: Optional[str] = None


class AIService:
    """Service for AI-powered image analysis using OpenAI Vision API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.client: Optional[openai.OpenAI] = None
        if self.api_key:
            self.client = openai.OpenAI(api_key=self.api_key)

    def analyze_image(self, photo_bytes: bytes) -> AIAnalysis:
        """
        Send image to OpenAI Vision API and parse the response.
        Returns AIAnalysis with category and severity.
        Falls back to defaults on failure (Req 2.4).
        """
        if not self.client:
            logger.warning("No OpenAI API key configured; returning defaults")
            return self.handle_api_error()

        request_id = str(uuid.uuid4())

        def _call_api():
            return self._call_vision_api(photo_bytes, request_id)

        try:
            response = self.retry_with_backoff(_call_api, MAX_RETRIES)
            return self._parse_response(response, request_id)
        except Exception as e:
            logger.error("AI analysis failed after retries [request_id=%s]: %s", request_id, e)
            return self.handle_api_error(request_id)

    def _call_vision_api(self, photo_bytes: bytes, request_id: str) -> dict:
        """Make the actual API call to OpenAI Vision."""
        b64_image = base64.b64encode(photo_bytes).decode("utf-8")

        categories_str = ", ".join(VALID_CATEGORIES)
        prompt = (
            f"Analyze this infrastructure issue photo. "
            f"Respond with ONLY a JSON object (no markdown, no explanation) with two fields:\n"
            f'  "category": one of [{categories_str}]\n'
            f'  "severity_score": integer from 1 to 10 (10 = most severe)\n'
            f"Example: {{\"category\": \"Pothole\", \"severity_score\": 7}}"
        )

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64_image}",
                                "detail": "low",
                            },
                        },
                    ],
                }
            ],
            max_tokens=100,
        )

        content = response.choices[0].message.content
        return {"content": content, "request_id": request_id}

    def _parse_response(self, response: dict, request_id: str) -> AIAnalysis:
        """
        Parse the AI API response to extract category and severity.
        Property 4: AI Response Parsing
        """
        import json

        content = response.get("content", "")

        # Strip markdown code fences if present
        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            # Remove first and last lines (``` markers)
            lines = [l for l in lines if not l.strip().startswith("```")]
            content = "\n".join(lines)

        try:
            data = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Failed to parse AI response [request_id=%s]: %s", request_id, content)
            return self.handle_api_error(request_id)

        category = self.extract_category(data)
        severity = self.extract_severity(data)

        return AIAnalysis(
            category=category,
            severity_score=severity,
            ai_generated=True,
            request_id=request_id,
        )

    @staticmethod
    def extract_category(response: dict) -> str:
        """
        Extract category from AI response dict.
        Returns DEFAULT_CATEGORY if not valid.
        """
        category = response.get("category", DEFAULT_CATEGORY)
        if category not in VALID_CATEGORIES:
            return DEFAULT_CATEGORY
        return category

    @staticmethod
    def extract_severity(response: dict) -> int:
        """
        Extract severity score from AI response dict.
        Clamps to [1, 10] range. Returns DEFAULT_SEVERITY if not valid.
        """
        try:
            score = int(response.get("severity_score", DEFAULT_SEVERITY))
        except (TypeError, ValueError):
            return DEFAULT_SEVERITY
        return max(1, min(10, score))

    @staticmethod
    def handle_api_error(request_id: Optional[str] = None) -> AIAnalysis:
        """
        Return safe default values when API fails.
        Requirements: 2.4
        """
        return AIAnalysis(
            category=DEFAULT_CATEGORY,
            severity_score=DEFAULT_SEVERITY,
            ai_generated=False,
            request_id=request_id,
        )

    @staticmethod
    def retry_with_backoff(fn: Callable, max_retries: int = MAX_RETRIES) -> dict:
        """
        Retry a function with exponential backoff.
        Raises the last exception if all retries fail.
        """
        last_exception = None
        backoff = INITIAL_BACKOFF

        for attempt in range(max_retries):
            try:
                return fn()
            except Exception as e:
                last_exception = e
                logger.warning(
                    "Retry attempt %d/%d failed: %s", attempt + 1, max_retries, e
                )
                if attempt < max_retries - 1:
                    time.sleep(backoff)
                    backoff *= 2

        raise last_exception
