import pandas as pd


def zahlung_tool(
    df: pd.DataFrame,
    vertragids: list[int] | None = None,
    partnerids: list[int] | None = None,
    konten: list[int] | None = None,
    von: str | None = None,
    bis: str | None = None,
    operation: str | None = None,
):
    data = df.copy()

    if vertragids and "vertragid" in data.columns:
        data = data[data["vertragid"].isin(vertragids)]

    if partnerids and "partnerid" in data.columns:
        data = data[data["partnerid"].isin(partnerids)]

    if konten:
        soll = data["sollkonto"].isin(konten) if "sollkonto" in data.columns else False
        haben = data["habenkonto"].isin(konten) if "habenkonto" in data.columns else False
        data = data[soll | haben]

    if von and "datum" in data.columns:
        data = data[data["datum"] >= pd.to_datetime(von)]

    if bis and "datum" in data.columns:
        data = data[data["datum"] <= pd.to_datetime(bis)]

    if operation == "summe":
        return float(data["betrag"].sum()) if "betrag" in data.columns else 0.0

    if operation == "check":
        return len(data) > 0

    if operation == "liste":
        return data

    return data
