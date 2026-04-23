from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import pandas as pd

from tools.mieter_matcher import run as run_mieter_matcher
from tools.partner_matcher import run as run_partner_matcher


class DatenimportAgent:
    def _resolve_input_path(self, file_path: str) -> Path:
        candidate = Path(file_path)
        if candidate.exists():
            return candidate

        raw_dir = Path("data") / "raw"
        if raw_dir.exists():
            fallback = raw_dir / Path(file_path).name
            if fallback.exists():
                return fallback

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
        df.columns = df.columns.str.strip()

        column_map = {
            "Datum": "datum",
            "Buchungstext": "buchungstext",
            "Betrag": "betrag",
            "Währung": "waehrung",
            "Sollkonto": "sollkonto",
            "Habenkonto": "habenkonto",
            "Steuerschlüssel": "steuerschluessel",
            "Buchungsnummer": "buchungsnummer",
            "Rechnungsnummern": "rechnungsnummern",
            "Gegenpartei": "gegenpartei",
            "Umsatzsteuer": "umsatzsteuer",
            "Zugewiesene Beträge": "zugewiesene_betraege",
            "Beleglinks": "beleglinks",
            "Festschreibung": "festschreibung",
            "Kommentar": "kommentar",
            "Kostenstelle": "kostenstelle",
            "Kostenstelle 2": "kostenstelle_2",
            "Beleg-Dateinamen": "beleg_dateinamen",
            "Leistungsdatum": "leistungsdatum",
            "Datum Zuordnung Steuerperiode": "datum_steuerperiode",
        }
        df = df.rename(columns=column_map)

        if "datum" in df.columns:
            df["datum"] = pd.to_datetime(df["datum"], errors="coerce", dayfirst=True)
        if "betrag" in df.columns:
            df["betrag"] = (
                df["betrag"]
                .astype(str)
                .str.replace(".", "", regex=False)
                .str.replace(",", ".", regex=False)
            )
            df["betrag"] = pd.to_numeric(df["betrag"], errors="coerce")
        if "sollkonto" in df.columns:
            df["sollkonto"] = pd.to_numeric(df["sollkonto"], errors="coerce")
        if "habenkonto" in df.columns:
            df["habenkonto"] = pd.to_numeric(df["habenkonto"], errors="coerce")

        # Existing matching pipeline: mieter first, partner second.
        df = run_mieter_matcher(df)
        df = run_partner_matcher(df)

        output_dir = Path("data/processed")
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{datetime.today().strftime('%Y-%m-%d')}_buchhaltung_processed.csv"
        output_path = output_dir / filename
        df.to_csv(output_path, index=False)

        return {
            "text": f"Import abgeschlossen. Datei gespeichert unter: {output_path}",
            "table": df.head(50),
        }
