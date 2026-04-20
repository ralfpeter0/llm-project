import os

import pandas as pd

FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "tbl_zahlung_mit_mieter.csv")


def filter_zahlungen(
    vertragids: list[int] | None = None,
    konten: list[int] | None = None,
    von: str | None = None,
    bis: str | None = None,
    sollkonto_oder_haben: bool = True,
) -> list[dict]:
    if not os.path.exists(FILE_PATH):
        raise FileNotFoundError(f"Zahlungsdatei nicht gefunden: {FILE_PATH}")

    df = pd.read_csv(FILE_PATH)
    df["datum"] = pd.to_datetime(df["datum"], errors="coerce")
    df["vertragid"] = pd.to_numeric(df["vertragid"], errors="coerce").fillna(0).astype(int)
    df["sollkonto"] = pd.to_numeric(df["sollkonto"], errors="coerce")
    df["habenkonto"] = pd.to_numeric(df["habenkonto"], errors="coerce")

    if vertragids:
        df = df[df["vertragid"].isin(vertragids)]

    if konten:
        if sollkonto_oder_haben:
            df = df[df["sollkonto"].isin(konten) | df["habenkonto"].isin(konten)]
        else:
            df = df[df["habenkonto"].isin(konten)]

    if von:
        df = df[df["datum"] >= pd.to_datetime(von, errors="coerce")]
    if bis:
        df = df[df["datum"] <= pd.to_datetime(bis, errors="coerce")]

    df = df.copy()
    df["datum"] = df["datum"].dt.strftime("%Y-%m-%d")

    return df.to_dict(orient="records")


def summe_zahlungen(buchungen: list[dict]) -> float:
    return sum(float(x.get("betrag", 0)) for x in buchungen)
