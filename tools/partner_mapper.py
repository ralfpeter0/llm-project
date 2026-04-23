import json
import os
from pathlib import Path

import pandas as pd

from tools.fuzzy_matcher import best_token_match, normalize

ROOT = Path(__file__).resolve().parents[1]
PARTNER_PATH = ROOT / "config" / "partner_mapping.json"
DATA_DIR = ROOT / "data" / "processed"
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


def _get_latest_file() -> Path | None:
    if not DATA_DIR.exists():
        return None
    files = list(DATA_DIR.glob("*.csv"))
    if not files:
        return None
    return max(files, key=lambda file: file.stat().st_mtime)


def get_partnerids(name: str) -> list[int]:
    file_path = _get_latest_file()
    if not file_path or not os.path.exists(file_path):
        return []

    df = pd.read_csv(file_path)
    if "buchungstext" not in df.columns or "partnerid" not in df.columns:
        return []

    matches = df[df["buchungstext"].astype(str).str.contains(str(name), case=False, na=False)]
    partnerids = pd.to_numeric(matches["partnerid"], errors="coerce").dropna().astype(int).unique().tolist()

    print(f"Partner-Suche: {name}")
    print(f"PartnerIDs: {partnerids}")

    return partnerids
