from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MIETMATRIX_PATH = ROOT / "data" / "raw" / "mietmatrix.csv"


def match_mieter(name: str) -> list:
    if not MIETMATRIX_PATH.exists():
        return []

    df = pd.read_csv(MIETMATRIX_PATH)
    if df.empty:
        return []

    df.columns = df.columns.str.lower().str.strip()

    required = {"mieter_name_1", "mieter_name_2", "vertragid"}
    missing = required.difference(df.columns)
    if missing:
        return []

    name = str(name).lower().strip()

    df["mieter_name_1"] = df["mieter_name_1"].astype(str).str.lower().str.strip()
    df["mieter_name_2"] = df["mieter_name_2"].astype(str).str.lower().str.strip()

    matches = df[
        df["mieter_name_1"].str.contains(name, na=False)
        | df["mieter_name_2"].str.contains(name, na=False)
    ]

    print("Suche:", name)
    print("Gefundene Namen:", matches["mieter_name_1"].unique())

    vertragids = matches["vertragid"].dropna().unique().tolist()

    print("VertragIDs:", vertragids)

    return vertragids


def get_vertragids(mieter: str) -> list[int]:
    return [int(v) for v in match_mieter(mieter)]
