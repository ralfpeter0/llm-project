import json
import os

MAPPING_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "konto_mapping.json")
FAQ_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "faq_interpretation.json")


def _load_mapping() -> dict:
    with open(MAPPING_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def _load_faq() -> dict:
    with open(FAQ_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def map_konten(konto_zweck: str) -> list[int]:
    if not konto_zweck:
        return []

    zweck = konto_zweck.strip().lower()
    mapping = _load_mapping()
    faq = _load_faq()
    treffer: set[int] = set()

    for faq_key, faq_entry in faq.items():
        synonyme = [s.lower() for s in faq_entry.get("synonyme", [])]
        if zweck in synonyme or zweck == faq_key.lower():
            konten_val = faq_entry.get("konten")
            if isinstance(konten_val, list):
                treffer.update(int(k) for k in konten_val)
            elif isinstance(konten_val, str) and konten_val.startswith("alle_"):
                kat = konten_val.replace("alle_", "")
                for konto, info in mapping.items():
                    if info.get("kategorie", "").lower() == kat.lower():
                        treffer.add(int(konto))

            varianten = faq_entry.get("varianten", {})
            standard = faq_entry.get("standard")
            for name, variante in varianten.items():
                trigger_match = any(t.lower() in zweck for t in variante.get("trigger", []))
                konten = variante.get("konten", [])
                if not isinstance(konten, list):
                    continue
                if standard and name == standard:
                    treffer.update(int(k) for k in konten)
                elif trigger_match:
                    treffer.update(int(k) for k in konten)

    if treffer:
        return sorted(treffer)

    for konto, info in mapping.items():
        kw = info.get("zweck", "").lower()
        if zweck in kw or kw in zweck:
            treffer.add(int(konto))

    if treffer:
        return sorted(treffer)

    for konto, info in mapping.items():
        if info.get("kategorie", "").lower() == zweck:
            treffer.add(int(konto))

    return sorted(treffer)


def get_alle_konten_by_kategorie(kategorie: str) -> list[int]:
    mapping = _load_mapping()
    return sorted(
        int(k) for k, info in mapping.items() if info.get("kategorie", "").lower() == kategorie.lower()
    )


def get_konto_info(konto: int) -> dict:
    mapping = _load_mapping()
    return mapping.get(str(konto), {})
