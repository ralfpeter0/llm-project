from pathlib import Path

from agents.zahlungs_assi.llm_parser import create_plan
from tools.konto_mapper import map_konten
from tools.mieter_mapper import match_mieter
import tools.partner_mapper as pm
from tools.zeitraum_tool import get_zeitraum
from tools.zahlung_tool import zahlung_tool


ROOT = Path(__file__).resolve().parents[2]


class ZahlungsAssi:
    def __init__(self, csv_path: Path | None = None):
        self.csv_path = csv_path or (
            ROOT / "data" / "processed" / "2026-04-23_buchhaltung_processed.csv"
        )

    def run(self, user_input: str) -> dict:
        # 1. Parser
        plan = create_plan(user_input)
        print("PLAN:", plan)

        # 2. Partner Mapping (nur wenn rolle = partner)
        partnerids = None
        if plan.get("rolle") == "partner" and plan.get("name"):
            name = plan.get("name")

            if hasattr(pm, "match_partner"):
                partnerids = pm.match_partner(name)
            elif hasattr(pm, "map_partner"):
                partnerids = pm.map_partner(name)
            elif hasattr(pm, "get_partner"):
                partnerids = pm.get_partner(name)
            else:
                partnerids = None

        # 3. Mieter Mapping
        name = plan.get("name")
        vertragsids = match_mieter(name) if name else None

        # 4. Konto Mapping
        konten = map_konten(plan.get("konto_zweck"))

        # 5. Zeitraum
        zeitraum = get_zeitraum(plan.get("jahr"))

        # 6. Tool-Aufruf
        result = zahlung_tool(
            vertragsids=vertragsids,
            partnerids=partnerids,
            konten=konten,
            von=zeitraum.get("von"),
            bis=zeitraum.get("bis"),
            operation=plan.get("operation", "summe"),
            richtung=plan.get("richtung"),
            buchungstext=plan.get("buchungstext"),
        )

        # 7. Ergebnis
        return result
