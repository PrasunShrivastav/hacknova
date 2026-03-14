"""Explain API — re-explain any text at different complexity levels."""

from fastapi import APIRouter
from pydantic import BaseModel
from llm_client import call_gemini
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["explain"])


class ExplainRequest(BaseModel):
    text: str
    level: str = "undergrad"  # "phd" | "undergrad" | "highschool" | "child"


LEVEL_INSTRUCTIONS = {
    "phd": "Explain for a PhD researcher in a different field. Use technical terms but define domain-specific jargon.",
    "undergrad": "Explain for a college student. Avoid heavy jargon. Use analogies.",
    "highschool": "Explain for a smart high schooler. Simple words, relatable examples.",
    "child": "Explain like the person is 10 years old. Use a fun story or toy analogy.",
}


@router.post("/explain")
async def explain_text(req: ExplainRequest):
    """Re-explain any text at the chosen complexity level."""
    instruction = LEVEL_INSTRUCTIONS.get(req.level, LEVEL_INSTRUCTIONS["undergrad"])

    prompt = f"""{instruction}

Text to explain:
{req.text[:1500]}

Write your explanation (3-4 sentences max):"""

    logger.info(f"Explain request: level={req.level}, text_len={len(req.text)}")
    explanation = call_gemini(prompt)

    return {"explanation": explanation, "level": req.level}
