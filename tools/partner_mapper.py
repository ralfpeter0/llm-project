import csv
import os

from tools.fuzzy_matcher import normalize

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "config")
PARTNER_CSV_PATH = os.path.join(CONFIG_DIR, "partner_mapping.csv")


def load_partner_mapping() -> list[dict[str, str]]:
    mapping: list[dict[str, str]] = []
    with open(PARTNER_CSV_PATH, "r", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        for row in reader:
            normalized_row: dict[str, str] = {}
            for key, value in row.items():
                normalized_key = (key or "").strip().lower()
                normalized_value = normalize(value or "")
                normalized_row[normalized_key] = normalized_value
            mapping.append(normalized_row)
    return mapping


def _extract_aliases(row: dict[str, str]) -> list[str]:
    aliases_raw = row.get("aliases", "")
    if not aliases_raw:
        return []
    aliases_text = aliases_raw.replace(";", ",")
    aliases = [normalize(alias) for alias in aliases_text.split(",")]
    return [alias for alias in aliases if alias]


# 🔥 HIER IST DER FIX
def _contains_match(normalized_text: str, candidate: str) -> bool:
    if not candidate:
        return False

    # ✅ Richtige Richtung
    if normalized_text in candidate:
        return True

    # optional robust gegen Varianten
    for token in candidate.split():
        if len(token) >= 3 and token in normalized_text:
            return True

    return False


def find_partner(text: str) -> str | None:
    normalized_text = normalize(text)
    if not normalized_text:
        return None

    mapping = load_partner_mapping()

    for row in mapping:
        canonical = row.get("partner", "")

        # direkt match auf canonical
        if _contains_match(normalized_text, canonical):
            return canonical

        # alias match
        for alias in _extract_aliases(row):
            if _contains_match(normalized_text, alias):
                return canonical or None

    return None


def get_partner_ids(canonical: str) -> list[int]:
    canonical_normalized = normalize(canonical)
    if not canonical_normalized:
        return []

    partner_ids: list[int] = []
    mapping = load_partner_mapping()

    for row in mapping:
        if normalize(row.get("partner", "")) != canonical_normalized:
            continue

        try:
            partner_ids.append(int(row.get("partnerid", "")))
        except (TypeError, ValueError):
            continue

    return list(set(partner_ids))


def get_kategorie(canonical: str) -> str | None:
    canonical_normalized = normalize(canonical)
    if not canonical_normalized:
        return None

    mapping = load_partner_mapping()

    for row in mapping:
        if normalize(row.get("partner", "")) == canonical_normalized:
            kategorie = row.get("kategorie", "")
            return kategorie or None

    return None
