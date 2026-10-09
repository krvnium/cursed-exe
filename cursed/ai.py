import os
import json
import base64
import logging
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv
from groq import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    BadRequestError,
    Groq,
    RateLimitError,
)

load_dotenv()

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "qwen/qwen3.8-27b"
DEFAULT_GROQ_BASE_URL = "https://api.groq.com"
LEGACY_MODELS = {"llama-3.2-11b-vision-preview"}

ALLOWED_CLASSES = [
    "ORGANIC", "ANIMAL", "AVIAN", "TECHNOLOGY", "HOUSEHOLD",
    "STRUCTURE", "INANIMATE", "GLITCH", "UNKNOWN"
]
MAX_FIELD_LENGTHS = {
    "subject": 80,
    "name": 60,
    "class": 32,
    "quirky_text": 180,
    "lore": 500,
}

FALLBACK_DATA = {
    "subject": "Unidentified Object",
    "name": "Null Anomaly",
    "class": "GLITCH",
    "quirky_text": "Error 404: Vibe not found.",
    "lore": "The reality matrix timed out. This cursed fragment exists only in the void."
}


def _api_key() -> str | None:
    return os.getenv("GROQ_API_KEY") or os.getenv("VISION_API_KEY")


def _model_name() -> str:
    configured_model = os.getenv("VISION_MODEL_NAME", "").strip()
    if not configured_model or configured_model in LEGACY_MODELS:
        return DEFAULT_MODEL
    return configured_model


def _normalize_endpoint(endpoint: str | None) -> str | None:
    if not endpoint:
        return None

    normalized = endpoint.strip().rstrip("/")
    if not normalized:
        return None
    if normalized.endswith("/openai/v1"):
        normalized = normalized[:-len("/openai/v1")].rstrip("/")
    if not normalized.startswith(("http://", "https://")):
        logger.warning("AI endpoint ignored: endpoint must use HTTP or HTTPS")
        return None
    return normalized


def _client() -> Groq | None:
    api_key = _api_key()
    if not api_key:
        return None

    client_options = {"api_key": api_key}
    endpoint = _normalize_endpoint(os.getenv("VISION_API_ENDPOINT"))
    if endpoint:
        client_options["base_url"] = endpoint
    return Groq(**client_options)


def _validate_metadata(value: object) -> dict | None:
    if not isinstance(value, dict):
        return None

    required_keys = ("subject", "name", "class", "quirky_text", "lore")
    if set(value) != set(required_keys):
        return None
    if value["class"] not in ALLOWED_CLASSES:
        return None

    validated = {}
    for key in required_keys:
        field = value[key]
        if not isinstance(field, str):
            return None
        field = field.strip()
        if not field or len(field) > MAX_FIELD_LENGTHS[key]:
            return None
        validated[key] = field
    return validated


def _log_bad_request(error: BadRequestError) -> None:
    details = str(error).lower()
    if "model" in details:
        logger.error("AI metadata failed: Groq rejected the configured model")
    elif "image" in details or "vision" in details:
        logger.error("AI metadata failed: Groq rejected the image input")
    else:
        logger.error("AI metadata failed: Groq rejected the request")


def _encode_image(image: Image.Image) -> str:
    buffered = BytesIO()
    image.convert("RGB").save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def generate_entity_metadata(image: Image.Image) -> dict:
    model_name = _model_name()

    if not _api_key():
        logger.warning("AI metadata unavailable: no Groq API key configured")
        return FALLBACK_DATA.copy()

    base64_image = _encode_image(image)

    prompt = (
        "Analyze this image and turn the main subject into a funny, fictional retro RPG creature. "
        "1. 'subject': Identify the real-world object. "
        "2. 'name': Generate a unique, funny name based on the object using puns or internet wordplay. "
        f"3. 'class': Assign a category STRICTLY from this list: {', '.join(ALLOWED_CLASSES)}. "
        "4. 'quirky_text': Write one short, humorous line (meme caption or quote) based on the subject. "
        "5. 'lore': Write 1-3 short sentences of absurd fictional RPG-style lore related to the object. "
        "Return ONLY a valid JSON object matching these 5 keys exactly."
    )

    try:
        client = _client()
        if client is None:
            return FALLBACK_DATA.copy()
        chat_completion = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            max_tokens=300,
            response_format={"type": "json_object"},
            timeout=15
        )

        content = chat_completion.choices[0].message.content
        parsed_metadata = _validate_metadata(json.loads(content))
        if parsed_metadata is None:
            logger.warning("AI metadata rejected: response failed schema validation")
            return FALLBACK_DATA.copy()
        return parsed_metadata
    except AuthenticationError:
        logger.error("AI metadata failed: Groq authentication rejected the API key")
    except BadRequestError as error:
        _log_bad_request(error)
    except RateLimitError:
        logger.warning("AI metadata failed: Groq rate limit exceeded")
    except APIConnectionError:
        logger.warning("AI metadata failed: could not reach Groq")
    except APIStatusError as error:
        logger.error("AI metadata failed: Groq returned HTTP %s", error.status_code)
    except (json.JSONDecodeError, TypeError, AttributeError):
        logger.warning("AI metadata failed: response was not valid JSON")
    except (OSError, ValueError):
        logger.warning("AI metadata failed: image could not be encoded")
    return FALLBACK_DATA.copy()
