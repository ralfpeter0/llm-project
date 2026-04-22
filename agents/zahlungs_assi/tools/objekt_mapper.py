import os

import pandas as pd

MIETMATRIX_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "mietmatrix.csv")


def _load() -> pd.DataFrame:
    if not os.path.exists(MIETMATRIX_PATH):
        raise FileNotFoundError(f"mietmatrix.csv nicht gefunden: {MIETMATRIX_PATH}")
    return pd.read_csv(MIETMATRIX_PATH)


def map_objekt_to_kostenstelle(objekt: str) -> str | None:
    df = _load()
    obj = str(objekt).strip().lower()

    if obj in df["kostenstelle"].astype(str).str.lower().values:
        return obj.upper()

    match_objekt = df[df["objekt"].astype(str).str.lower() == obj]
    if not match_objekt.empty:
        return str(match_objekt.iloc[0]["kostenstelle"])

    match_strasse = df[df["strasse"].astype(str).str.lower().str.contains(obj, na=False)]
    if not match_strasse.empty:
        return str(match_strasse.iloc[0]["kostenstelle"])

    return None
