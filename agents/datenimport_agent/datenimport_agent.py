import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

import pandas as pd

from datenimport_agent.tools.mieter_matcher import match_mieter
from datenimport_agent.tools.normalizer import normalize_column_names, normalize_buchungstext, REQUIRED_COLUMNS
from datenimport_agent.tools.partner_matcher import match_partner


class DatenimportAgent:
    def _resolve_input_path(self, file_path: str) -> Path:
        candidate = Path(file_path)
        if candidate.exists():
            return candidate

        # tolerate minor naming differences from caller by matching in datain/
        datain = Path("data") / "datain"
        if datain.exists():
            needle = Path(file_path).name.replace(" ", "")
            for item in datain.glob("*.csv"):
                if item.name.replace(" ", "") == needle:
                    return item

        raise FileNotFoundError(f"Input file not found: {file_path}")

    def _load_csv(self, path: Path) -> pd.DataFrame:
        try:
            return pd.read_csv(path, sep=";", encoding="utf-8", encoding_errors="replace")
        except Exception:
            return pd.read_csv(path, sep=";", encoding="latin-1")

    def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        file_path = input.get("file_path")
        if not file_path:
            raise ValueError("input.file_path is required")

        input_path = self._resolve_input_path(file_path)
        df = self._load_csv(input_path)

        # 1) normalize headers and text
        df = normalize_column_names(df)
        df = normalize_buchungstext(df)

        # 2) enforce critical column cleanup
        if "Kostenstelle 2" in df.columns:
            df = df.drop(columns=["Kostenstelle 2"])

        missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            raise ValueError(f"Pflichtspalten fehlen: {missing}")

        df = df[REQUIRED_COLUMNS].copy()  # exact order incl. Buchungsnummer last

        # Pflichtfeld: Buchungsnummer
        if df["Buchungsnummer"].isna().any() or (df["Buchungsnummer"].astype(str).str.strip() == "").any():
            raise ValueError("Pflichtspalte Buchungsnummer enthält leere Werte")

        # 3) datatype conversions
        df["Betrag"] = (
            df["Betrag"].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
        )
        df["Betrag"] = pd.to_numeric(df["Betrag"], errors="raise")

        df["Datum"] = pd.to_datetime(df["Datum"], format="mixed", dayfirst=True, errors="raise")
        df["Sollkonto"] = pd.to_numeric(df["Sollkonto"], errors="raise").astype("Int64")
        df["Habenkonto"] = pd.to_numeric(df["Habenkonto"], errors="raise").astype("Int64")

        df["Kostenstelle"] = df["Kostenstelle"].astype("string").str.strip()
        df["Kostenstelle"] = df["Kostenstelle"].replace("", pd.NA)
        df["Buchungsnummer"] = df["Buchungsnummer"].astype(str).str.strip()

        # 4) matching pipeline - mieter first, then partner only for unmatched
        df = match_mieter(df, "data/mietmatrix.csv")
        df = match_partner(df, "datenimport_agent/config/partner_mapping.csv")

        # 5) output
        today = datetime.today().strftime("%y%m%d")
        filename = f"{today}_norm_buchhaltung.csv"
        output_rel = os.path.join("data", filename)
        output_abs = Path(output_rel)
        output_abs.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_abs, sep=";", index=False)

        return {
            "status": "success",
            "rows": int(len(df)),
            "output_file": output_rel,
            "preview": df.head(10).to_dict(orient="records"),
        }
