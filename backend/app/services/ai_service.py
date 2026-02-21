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
        logger.info("Encoded image to base64 [request_id=%s, original_size=%d bytes, b64_length=%d chars]", 
                   request_id, len(photo_bytes), len(b64_image))

        categories_str = ", ".join(VALID_CATEGORIES)
        
        # Enhanced system prompt based on prompt engineering best practices
        system_prompt = (
            "You are an expert infrastructure damage assessment specialist with years of experience "
            "evaluating municipal infrastructure issues. Your role is to analyze photos of infrastructure "
            "problems and provide accurate categorization and severity ratings that will guide maintenance "
            "teams in prioritizing repairs.\n\n"
            "Your analysis must be:\n"
            "- Evidence-based: Only assess what you can clearly see in the image\n"
            "- Specific: Identify concrete visual indicators of damage\n"
            "- Safety-focused: Prioritize issues that pose immediate risks to public safety\n"
            "- Actionable: Provide ratings that help maintenance teams allocate resources effectively"
        )
        
        # Enhanced user prompt with detailed category descriptions and severity rubric
        user_prompt = (
            f"Analyze this infrastructure issue photo in detail. Examine the image carefully and identify:\n"
            f"1. What type of infrastructure problem is visible?\n"
            f"2. What is the extent and severity of the damage?\n"
            f"3. What safety risks or functional impacts does this create?\n\n"
            f"CATEGORY IDENTIFICATION:\n"
            f"Choose the MOST SPECIFIC category that matches what you see:\n\n"
            f"- **Pothole**: Road surface damage with visible depression, hole, or crater. Look for: exposed aggregate, "
            f"cracked asphalt edges, depth indicators, water pooling, tire damage risk.\n\n"
            f"- **Water Leak**: Active water flow or evidence of leaking pipes. Look for: water streams, wet patches, "
            f"puddles on dry days, exposed pipes, water stains, erosion around infrastructure.\n\n"
            f"- **Vandalism**: Intentional damage or defacement. Look for: graffiti, broken fixtures, smashed glass, "
            f"deliberately damaged property, spray paint, scratched surfaces.\n\n"
            f"- **Broken Streetlight**: Non-functional or damaged street lighting. Look for: dark/unlit fixtures, "
            f"broken bulbs, damaged poles, hanging wires, shattered covers, tilted posts.\n\n"
            f"- **Illegal Dumping**: Unauthorized disposal of waste or materials. Look for: trash piles, discarded "
            f"furniture, construction debris, abandoned items, waste in unauthorized locations.\n\n"
            f"- **Other**: Use ONLY if the issue clearly doesn't fit any category above. Examples: sidewalk cracks, "
            f"overgrown vegetation, damaged signage, drainage issues.\n\n"
            f"SEVERITY ASSESSMENT (1-10 scale):\n"
            f"Rate based on these specific criteria:\n\n"
            f"**1-3 (Minor - Low Priority)**\n"
            f"- Cosmetic damage only, no functional impact\n"
            f"- No safety hazards present\n"
            f"- Can wait weeks/months for repair\n"
            f"- Examples: Small surface cracks, minor paint chips, light graffiti on non-critical surfaces\n\n"
            f"**4-6 (Moderate - Medium Priority)**\n"
            f"- Functional impairment but not dangerous\n"
            f"- Minor inconvenience to users\n"
            f"- Should be addressed within days/weeks\n"
            f"- Examples: Small potholes (< 6 inches), minor leaks, dim streetlights, small trash accumulation\n\n"
            f"**7-8 (Serious - High Priority)**\n"
            f"- Clear safety concern or significant functional impact\n"
            f"- Could cause injury or property damage\n"
            f"- Requires attention within 24-48 hours\n"
            f"- Examples: Large potholes (> 6 inches deep), active water leaks, completely dark streets, "
            f"extensive vandalism, large illegal dumps\n\n"
            f"**9-10 (Critical - Immediate Action)**\n"
            f"- Imminent danger to public safety\n"
            f"- High risk of serious injury or major property damage\n"
            f"- Requires emergency response (same day)\n"
            f"- Examples: Deep potholes causing vehicle damage, major water main breaks, exposed electrical wires, "
            f"hazardous material dumping, complete road blockage\n\n"
            f"RESPONSE FORMAT:\n"
            f"Respond with ONLY a valid JSON object (no markdown code blocks, no explanations):\n"
            f'{{"category": "CategoryName", "severity_score": X}}\n\n'
            f"Valid categories: {categories_str}\n\n"
            f"Base your assessment on concrete visual evidence in the image. If the image is unclear or doesn't show "
            f"infrastructure damage, use category 'Other' with severity 3-5."
        )

        logger.info("Calling Groq API with model llama-3.2-90b-vision-preview [request_id=%s, prompt_length=%d chars]", 
                   request_id, len(system_prompt) + len(user_prompt))
        
        try:
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
                max_tokens=300,  # Increased from 150 to allow for more detailed responses
                temperature=0.1,  # Low temperature for consistent, factual responses
            )

            content = response.choices[0].message.content
            logger.info("Groq API response received [request_id=%s, response_length=%d chars]: %s", 
                       request_id, len(content), content[:200])
            return {"content": content, "request_id": request_id}
        except Exception as e:
            logger.error("Groq API call failed [request_id=%s]: %s", request_id, str(e), exc_info=True)
            raise

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
