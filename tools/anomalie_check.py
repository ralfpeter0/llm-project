import pandas as pd


def run(df):

    df = df.copy()

    # -----------------------------
    # Vorbereitung
    # -----------------------------
    df["datum"] = pd.to_datetime(df["Datum"], format="%d.%m.%Y", errors="coerce")
    df["betrag"] = df["Betrag"].astype(str).str.replace(",", ".").astype(float)

    # nur relevante Konten
    df = df[df["Habenkonto"].isin([8105, 8195, 8115])]

    # -----------------------------
    # Name bestimmen
    # -----------------------------
    def get_name(row):
        if pd.notna(row["vertragid"]):
            # optional schöner machen, wenn mieter_name existiert
            if "mieter_name" in row and pd.notna(row["mieter_name"]):
                return row["mieter_name"]
            return f"vertrag_{int(row['vertragid'])}"
        elif pd.notna(row["partnerid"]):
            if "partner_name" in row and pd.notna(row["partner_name"]):
                return row["partner_name"]
            return f"partner_{int(row['partnerid'])}"
        return "unbekannt"

    df["name"] = df.apply(get_name, axis=1)

    results = []

    # -----------------------------
    # Gruppierung nach Name
    # -----------------------------
    for name, group in df.groupby("name"):

        if name == "unbekannt":
            continue

        group = group.sort_values("datum")

        group["delta_tage"] = group["datum"].diff().dt.days
        group["delta_betrag"] = group["betrag"].diff()

        for _, row in group.iterrows():

            # -----------------------------
            # Zeit-Anomalie
            # -----------------------------
            if pd.notna(row["delta_tage"]):
                if row["delta_tage"] < 20 or row["delta_tage"] > 40:
                    results.append({
                        "typ": "zeit",
                        "name": name,
                        "datum": row["datum"],
                        "delta_tage": row["delta_tage"],
                        "betrag": row["betrag"],
                        "konto": row["Habenkonto"]
                    })

            # -----------------------------
            # Betrags-Anomalie
            # -----------------------------
            if pd.notna(row["delta_betrag"]):
                if abs(row["delta_betrag"]) > 200:
                    results.append({
                        "typ": "betrag",
                        "name": name,
                        "datum": row["datum"],
                        "delta_betrag": row["delta_betrag"],
                        "betrag": row["betrag"],
                        "konto": row["Habenkonto"]
                    })

    return pd.DataFrame(results)