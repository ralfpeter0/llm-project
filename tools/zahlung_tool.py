from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "processed"


def get_latest_file() -> Path:
    files = list(DATA_DIR.glob("*.csv"))
    if not files:
        raise FileNotFoundError("No processed CSV files found in data/processed")

    latest_file = max(files, key=lambda f: f.stat().st_mtime)

    if len(files) > 1:
        print(f"Warning: multiple processed CSV files found ({len(files)}). Selecting latest: {latest_file.name}")

    return latest_file


def filter_zahlungen(
    vertragids: list[int] | None = None,
    konten: list[int] | None = None,
    von: str | None = None,
    bis: str | None = None,
    sollkonto_oder_haben: bool = True,
) -> list[dict]:
    file_path = get_latest_file()

    try:
        printable_path = file_path.relative_to(ROOT)
    except ValueError:
        printable_path = file_path

    print(f"Using data file: {printable_path}")

    df = pd.read_csv(file_path)
    df = df.rename(columns={
        "Datum": "datum",
        "Betrag": "betrag",
        "Sollkonto": "sollkonto",
        "Habenkonto": "habenkonto",
    })

    df["datum"] = pd.to_datetime(df["datum"], errors="coerce")

    betrag_col = df.get("betrag")
    if betrag_col is not None:
        if pd.api.types.is_numeric_dtype(betrag_col):
            df["betrag"] = betrag_col
        else:
            df["betrag"] = pd.to_numeric(
                betrag_col.astype(str)
                .str.replace(".", "", regex=False)
                .str.replace(",", ".", regex=False),
                errors="coerce",
            )
    df["sollkonto"] = pd.to_numeric(df["sollkonto"], errors="coerce")
    df["habenkonto"] = pd.to_numeric(df["habenkonto"], errors="coerce")
    df["vertragid"] = pd.to_numeric(df["vertragid"], errors="coerce")

    if vertragids:
        df = df[df["vertragid"].isin(vertragids)]

    if konten:
        if sollkonto_oder_haben:
            df = df[df["habenkonto"].isin(konten)]
        else:
            df = df[df["sollkonto"].isin(konten)]

    if von:
        df = df[df["datum"] >= pd.to_datetime(von, errors="coerce")]
    if bis:
        df = df[df["datum"] <= pd.to_datetime(bis, errors="coerce")]

    df = df.copy()
    df["datum"] = df["datum"].dt.strftime("%Y-%m-%d")

    return df.to_dict(orient="records")


def summe_zahlungen(buchungen: list[dict]) -> float:
    return sum(float(x.get("betrag", 0)) for x in buchungen)
