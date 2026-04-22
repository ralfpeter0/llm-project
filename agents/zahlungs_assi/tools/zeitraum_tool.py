def get_zeitraum(jahr: int | None = None, monat: int | None = None) -> dict:
    if jahr is None:
        return {"von": None, "bis": None}

    jahr = int(jahr)

    if monat is not None:
        monat = int(monat)
        if monat == 1:
            return {"von": f"{jahr - 1}-12-20", "bis": f"{jahr}-01-19"}
        return {"von": f"{jahr}-{monat - 1:02d}-20", "bis": f"{jahr}-{monat:02d}-19"}

    return {"von": f"{jahr - 1}-12-20", "bis": f"{jahr}-12-19"}
