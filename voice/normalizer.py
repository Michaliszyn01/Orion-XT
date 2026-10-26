import re

from core.utils import normalize_text


PHRASE_REPLACEMENTS = {
    "moutro oreo": "modo orion",
    "outro oreo": "modo orion",
    "mado orion": "modo orion",
    "moto orion": "modo orion",
    "modo audio": "modo orion",
    "modo oreo": "modo orion",
    "macho ario modo audio": "modo orion",
}

WORD_REPLACEMENTS = {
    "gugou": "google",
    "iutube": "youtube",
    "yutube": "youtube",
    "giti rab": "github",
    "git rab": "github",
    "lura": "alura",
}


def _basic_normalize(text: str) -> str:
    return normalize_text(text)


def normalize_voice_text(text: str) -> str:
    original = text or ""
    normalized = _basic_normalize(original)

    for wrong, correct in PHRASE_REPLACEMENTS.items():
        if wrong in normalized:
            normalized = normalized.replace(wrong, correct)

    for wrong, correct in WORD_REPLACEMENTS.items():
        normalized = re.sub(rf"\b{re.escape(wrong)}\b", correct, normalized)

    return normalized.strip()
