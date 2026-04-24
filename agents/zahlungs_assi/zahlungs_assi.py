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

        # 2. Initialisierung
        vertragsids = None
        partnerids = None

        name = plan.get("name")
        role = plan.get("rolle")

        # 3. Mapping strikt trennen
        if role == "mieter" and name:
            vertragsids = match_mieter(name)

        elif name:
            canonical = pm.find_partner(name)
            partnerids = pm.get_partner_ids(canonical) if canonical else None
            print("DEBUG canonical:", canonical)
            print("DEBUG partnerids:", partnerids)

        # 4. Weitere Filter
        konten = map_konten(plan.get("konto_zweck"))
        zeitraum = get_zeitraum(plan.get("jahr"))

        # 5. Tool-Aufruf
        result = zahlung_tool(
            vertragids=vertragsids,        # ⚠️ wichtig: ohne "s"
            partnerids=partnerids,
            konten=konten,
            von=zeitraum.get("von"),
            bis=zeitraum.get("bis"),
            operation=plan.get("operation", "summe"),
            richtung=plan.get("richtung"),
            buchungstext=plan.get("buchungstext"),
        )

        return result