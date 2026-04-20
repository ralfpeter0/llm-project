import re
from difflib import SequenceMatcher


def normalize(text: str) -> str:
    value = str(text or "").lower()
    replacements = {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "ß": "ss",
    }
    for src, dst in replacements.items():
        value = value.replace(src, dst)
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def tokenize(text: str) -> list[str]:
    normalized = normalize(text)
    if not normalized:
        return []
    return normalized.split(" ")


def similarity(a: str, b: str) -> int:
    left = normalize(a)
    right = normalize(b)
    if not left or not right:
        return 0
    return int(round(SequenceMatcher(None, left, right).ratio() * 100))


def best_token_match(user_input: str, candidate: str) -> int:
    input_tokens = tokenize(user_input)
    candidate_tokens = tokenize(candidate)
    if not input_tokens or not candidate_tokens:
        return 0

    best = 0
    for input_token in input_tokens:
        for candidate_token in candidate_tokens:
            score = similarity(input_token, candidate_token)
            if score > best:
                best = score
    return best
