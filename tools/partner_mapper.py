import csv
import json
import os

from tools.fuzzy_matcher import best_token_match, normalize

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "config")
PARTNER_PATH = os.path.join(CONFIG_DIR, "partner_mapping.json")
PARTNER_ID_CSV_PATH = os.path.join(CONFIG_DIR, "partner_mapping.csv")
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


def get_partner_ids(canonical: str) -> list[int]:
    canonical_normalized = normalize(canonical)
    if not canonical_normalized:
        return []

    if os.path.exists(PARTNER_ID_CSV_PATH):
        partner_ids: list[int] = []
        with open(PARTNER_ID_CSV_PATH, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                partner = normalize(row.get("partner", ""))
                if partner == canonical_normalized:
                    try:
                        partner_ids.append(int(row.get("partnerid")))
                    except (TypeError, ValueError):
                        continue
        return partner_ids

    partner_ids: list[int] = []
    for entry in _load():
        if normalize(entry.get("canonical", "")) != canonical_normalized:
            continue
        for partner_id in entry.get("partnerids", []):
            try:
                partner_ids.append(int(partner_id))
            except (TypeError, ValueError):
                continue
        if entry.get("partnerid") is not None:
            try:
                partner_ids.append(int(entry.get("partnerid")))
            except (TypeError, ValueError):
                pass
    return partner_ids


def get_kategorie(canonical: str) -> str | None:
    for entry in _load():
        if entry.get("canonical") == canonical:
            return entry.get("kategorie")
    return None
