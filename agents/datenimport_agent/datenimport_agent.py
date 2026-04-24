from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import pandas as pd

from tools.mieter_matcher import run as run_mieter_matcher
from tools.partner_matcher import run as run_partner_matcher


class DatenimportAgent:
    def _parse_betrag(self, series: pd.Series) -> pd.Series:
        cleaned = series.astype(str).str.strip()
        has_comma = cleaned.str.contains(",", na=False)

        cleaned_with_german_decimal = (
            cleaned.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
        )
        cleaned = cleaned.where(~has_comma, cleaned_with_german_decimal)

        return pd.to_numeric(cleaned, errors="coerce")

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
        df.columns = df.columns.str.strip().str.lower()

        column_map = {
            "datum": "datum",
            "buchungstext": "buchungstext",
            "betrag": "betrag",
            "währung": "waehrung",
            "sollkonto": "sollkonto",
            "habenkonto": "habenkonto",
            "steuerschlüssel": "steuerschluessel",
            "buchungsnummer": "buchungsnummer",
            "rechnungsnummern": "rechnungsnummern",
            "gegenpartei": "gegenpartei",
            "umsatzsteuer": "umsatzsteuer",
            "zugewiesene beträge": "zugewiesene_betraege",
            "beleglinks": "beleglinks",
            "festschreibung": "festschreibung",
            "kommentar": "kommentar",
            "kostenstelle": "kostenstelle",
            "kostenstelle 2": "kostenstelle_2",
            "beleg-dateinamen": "beleg_dateinamen",
            "leistungsdatum": "leistungsdatum",
            "datum zuordnung steuerperiode": "datum_steuerperiode",
        }
        df = df.rename(columns=column_map)

        if "datum" in df.columns:
            df["datum"] = pd.to_datetime(df["datum"], errors="coerce", dayfirst=True)
        if "betrag" in df.columns:
            df["betrag"] = self._parse_betrag(df["betrag"])
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
        if "betrag" in df.columns:
            df["betrag"] = self._parse_betrag(df["betrag"])
        df = df.loc[:, ~df.columns.duplicated()]
        df.to_csv(output_path, index=False)

        return {
            "text": f"Import abgeschlossen. Datei gespeichert unter: {output_path}",
            "table": df.head(50),
        }
