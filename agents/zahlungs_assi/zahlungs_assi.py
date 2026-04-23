from pathlib import Path

import pandas as pd

from agents.zahlungs_assi.llm_parser import AutonomousZahlungsAgent

ROOT = Path(__file__).resolve().parents[2]


class ZahlungsAssi:
    def __init__(self, csv_path: Path | None = None, model: str = "gpt-4o-mini"):
        self.csv_path = csv_path or (ROOT / "data" / "processed" / "2026-04-22_buchhaltung_processed.csv")
        self.agent = AutonomousZahlungsAgent(model=model)

    def run(self, user_input: str) -> dict:
        result = self.agent.run(user_input)
        daten = result.get("daten", [])

        return {
            "summe": float(result.get("summe", 0.0)),
            "anzahl": int(result.get("anzahl", 0)),
            "daten": pd.DataFrame(daten),
            "context": result.get("context", {}),
        }
