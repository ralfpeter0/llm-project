from pathlib import Path

import pandas as pd

from agents.zahlungs_assi.llm_parser import parse_query
from tools.konto_mapper import map_konten as map_konto
from tools.mieter_mapper import get_vertragids as map_mieter_to_vertragids
from tools.zeitraum_tool import get_zeitraum

ROOT = Path(__file__).resolve().parents[2]


class ZahlungsAssi:
    def __init__(self, csv_path: Path | None = None):
        self.csv_path = csv_path or (ROOT / "data" / "processed" / "2026-04-22_buchhaltung_processed.csv")

    def run(self, user_input: str) -> dict:
        parsed = parse_query(user_input)

        name = parsed["name"]
        jahr = parsed["jahr"]
        konto_zweck = parsed["konto_zweck"]
        rolle = parsed["rolle"]

        vertragids = map_mieter_to_vertragids(name)
        konten = map_konto(konto_zweck)
        zeitraum = get_zeitraum(jahr=jahr)

        print("parsed:", parsed)
        print("name:", name)
        print("konto_zweck:", konto_zweck)
        print("jahr:", jahr)
        print("rolle:", rolle)
        print(f"vertragids: {vertragids}")
        print(f"konten: {konten}")
        print(f"zeitraum: {zeitraum}")

        df = pd.read_csv(self.csv_path)

        required_columns = {"vertragid", "datum", "betrag", "sollkonto", "habenkonto"}
        missing = required_columns.difference(df.columns)
        if missing:
            raise ValueError(f"Fehlende Spalten in CSV: {sorted(missing)}")

        df["vertragid"] = pd.to_numeric(df["vertragid"], errors="coerce")
        df["sollkonto"] = pd.to_numeric(df["sollkonto"], errors="coerce")
        df["habenkonto"] = pd.to_numeric(df["habenkonto"], errors="coerce")
        df["datum"] = pd.to_datetime(df["datum"], errors="coerce")
        df["betrag"] = (
            df["betrag"]
            .astype(str)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
            .astype(float)
        )

        von = pd.to_datetime(zeitraum["von"], errors="coerce")
        bis = pd.to_datetime(zeitraum["bis"], errors="coerce")

        df_result = df[
            df["vertragid"].isin(vertragids)
            & (
                df["sollkonto"].isin(konten)
                | df["habenkonto"].isin(konten)
            )
            & (df["datum"] >= von)
            & (df["datum"] <= bis)
        ].copy()

        print(f"anzahl zeilen: {len(df_result)}")

        return {
            "summe": float(df_result["betrag"].sum()),
            "anzahl": int(len(df_result)),
            "daten": df_result,
        }
