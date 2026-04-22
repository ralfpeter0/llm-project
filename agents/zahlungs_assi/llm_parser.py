import re
from typing import Optional


DEFAULT_RESULT = {
    "intent": "zahlung",
    "rolle": None,
    "name": None,
    "konto_zweck": None,
    "jahr": None,
}

PARTNER_KEYWORDS = {
    "gmbh",
    "ag",
    "kg",
    "ug",
    "ohg",
    "e.v",
    "ev",
    "hausmeister",
    "service",
    "reinigung",
    "clean",
    "strom",
    "wasser",
    "energie",
    "werke",
    "versicherung",
    "telefon",
    "internet",
    "handwerker",
}

STOPWORDS = {
    "was",
    "hat",
    "habe",
    "ich",
    "wir",
    "an",
    "im",
    "in",
    "für",
    "fuer",
    "bezahlt",
    "gezahlt",
    "zahlung",
    "zahlungen",
    "der",
    "die",
    "das",
    "den",
    "dem",
    "des",
    "und",
    "von",
}


def _extract_year(text: str) -> Optional[int]:
    match = re.search(r"\b(19|20)\d{2}\b", text)
    return int(match.group()) if match else None


def _extract_konto_zweck(text: str) -> Optional[str]:
    if re.search(r"\b(nebenkosten|bk)\b", text):
        return "nebenkosten"
    if re.search(r"\bmiete\b", text):
        return "miete"
    return None


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _extract_name(text: str) -> Optional[str]:
    patterns = [
        r"\bhat\s+([\wäöüÄÖÜß&.\- ]+?)\s+\d{4}\b",
        r"\bhabe\s+ich\s+\d{4}\s+an\s+([\wäöüÄÖÜß&.\- ]+?)\s+bezahlt\b",
        r"\bich\s+\d{4}\s+an\s+([\wäöüÄÖÜß&.\- ]+?)\s+bezahlt\b",
        r"\ban\s+([\wäöüÄÖÜß&.\- ]+?)\s+bezahlt\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            candidate = _normalize_whitespace(match.group(1).strip(" ?!.,"))
            if candidate:
                return candidate

    words = [w for w in re.findall(r"[\wäöüÄÖÜß&.\-]+", text) if w not in STOPWORDS and not re.fullmatch(r"\d{4}", w)]
    return words[0] if words else None


def _detect_role(text: str, name: Optional[str]) -> str:
    if re.search(r"\b(ich|wir|mein|meine|unser|unsere)\b", text):
        return "partner"

    candidate = (name or "").lower()
    candidate_tokens = set(re.findall(r"[a-zäöüß.&\-]+", candidate))

    if any(keyword in candidate_tokens or keyword in candidate for keyword in PARTNER_KEYWORDS):
        return "partner"

    return "mieter"


def parse_query(user_input: str) -> dict:
    text = _normalize_whitespace(user_input.lower())

    result = dict(DEFAULT_RESULT)
    result["jahr"] = _extract_year(text)
    result["konto_zweck"] = _extract_konto_zweck(text)
    result["name"] = _extract_name(text)
    result["rolle"] = _detect_role(text, result["name"])

    return result
