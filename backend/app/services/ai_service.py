"""
AI Vision API integration service.

Sends images to Groq Vision API for category/severity analysis.
Implements retry with exponential backoff and graceful fallback.

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
"""
import base64
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Callable, Optional

from groq import Groq

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
    """Service for AI-powered image analysis using Groq Vision API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.client: Optional[Groq] = None
        if self.api_key:
            self.client = Groq(api_key=self.api_key)

    def analyze_image(self, photo_bytes: bytes) -> AIAnalysis:
        """
        Send image to Groq Vision API and parse the response.
        Returns AIAnalysis with category and severity.
        Falls back to defaults on failure (Req 2.4).
        """
        if not self.api_key:
            logger.warning("No Groq API key configured (GROQ_API_KEY env var is empty); returning defaults")
            return self.handle_api_error()
        
        if not self.client:
            logger.warning("Groq client not initialized; returning defaults")
            return self.handle_api_error()

        request_id = str(uuid.uuid4())
        logger.info("Starting AI analysis [request_id=%s, image_size=%d bytes]", request_id, len(photo_bytes))

        def _call_api():
            return self._call_vision_api(photo_bytes, request_id)

        try:
            response = self.retry_with_backoff(_call_api, MAX_RETRIES)
            logger.info("AI API call successful [request_id=%s]", request_id)
            return self._parse_response(response, request_id)
        except Exception as e:
            logger.error("AI analysis failed after retries [request_id=%s]: %s", request_id, e, exc_info=True)
            return self.handle_api_error(request_id)

    def _call_vision_api(self, photo_bytes: bytes, request_id: str) -> dict:
        """Make the actual API call to Groq Vision."""
        b64_image = base64.b64encode(photo_bytes).decode("utf-8")
        logger.info("Encoded image to base64 [request_id=%s, b64_length=%d]", request_id, len(b64_image))

        categories_str = ", ".join(VALID_CATEGORIES)
        system_prompt = (
            "You are an AI assistant specialized in analyzing infrastructure issues from photos. "
            "Your task is to categorize the issue and assess its severity based on visual evidence. "
            "Consider factors like: size of damage, safety hazard level, impact on daily use, urgency of repair needed."
        )
        user_prompt = (
            f"Analyze this infrastructure issue photo carefully. Look at the actual content of the image.\n\n"
            f"Based on what you see, respond with ONLY a JSON object (no markdown, no explanation) with two fields:\n"
            f'  "category": must be exactly one of [{categories_str}]\n'
            f'  "severity_score": integer from 1 to 10 where:\n'
            f"    1-3 = Minor (cosmetic, no safety risk)\n"
            f"    4-6 = Moderate (functional issue, minor inconvenience)\n"
            f"    7-8 = Serious (safety concern, significant impact)\n"
            f"    9-10 = Critical (immediate danger, urgent action needed)\n\n"
            f"Analyze the specific details in this image and provide an accurate assessment.\n"
            f'Example response: {{"category": "Pothole", "severity_score": 7}}'
        )

        logger.info("Calling Groq API with model llama-3.2-90b-vision-preview [request_id=%s]", request_id)
        
        response = self.client.chat.completions.create(
            model="llama-3.2-90b-vision-preview",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64_image}",
                            },
                        },
                    ],
                }
            ],
            max_tokens=150,
            temperature=0.1,  # Low temperature for consistent, factual responses
        )

        content = response.choices[0].message.content
        logger.info("Groq API response [request_id=%s]: %s", request_id, content)
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
