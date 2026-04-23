from pathlib import Path

import pandas as pd

from agents.zahlungs_assi.llm_parser import create_plan
from tools.konto_mapper import map_konten
from tools.mieter_mapper import get_vertragids
from tools.partner_mapper import get_partnerids
from tools.zahlung_tool import zahlung_tool
from tools.zeitraum_tool import get_zeitraum

ROOT = Path(__file__).resolve().parents[2]


class ZahlungsAssi:
    def __init__(self, csv_path: Path | None = None):
        self.csv_path = csv_path or self._find_latest_csv()

    def _find_latest_csv(self) -> Path:
        processed_dir = ROOT / "data" / "processed"
        candidates = list(processed_dir.glob("*_buchhaltung_processed.csv"))

        if not candidates:
            raise FileNotFoundError("No processed CSV file found in data/processed")

        return max(candidates, key=lambda path: path.stat().st_mtime)

    def run(self, user_input: str) -> dict:
        plan = create_plan(user_input)
        print("PLAN:", plan)

        rolle = plan.get("rolle")
        name = plan.get("name")

        vertragids = None
        partnerids = None

        if rolle == "mieter" and name:
            vertragids = get_vertragids(name)

        if rolle == "partner" and name:
            partnerids = get_partnerids(name)

        konten = map_konten(plan.get("konto_zweck"))
        zeitraum = get_zeitraum(plan.get("jahr"))

        print("Using data file:", self.csv_path)
        df = pd.read_csv(self.csv_path, parse_dates=["datum"])

        result = zahlung_tool(
            df=df,
            vertragids=vertragids,
            partnerids=partnerids,
            konten=konten,
            von=zeitraum.get("von"),
            bis=zeitraum.get("bis"),
            operation=plan.get("operation"),
        )

        return {
            "result": result,
            "context": {
                "plan": plan,
                "vertragids": vertragids,
                "partnerids": partnerids,
                "konten": konten,
                "zeitraum": zeitraum,
            },
        }
