import re
from pathlib import Path

import pandas as pd

from tools.konto_mapper import map_konten as map_konto
from tools.mieter_mapper import get_vertragids as map_mieter_to_vertragids
from tools.zeitraum_tool import get_zeitraum


class ZahlungsAssi:
    def __init__(self, csv_path: str = "data/tbl_zahlung_mit_vertragid.csv"):
        self.csv_path = Path(csv_path)

    def _parse_query(self, query: str) -> tuple[str, str, int]:
        text = query.strip().lower()

        jahr_match = re.search(r"\b(19|20)\d{2}\b", text)
        if not jahr_match:
            raise ValueError("Kein Jahr in der Query gefunden.")
        jahr = int(jahr_match.group())

        if "nebenkosten" in text:
            konto_zweck = "nebenkosten"
        elif "miete" in text:
            konto_zweck = "miete"
        else:
            raise ValueError("Kein Konto-Zweck erkannt (erwartet: miete/nebenkosten).")

        name_match = re.search(r"hat\s+(.+?)\s+(?:\d{4}|an)\b", text)
        if name_match:
            name = name_match.group(1).strip(" ?!.,")
        else:
            words = [w for w in re.findall(r"[a-zA-ZäöüÄÖÜß-]+", text) if w not in {"was", "hat", "an", "bezahlt", "welche"}]
            if not words:
                raise ValueError("Kein Name in der Query erkannt.")
            name = words[0]

        return name, konto_zweck, jahr

    @staticmethod
    def _find_konto_mask(df: pd.DataFrame, konten: list[int]) -> pd.Series:
        if not konten:
            return pd.Series(False, index=df.index)

        konto_set = {int(k) for k in konten}

        if "konto" in df.columns:
            return pd.to_numeric(df["konto"], errors="coerce").isin(konto_set)

        soll_cols = [c for c in ["konto_soll", "soll_konto", "soll"] if c in df.columns]
        haben_cols = [c for c in ["konto_haben", "haben_konto", "haben"] if c in df.columns]

        mask = pd.Series(False, index=df.index)
        for col in soll_cols + haben_cols:
            mask = mask | pd.to_numeric(df[col], errors="coerce").isin(konto_set)
        return mask

    def run(self, query: str) -> dict:
        name, konto_zweck, jahr = self._parse_query(query)

        vertragids = map_mieter_to_vertragids(name)
        konten = map_konto(konto_zweck)
        zeitraum = get_zeitraum(jahr=jahr)

        print(f"erkannter name: {name}")
        print(f"vertragids: {vertragids}")
        print(f"konten: {konten}")
        print(f"zeitraum: {zeitraum}")

        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV nicht gefunden: {self.csv_path}")

        df = pd.read_csv(self.csv_path)

        if "vertragid" not in df.columns:
            raise ValueError("Spalte 'vertragid' fehlt in der CSV.")
        if "datum" not in df.columns:
            raise ValueError("Spalte 'datum' fehlt in der CSV.")
        if "betrag" not in df.columns:
            raise ValueError("Spalte 'betrag' fehlt in der CSV.")

        df["vertragid"] = pd.to_numeric(df["vertragid"], errors="coerce")
        df["datum"] = pd.to_datetime(df["datum"], errors="coerce")
        df["betrag"] = pd.to_numeric(df["betrag"].astype(str).str.replace(",", ".", regex=False), errors="coerce").fillna(0.0)

        datum_von = pd.to_datetime(zeitraum["von"], errors="coerce")
        datum_bis = pd.to_datetime(zeitraum["bis"], errors="coerce")

        mask_vertrag = df["vertragid"].isin(vertragids)
        mask_konto = self._find_konto_mask(df, konten)
        mask_zeit = (df["datum"] >= datum_von) & (df["datum"] <= datum_bis)

        df_result = df[mask_vertrag & mask_konto & mask_zeit].copy()

        print(f"anzahl zeilen: {len(df_result)}")

        return {
            "summe": float(df_result["betrag"].sum()),
            "anzahl": int(len(df_result)),
            "daten": df_result,
        }
