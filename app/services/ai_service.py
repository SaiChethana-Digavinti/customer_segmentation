import logging
import os
import time
from typing import Any, Tuple, List

from dotenv import load_dotenv
from google import genai
from google.genai import types

# Set up logger
logger = logging.getLogger("ai_service")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

# Get Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env")

# Request timeout in milliseconds (minimum 10000ms required by Google GenAI API)
_raw_timeout = int(os.getenv("GEMINI_TIMEOUT_MS", "12000"))
REQUEST_TIMEOUT_MS = max(_raw_timeout, 10000)

# Preferred Gemini models in priority order for low latency and high reliability
PRIMARY_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
_DEFAULT_FALLBACKS = [
    "gemini-3.1-flash-lite",
    "gemini-flash-latest",
    "gemini-3.5-flash-lite",
]

# Ensure candidate list has PRIMARY_MODEL first, without duplicates
MODEL_CHAIN: List[str] = [PRIMARY_MODEL] + [m for m in _DEFAULT_FALLBACKS if m != PRIMARY_MODEL]

# Create Gemini client with configured timeout
client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options=types.HttpOptions(timeout=REQUEST_TIMEOUT_MS),
)


def _extract_customer_context(customer: Any) -> Tuple[str, str, str]:
    """
    Safely extract only high-signal marketing fields for the prompt.
    Avoids sending internal IDs, raw RFM scores, and numeric metrics.
    """
    if isinstance(customer, dict):
        segment = customer.get("segment") or "Valued Customer"
        action = customer.get("recommended_action") or "Engage with personalized recommendations"
        strategy = customer.get("marketing_strategy") or customer.get("campaign") or ""
    else:
        segment = getattr(customer, "segment", None) or "Valued Customer"
        action = getattr(customer, "recommended_action", None) or "Engage with personalized recommendations"
        strategy = getattr(customer, "marketing_strategy", None) or getattr(customer, "campaign", None) or ""

    return str(segment).strip(), str(action).strip(), str(strategy).strip()


def _generate_smart_fallback(segment: str, action: str, strategy: str) -> str:
    """
    Produce a high-quality, tailored marketing recommendation when upstream AI APIs
    are temporarily unavailable, ensuring 100% uptime for end users.
    """
    seg_lower = segment.lower()

    if any(k in seg_lower for k in ["champion", "vip", "platinum"]):
        return (
            "As one of our most distinguished VIP patrons, you have unlocked early VIP access "
            "to our newest seasonal arrivals and exclusive concierge rewards."
        )
    elif any(k in seg_lower for k in ["loyal", "frequent", "advocate"]):
        return (
            "Thank you for being such a valued customer! We've prepared personalized recommendations "
            "and member-exclusive bonus rewards tailored to your shopping preferences."
        )
    elif any(k in seg_lower for k in ["potential", "promising", "growth"]):
        return (
            "You're on the fast track to our highest reward tier! Explore our curated selections "
            "today and enjoy bonus loyalty rewards on your next purchase."
        )
    elif any(k in seg_lower for k in ["risk", "churn", "lost", "leaving"]):
        return (
            "We've truly missed your presence! Discover our fresh new arrivals today with an "
            "exclusive welcome-back privilege crafted specifically for you."
        )
    elif any(k in seg_lower for k in ["hibernating", "attention", "sleep"]):
        return (
            "Exclusive member perks are waiting for you. Reconnect with our latest popular "
            "highlights and take advantage of limited-time seasonal bonuses."
        )
    elif any(k in seg_lower for k in ["new", "recent"]):
        return (
            "Welcome to our community! We are excited to offer you curated starter benefits "
            "and personalized recommendations to kick off your shopping journey."
        )
    else:
        return (
            "We deeply value your business and have hand-selected exclusive offers and "
            "tailored promotions ready for your next shopping experience."
        )


def _extract_response_text(response: Any) -> str:
    """Safely extract generated text from GenAI response across models and candidate structures."""
    if not response:
        return ""
    if getattr(response, "text", None):
        return str(response.text).strip()
    candidates = getattr(response, "candidates", None)
    if candidates:
        for cand in candidates:
            content = getattr(cand, "content", None)
            if content and hasattr(content, "parts"):
                parts_text = []
                for p in content.parts:
                    p_text = getattr(p, "text", None)
                    if p_text:
                        parts_text.append(str(p_text).strip())
                if parts_text:
                    return " ".join(parts_text).strip()
    return ""


def generate_ai_recommendation(customer: Any) -> str:
    """
    Generate a concise, personalized Gemini-powered marketing message.
    Features automated multi-model failover and high-quality fallback for seamless reliability.
    """
    segment, action, strategy = _extract_customer_context(customer)

    strategy_line = f"\n- Strategy: {strategy}" if strategy else ""

    prompt = f"""You are an AI retail marketing assistant. Write a short, personalized marketing message directly to this customer.

Customer Context:
- Segment: {segment}
- Recommended Action: {action}{strategy_line}

Rules:
- Write 1 to 2 engaging sentences addressed directly to the customer.
- Warm, natural, and persuasive tone.
- Do not mention internal metrics, scores, IDs, segment names, or strategy terms.
- Do not include subject lines, greetings placeholders (like [Name]), or brand placeholders.
- Output only the message text."""

    # Try each model in the fallback chain
    for model_name in MODEL_CHAIN:
        start_time = time.perf_counter()
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=120,
                    temperature=0.7,
                ),
            )
            duration = time.perf_counter() - start_time
            message = _extract_response_text(response)
            if message:
                logger.info(
                    "AI recommendation generated in %.2fs (model=%s, segment=%s)",
                    duration,
                    model_name,
                    segment,
                )
                return message
            else:
                logger.warning(
                    "Model %s returned empty text after %.2fs. Trying next model...",
                    model_name,
                    duration,
                )
        except Exception as exc:
            duration = time.perf_counter() - start_time
            logger.warning(
                "Gemini model '%s' failed after %.2fs (%s). Trying fallback...",
                model_name,
                duration,
                exc,
            )

    # If all models in the chain fail or are unavailable, use the smart fallback
    logger.warning(
        "All Gemini models in fallback chain failed. Using intelligent dynamic fallback for segment '%s'",
        segment,
    )
    return _generate_smart_fallback(segment, action, strategy)