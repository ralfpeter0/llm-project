import json
from pathlib import Path
from typing import Any

from openai import OpenAI

ROOT = Path(__file__).resolve().parents[2]
KONTO_MAPPING_PATH = ROOT / "config" / "konto_mapping.json"
DEFAULT_MODEL = "gpt-4o-mini"


class AutonomousZahlungsAgent:
    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model
        self.client = OpenAI()
        self.konto_begriffe = self._load_konto_begriffe()

    def _load_konto_begriffe(self) -> list[str]:
        if not KONTO_MAPPING_PATH.exists():
            return []

        with open(KONTO_MAPPING_PATH, "r", encoding="utf-8") as file:
            mapping = json.load(file)

        begriffe = {entry.get("zweck", "").strip() for entry in mapping.values()}
        return sorted(begriff for begriff in begriffe if begriff)

    def build_prompt(self) -> str:
        konto_hinweis = ", ".join(self.konto_begriffe) if self.konto_begriffe else ""

        return (
            "Du bist ein Parser für Zahlungsanfragen in der Immobilienbuchhaltung.\\n"
            "Gib IMMER nur JSON zurück (kein Text außerhalb von JSON).\\n\\n"
            "Erlaubte Felder im Output:\\n"
            "{\\n"
            '  "intent": "zahlung | soll | info | check",\\n'
            '  "operation": "summe | liste | check | null",\\n'
            '  "rolle": "mieter | partner | unknown",\\n'
            '  "name": "string | null",\\n'
            '  "jahr": "integer | null",\\n'
            '  "konto_zweck": "string | null"\\n'
            "}\\n\\n"
            "Regeln:\\n"
            "- intent muss immer gesetzt sein.\\n"
            "- operation darf nur summe, liste, check oder null sein.\\n"
            "- rolle nur mieter, partner oder unknown.\\n"
            "- name ist Person oder Firma, sonst null.\\n"
            "- jahr nur als integer, sonst null.\\n"
            "- konto_zweck nur mit Begriffen aus konto_mapping.json (zweck), sonst null.\\n"
            "- KEIN hardcoding wie kosten/nebenkosten als feste Kategorie.\\n"
            "- KEIN default wie 'always zahlung_mieter'.\\n\\n"
            f"Begriffe aus konto_mapping.json (zweck): {konto_hinweis}\\n\\n"
            "Beispiele:\\n"
            "User: Wie viel hat Flury 2024 für mieteinnahmen wohnung gezahlt?\\n"
            'JSON: {"intent":"zahlung","operation":"summe","rolle":"mieter","name":"Flury","jahr":2024,"konto_zweck":"mieteinnahmen wohnung"}\\n\\n'
            "User: Liste alle SWM Zahlungen 2025 für heizkosten.\\n"
            'JSON: {"intent":"zahlung","operation":"liste","rolle":"partner","name":"SWM","jahr":2025,"konto_zweck":"heizkosten"}\\n\\n'
            "User: Wie hoch waren die heizkosten 2024?\\n"
            'JSON: {"intent":"zahlung","operation":"summe","rolle":"unknown","name":null,"jahr":2024,"konto_zweck":"heizkosten"}\\n\\n'
            "User: Gibt es 2025 Buchungen für SWM bei energie allgemein?\\n"
            'JSON: {"intent":"check","operation":"check","rolle":"partner","name":"SWM","jahr":2025,"konto_zweck":"energie allgemein"}'
        )

    def create_plan(self, query: str) -> dict[str, Any]:
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            messages=[
                {"role": "system", "content": self.build_prompt()},
                {"role": "user", "content": query},
            ],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "{}"
        plan = json.loads(content)
        print(f"PLAN: {plan}")
        return plan

    def run(self, query: str) -> dict[str, Any]:
        return self.create_plan(query)


def parse_query(user_input: str) -> dict[str, Any]:
    agent = AutonomousZahlungsAgent()
    return agent.create_plan(user_input)
