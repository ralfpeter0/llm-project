
from pathlib import Path

from agents.zahlungs_assi.llm_parser import create_plan
from tools.konto_mapper import map_konten
from tools.mieter_mapper import get_vertragsids
from tools.zeitraum_tool import get_zeitraum
from tools.zahlung_tool import zahlung_tool


ROOT = Path(__file__).resolve().parents[2]


class ZahlungsAssi:
    def __init__(self, csv_path: Path | None = None):
        self.csv_path = csv_path or (ROOT / "data" / "processed" / "2026-04-23_buchhaltung_processed.csv")

    def run(self, user_input: str) -> dict:
        # 1. Parser
        plan = create_plan(user_input)
        print("PLAN:", plan)

        # 2. Mapping
        name = plan.get("name")
        vertragsids = get_vertragsids(name) if name else None
        konten = map_konten(plan.get("konto_zweck"))
        zeitraum = get_zeitraum(plan.get("jahr"))

        # 3. Tool-Aufruf
        result = zahlung_tool(
            vertragsids=vertragsids,
            konten=konten,
            von=zeitraum.get("von"),
            bis=zeitraum.get("bis"),
            operation=plan.get("operation", "summe"),
            richtung=plan.get("richtung"),   # ← wichtig
        )

        # 4. Ergebnis zurückgeben
        return result