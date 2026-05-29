"""
Finguard_rag/generation/gemini_client.py
Amala P Ansalem — M5: Gemini 1.5 Flash API Wrapper

Wraps the google-generativeai SDK to call Gemini 1.5 Flash.
Falls back to Groq (Llama 3 70B) when USE_GROQ_FALLBACK=true or
if the Gemini call fails.

All configuration is read from config.yaml and .env.
"""

import os
import sys
import logging
from pathlib import Path

import yaml
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Resolve repo root so imports work regardless of working directory
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Load .env from repo root
load_dotenv(dotenv_path=_REPO_ROOT / ".env")

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Load config.yaml once at module level
# ---------------------------------------------------------------------------
_CONFIG_PATH = _REPO_ROOT / "config.yaml"

def _load_config() -> dict:
    """Load and return the full config dict from config.yaml."""
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    # Sensible defaults if config.yaml is missing
    return {
        "llm": {
            "provider": "gemini",
            "model_name": "gemini-2.0-flash-lite",
            "temperature": 0.3,
            "max_tokens": 2048,
            "timeout_seconds": 30,
        }
    }

_CFG = _load_config()
_LLM_CFG = _CFG.get("llm", {})

# ---------------------------------------------------------------------------
# Gemini client
# ---------------------------------------------------------------------------
def _call_gemini(prompt: str) -> str:
    """
    Call Google Gemini 1.5 Flash via the google-generativeai SDK.

    Returns:
        Raw text response from the model.

    Raises:
        RuntimeError: If the API key is missing or the call fails.
    """
    import google.generativeai as genai

    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or api_key == "your_key_here":
        raise RuntimeError(
            "GEMINI_API_KEY not set. Get a free key at https://aistudio.google.com"
        )

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(_LLM_CFG.get("model_name", "gemini-2.0-flash-lite"))

    generation_config = genai.types.GenerationConfig(
        temperature=_LLM_CFG.get("temperature", 0.3),
        max_output_tokens=_LLM_CFG.get("max_tokens", 2048),
    )

    response = model.generate_content(
        prompt,
        generation_config=generation_config,
    )

    # Gemini may return empty if safety filters fire
    if not response.text:
        logger.warning("Gemini returned an empty response (safety filter?)")
        return "[FinGuard: Gemini safety filter blocked the response. Please rephrase your query.]"

    return response.text


# ---------------------------------------------------------------------------
# Groq fallback client
# ---------------------------------------------------------------------------
def _call_groq(prompt: str) -> str:
    """
    Call Groq API (Llama 3 70B) as a fallback LLM.

    Returns:
        Raw text response from the model.

    Raises:
        RuntimeError: If the GROQ_API_KEY is missing or the call fails.
    """
    from groq import Groq

    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY not set. Get a free key at https://console.groq.com"
        )

    client = Groq(api_key=api_key)
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        temperature=_LLM_CFG.get("temperature", 0.3),
        max_tokens=_LLM_CFG.get("max_tokens", 2048),
    )

    result = chat_completion.choices[0].message.content
    import time
    time.sleep(2)  # rate-limit guard for Groq free tier
    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
_MOCK_RESPONSE = (
    "Under SEBI LODR Regulation 30 (2015, as amended by Master Circular 2023), "
    "listed entities must disclose material events to the stock exchanges within "
    "24 hours of occurrence or within 30 minutes for certain events specified in "
    "Part A of Schedule III. The compliance officer is responsible for determining "
    "materiality and ensuring timely disclosure. "
    "[Source: SEBI-LODR-2015-REG30] [Source: SEBI-MC-LODR-2023]"
)


def call_llm(prompt: str, mock_mode: bool = False) -> str:
    """
    Send a prompt to the configured LLM and return the raw text response.

    Tries Gemini first.  If USE_GROQ_FALLBACK is set or Gemini fails,
    falls back to Groq.

    Args:
        prompt:     The fully-assembled prompt string.
        mock_mode:  If True, return a canned response without any API call.

    Returns:
        Raw response text from the LLM.
    """
    if mock_mode:
        logger.info("LLM call — mock_mode=True, returning canned response")
        return _MOCK_RESPONSE

    use_groq = os.getenv("USE_GROQ_FALLBACK", "false").lower() == "true"

    if use_groq:
        logger.info("Using Groq (Llama 3 70B) as primary LLM")
        return _call_groq(prompt)

    # Default: try Gemini, fall back to Groq on failure
    try:
        logger.info("Calling Gemini 1.5 Flash …")
        return _call_gemini(prompt)
    except Exception as e:
        logger.warning("Gemini call failed (%s) — falling back to Groq", e)
        try:
            return _call_groq(prompt)
        except Exception as groq_err:
            raise RuntimeError(
                f"Both Gemini and Groq failed.  Gemini: {e}  |  Groq: {groq_err}"
            ) from groq_err
