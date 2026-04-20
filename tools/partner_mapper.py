import json
import os

from tools.fuzzy_matcher import best_token_match, normalize

PARTNER_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "partner_mapping.json")
FUZZY_THRESHOLD = 75


def _load() -> list[dict]:
    with open(PARTNER_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def _is_exact_alias_match(text: str, alias: str) -> bool:
    text_normalized = normalize(text)
    alias_normalized = normalize(alias)
    if not text_normalized or not alias_normalized:
        return False
    if text_normalized == alias_normalized:
        return True
    return alias_normalized in text_normalized.split(" ")


def find_partner(text: str) -> str | None:
    text_raw = str(text).strip()
    mapping = _load()

    for entry in mapping:
        for alias in entry.get("aliases", []):
            if _is_exact_alias_match(text_raw, alias):
                return entry.get("canonical")

    best_canonical = None
    best_score = 0
    for entry in mapping:
        for alias in entry.get("aliases", []):
            score = best_token_match(text_raw, alias)
            if score > best_score:
                best_score = score
                best_canonical = entry.get("canonical")

    if best_canonical and best_score >= FUZZY_THRESHOLD:
        print(f"UNMATCHED (Mapping fehlt): {text_raw}")
        print(f"Fuzzy Partner: {text_raw} -> {best_canonical} | Score: {best_score}")
        return best_canonical

    return None


def get_kategorie(canonical: str) -> str | None:
    for entry in _load():
        if entry.get("canonical") == canonical:
            return entry.get("kategorie")
    return None
