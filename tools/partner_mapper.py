from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def get_partnerids(name: str) -> list[int]:
    file_path = ROOT / "data" / "processed" / "2026-04-22_buchhaltung_processed.csv"

    df = pd.read_csv(file_path)

    if "buchungstext" not in df.columns or "partnerid" not in df.columns:
        return []

    mask = df["buchungstext"].astype(str).str.contains(name, case=False, na=False)
    partnerids = (
        pd.to_numeric(df.loc[mask, "partnerid"], errors="coerce")
        .dropna()
        .astype(int)
        .unique()
        .tolist()
    )

    print("PartnerIDs:", partnerids)
    return partnerids