import pandas as pd


MIETE = [8105, 8400, 8403]
BK_MONATLICH = [8195, 8401]
STELLPLATZ = [8115]

RELEVANTE_KONTEN = MIETE + BK_MONATLICH + STELLPLATZ


def get_mietmonat(d):
    if d.day >= 20:
        return f"{d.year}-{d.month:02d}"
    else:
        prev = d - pd.DateOffset(months=1)
        return f"{prev.year}-{prev.month:02d}"


def run(df_ist, df_soll):

    # -----------------------------
    # IST vorbereiten
    # -----------------------------
    df = df_ist.copy()

    df["datum"] = pd.to_datetime(df["Datum"], format="%d.%m.%Y", errors="coerce")
    df["betrag"] = df["Betrag"].astype(str).str.replace(",", ".").astype(float)

    df = df[df["Habenkonto"].isin(RELEVANTE_KONTEN)]
    df = df[df["vertragid"].notna()]

    df["monat"] = df["datum"].apply(get_mietmonat)

    # -----------------------------
    # IST aggregieren
    # -----------------------------
    ist = (
        df.groupby(["vertragid", "Habenkonto", "monat"])["betrag"]
        .sum()
        .reset_index()
    )

    ist = ist.rename(columns={
        "Habenkonto": "konto",
        "betrag": "ist"
    })

    # -----------------------------
    # SOLL vorbereiten
    # -----------------------------
    soll = df_soll.copy()

    soll = soll[["vertragid", "konto", "sollbetrag"]]
    soll["konto"] = soll["konto"].astype(int)

    soll = soll.rename(columns={
        "sollbetrag": "soll"
    })

    # -----------------------------
    # Join
    # -----------------------------
    merged = pd.merge(
        ist,
        soll,
        on=["vertragid", "konto"],
        how="left"
    )

    # -----------------------------
    # Bewertung
    # -----------------------------
    def check(row):

        if pd.isna(row["soll"]):
            return "kein_soll"

        if row["ist"] == 0:
            return "fehlend"

        if abs(row["ist"] - row["soll"]) < 1:
            return "ok"

        if row["ist"] < row["soll"]:
            return "zu_wenig"

        if row["ist"] > row["soll"]:
            return "zu_viel"

    merged["status"] = merged.apply(check, axis=1)

    return merged