import logging
from dataclasses import dataclass

from api.config import Settings
from narrator.guard import narration_matches_trace
from narrator.llm import Completion, anthropic_completion, narrate_with_llm
from narrator.templates import LANGUAGES, explain
from reasoner.kb import load_kb

logger = logging.getLogger("hakiki.narrator")


@dataclass(frozen=True)
class Narration:
    language: str
    text: str
    source: str


def build_completion(settings: Settings) -> Completion | None:
    return anthropic_completion(settings) if settings.llm_api_key else None


def narrate(result: dict, language: str, complete: Completion | None = None) -> Narration:
    if language not in LANGUAGES:
        raise ValueError("unsupported language")
    if complete is not None:
        try:
            verdict, text = narrate_with_llm(complete, result, language)
            if narration_matches_trace(text, verdict, result):
                return Narration(language, text.strip(), "llm")
            logger.warning("narration discarded: does not match the trace")
        except Exception as exc:
            logger.warning("narration unavailable: %s", type(exc).__name__)
    return Narration(language, explain(load_kb(), result, language), "template")
