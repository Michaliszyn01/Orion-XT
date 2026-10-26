import re
import unicodedata


TARGET_ALIASES = {
    "google": ["google", "gugou"],
    "youtube": ["youtube", "iutube", "yutube"],
    "github": ["github", "giti rab", "git hub"],
    "alura": ["alura", "lura"],
    "wikipedia": ["wikipedia"],
    "linkedin": ["linkedin"],
}

SEARCH_WORDS = ["pesquisa", "procura", "busca"]


def normalize_text(text: str) -> str:
    text = (text or "").lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return re.sub(r"\s+", " ", text).strip()


def normalize_target(text: str) -> str:
    text = normalize_text(text)

    mapping = TARGET_ALIASES

    for key, aliases in mapping.items():
        for alias in aliases:
            if alias in text:
                return key

    return ""


def clean_search_query(text: str, target: str = "") -> str:
    query = normalize_text(text)

    last_search_pos = -1
    last_search_word = ""

    for word in SEARCH_WORDS:
        for match in re.finditer(rf"\b{re.escape(word)}\b", query):
            if match.start() > last_search_pos:
                last_search_pos = match.start()
                last_search_word = word

    if last_search_pos >= 0:
        query = query[last_search_pos + len(last_search_word):]

    for word in ["no", "na"]:
        query = re.sub(rf"\b{word}\b", " ", query)

    aliases = TARGET_ALIASES.get(target, [])
    for alias in sorted(aliases, key=len, reverse=True):
        query = re.sub(rf"\b{re.escape(alias)}\b", " ", query)

    query = re.sub(r"\s+", " ", query)
    return query.strip(" .?!,;:-")
