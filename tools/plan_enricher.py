import tools.partner_mapper as pm
from tools.mieter_mapper import match_mieter


def enrich_plan(plan: dict, user_input: str) -> dict:
    text = user_input.lower()

    name = plan.get("name")
    rolle = plan.get("rolle")
    richtung = plan.get("richtung")

    # 1. Name-Fallback: wenn LLM Name nicht erkennt
    if not name and plan.get("buchungstext"):
        name = plan["buchungstext"]
        plan["name"] = name

    # 2. Rolle bestimmen
    if name and (not rolle or rolle == "unknown"):
        try:
            mieter_ids = match_mieter(name)
        except Exception:
            mieter_ids = []

        canonical = pm.find_partner(name)

        if mieter_ids:
            plan["rolle"] = "mieter"
        elif canonical:
            plan["rolle"] = "partner"

    # 3. Richtung bestimmen
    if not richtung or richtung == "unknown":
        if " an " in f" {text} " or "bezahlt" in text or "überwiesen" in text:
            if plan.get("rolle") == "partner":
                plan["richtung"] = "ausgabe"
            elif plan.get("rolle") == "mieter":
                plan["richtung"] = "einnahme"

        if " von " in f" {text} " or "erhalten" in text or "bekommen" in text:
            plan["richtung"] = "einnahme"

    return plan