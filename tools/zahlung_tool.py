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
        print(
            f"Warning: multiple processed CSV files found ({len(files)}). "
            f"Selecting latest: {latest_file.name}"
        )

    return latest_file


def zahlung_tool(
    vertragids=None,
    konten=None,
    von=None,
    bis=None,
    operation="summe",
):

    file_path = get_latest_file()

    try:
        printable_path = file_path.relative_to(ROOT)
    except ValueError:
        printable_path = file_path

    print(f"Using data file: {printable_path}")

    # CSV laden
    df = pd.read_csv(file_path, encoding="latin1")

    # Spalten vereinheitlichen
    df = df.rename(columns={
        "Datum": "datum",
        "Betrag": "betrag",
        "Sollkonto": "sollkonto",
        "Habenkonto": "habenkonto",
    })

    # Datentypen
    df["datum"] = pd.to_datetime(df["datum"], errors="coerce")

    # WICHTIG: nur Komma ersetzen, KEIN Punkt entfernen
    df["betrag"] = (
        df["betrag"]
        .astype(str)
        .str.replace(",", ".", regex=False)
    )
    df["betrag"] = pd.to_numeric(df["betrag"], errors="coerce")

    df["sollkonto"] = pd.to_numeric(df["sollkonto"], errors="coerce")
    df["habenkonto"] = pd.to_numeric(df["habenkonto"], errors="coerce")
    df["vertragid"] = pd.to_numeric(df["vertragid"], errors="coerce")

    # Filter
    if vertragids:
        df = df[df["vertragid"].isin(vertragids)]

    if konten:
        df = df[
            df["sollkonto"].isin(konten) |
            df["habenkonto"].isin(konten)
        ]

    if von:
        df = df[df["datum"] >= pd.to_datetime(von, errors="coerce")]

    if bis:
        df = df[df["datum"] <= pd.to_datetime(bis, errors="coerce")]

    df = df.copy()
    df["datum"] = df["datum"].dt.strftime("%Y-%m-%d")

    # Operationen
    if operation == "summe":
        return {"summe": float(df["betrag"].sum())}

    if operation == "liste":
        return {"buchungen": df.to_dict(orient="records")}

    if operation == "check":
        return {"exists": len(df) > 0}

    return {"buchungen": df.to_dict(orient="records")}
