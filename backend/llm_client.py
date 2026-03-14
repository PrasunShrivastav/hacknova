"""Two-tier LLM client via Ollama — fast model for extraction, heavy model for reasoning."""

import httpx
import os
import time
import logging
import re
import json

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Configure Ollama
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL_HEAVY = os.getenv("OLLAMA_MODEL", "gemma3:12b")
OLLAMA_MODEL_FAST = os.getenv("OLLAMA_MODEL_FAST", "gemma3:1b")

_last_call_ts: float = 0.0


def _call_ollama(prompt: str, model: str, json_mode: bool = False,
                 max_tokens: int = 800, timeout: float = 300.0) -> str:
    """Internal: call Ollama with specified model."""
    global _last_call_ts

    if json_mode:
        prompt = prompt + "\n\nRespond ONLY with valid JSON. No markdown, no explanation, no code fences."

    for attempt in range(3):
        elapsed = time.time() - _last_call_ts
        if elapsed < 0.3:
            time.sleep(0.3 - elapsed)

        try:
            _last_call_ts = time.time()
            response = httpx.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                headers={
                    "ngrok-skip-browser-warning": "true",  # Bypass ngrok 403 interstitial
                },
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2 if model == OLLAMA_MODEL_HEAVY else 0.1,
                        "num_ctx": 8192 if model == OLLAMA_MODEL_HEAVY else 4096,
                        "num_predict": max_tokens,
                    },
                },
                timeout=timeout,
            )
            response.raise_for_status()
            text = response.json()["response"].strip()

            if json_mode:
                text = _strip_code_fences(text)
            return text
        except httpx.ConnectError:
            logger.error("Cannot connect to Ollama. Start with: ollama serve")
            raise RuntimeError("Ollama is not running. Start it with: ollama serve")
        except Exception as e:
            logger.warning(f"Ollama {model} error (attempt {attempt+1}): {e}")
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
            else:
                raise e

    return "{}" if json_mode else ""


# ── TIER 1: Heavy model (gemma3:12b) ──────────────────────────
# Use for: synthesis, contradiction detection, gap analysis, chat, explain, roadmap
def call_gemini(prompt: str, json_mode: bool = False) -> str:
    """Call heavy model for reasoning tasks. Name kept for backward compat."""
    return _call_ollama(prompt, OLLAMA_MODEL_HEAVY, json_mode=json_mode,
                        max_tokens=800, timeout=300.0)


# ── TIER 2: Fast model (gemma3:1b) ────────────────────────────
# Use for: paper extraction, keyword tagging, classification
# ~6-8x faster than 12b
def call_gemma_fast(prompt: str, json_mode: bool = False) -> str:
    """Call fast model for structured extraction tasks."""
    return _call_ollama(prompt, OLLAMA_MODEL_FAST, json_mode=json_mode,
                        max_tokens=400, timeout=60.0)


def _strip_code_fences(text: str) -> str:
    """Remove ```json ... ``` wrappers from LLM output."""
    text = text.strip()
    pattern = r"^```(?:json)?\s*\n?(.*?)\n?\s*```$"
    match = re.match(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text
