"""Local LLM client via Ollama with retry logic."""

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
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:4b")

# Track last call time
_last_call_ts: float = 0.0


def call_gemini(prompt: str, json_mode: bool = False) -> str:
    """Call local Ollama model with retry logic.

    Function name kept as call_gemini to avoid changing all callers.

    Args:
        prompt: The prompt to send.
        json_mode: If True, appends an instruction to respond only with JSON.

    Returns:
        The model's text response.
    """
    global _last_call_ts

    if json_mode:
        prompt = prompt + "\n\nRespond ONLY with valid JSON. No markdown, no explanation, no code fences."

    for attempt in range(4):
        # Small delay between calls to be gentle on local resources
        elapsed = time.time() - _last_call_ts
        if elapsed < 0.5:
            time.sleep(0.5 - elapsed)

        try:
            _last_call_ts = time.time()
            response = httpx.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_ctx": 8192,
                    },
                },
                timeout=300.0,
            )
            response.raise_for_status()
            text = response.json()["response"].strip()

            # Strip markdown code fences if present
            if json_mode:
                text = _strip_code_fences(text)
            return text
        except httpx.ConnectError:
            logger.error(
                "Cannot connect to Ollama. Is it running? Start with: ollama serve"
            )
            raise RuntimeError(
                "Ollama is not running. Start it with: ollama serve"
            )
        except Exception as e:
            logger.warning(f"Ollama error (attempt {attempt+1}): {e}")
            if attempt < 3:
                time.sleep(2)
            else:
                raise e

    raise Exception("Ollama request failed after 4 retries")


def _strip_code_fences(text: str) -> str:
    """Remove ```json ... ``` wrappers from LLM output."""
    text = text.strip()
    pattern = r"^```(?:json)?\s*\n?(.*?)\n?\s*```$"
    match = re.match(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text
