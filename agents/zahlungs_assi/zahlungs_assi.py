from pathlib import Path

import pandas as pd

from agents.zahlungs_assi.llm_parser import create_plan
from tools.konto_mapper import map_konten
from tools.mieter_mapper import get_vertragids
from tools.zeitraum_tool import get_zeitraum
from tools.zahlung_tool import filter_zahlungen, summe_zahlungen

ROOT = Path(__file__).resolve().parents[2]


class ZahlungsAssi:
    def __init__(self, csv_path: Path | None = None):
        self.csv_path = csv_path or (ROOT / "data" / "processed" / "2026-04-22_buchhaltung_processed.csv")

    def run(self, user_input: str) -> dict:
        plan = create_plan(user_input)
        print("PLAN:", plan)

        name = plan.get("name")
        if not name:
            return {"summe": 0.0, "anzahl": 0, "daten": pd.DataFrame(), "context": {"plan": plan}}

        vertragids = get_vertragids(name)
        konten = map_konten(plan.get("konto_zweck"))
        zeitraum = get_zeitraum(plan.get("jahr"))

        buchungen = filter_zahlungen(
            vertragids=vertragids,
            konten=konten,
            von=zeitraum.get("von"),
            bis=zeitraum.get("bis"),
        )

        return {
            "summe": float(summe_zahlungen(buchungen)),
            "anzahl": len(buchungen),
            "daten": pd.DataFrame(buchungen),
            "context": {
                "plan": plan,
                "vertragids": vertragids,
                "konten": konten,
                "zeitraum": zeitraum,
            },
        }
