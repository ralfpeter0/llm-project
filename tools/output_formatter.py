import pandas as pd


def _fmt_eur(value: float) -> str:
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"


def _fmt_datum(ts) -> str:
    if pd.isna(ts):
        return "  –  "
    return pd.Timestamp(ts).strftime("%d.%m.%Y")


def _trunc(text: str, n: int = 55) -> str:
    t = str(text).replace("\n", " ").strip()
    return t[:n] + "…" if len(t) > n else t


def _divider(char: str = "─", width: int = 72) -> str:
    return char * width


def _print_zahlung_check(intent: dict) -> bool:
    batch = intent.get("zahlung_check_batch_result")
    if intent.get("intent") == "zahlung_check" and isinstance(batch, dict):
        print()
        print(f"BATCH ZAHLUNGSCHECK {batch.get('jahr', '–')}")
        print(_divider("─", 120))
        header = [
            "Vertrag",
            "Mieter",
            "Laden",
            "Konto",
            "Soll mtl",
            "Jan IST",
            "Jan Δ",
            "Feb IST",
            "Feb Δ",
            "Mrz IST",
            "Mrz Δ",
            "Apr IST",
            "Apr Δ",
            "Mai IST",
            "Mai Δ",
            "Jun IST",
            "Jun Δ",
            "Jul IST",
            "Jul Δ",
            "Aug IST",
            "Aug Δ",
            "Sep IST",
            "Sep Δ",
            "Okt IST",
            "Okt Δ",
            "Nov IST",
            "Nov Δ",
            "Dez IST",
            "Dez Δ",
        ]
        print(" | ".join(header))
        print(_divider("─", 120))

        for row in batch.get("rows", []):
            months = row.get("months", {})
            values = [
                str(row.get("vertragid", "")),
                str(row.get("mieter", "")),
                str(row.get("laden", "")),
                str(row.get("konto", "")),
                _fmt_eur(float(row.get("soll_mtl", 0.0))),
            ]
            for m in range(1, 13):
                values.append(_fmt_eur(float(months.get(f"{m:02d}_ist", 0.0))))
                values.append(_fmt_eur(float(months.get(f"{m:02d}_delta", 0.0))))
            print(" | ".join(values))
        return True

    result = intent.get("zahlung_check_result")
    if intent.get("intent") != "zahlung_check" or not isinstance(result, dict):
        return False

    name = str(result.get("anzeige_name") or intent.get("mieter") or "MIETER").upper()
    jahr = result.get("jahr") or intent.get("jahr") or "–"

    print()
    print(f"{name}  ·  ZAHLUNGSCHECK {jahr}")
    print("─" * 28)
    print(f"Erwartet (SOLL):     {_fmt_eur(float(result.get('summe_soll', 0.0)))}")
    print(f"Erhalten (IST):      {_fmt_eur(float(result.get('summe_ist', 0.0)))}")
    print()
    print(f"Status:              {result.get('status_icon', '❌')} {result.get('status', 'nicht vollständig')}")
    print()
    print(f"Summe SOLL:          {_fmt_eur(float(result.get('summe_soll', 0.0)))}")
    print(f"Summe IST:           {_fmt_eur(float(result.get('summe_ist', 0.0)))}")
    print(f"Differenz:           {_fmt_eur(float(result.get('differenz', 0.0)))}")
    print()
    print("─" * 28)
    print("BUCHUNGEN (IST)")
    print("─" * 28)

    buchungen = result.get("buchungen", [])
    if not buchungen:
        print("Keine Buchungen gefunden.")
        return True

    for buchung in buchungen:
        print(f"{_fmt_datum(buchung.get('datum')):<12} {_fmt_eur(float(buchung.get('betrag', 0.0))):>10}")
    return True


def format_output(intent: dict, df: pd.DataFrame | None) -> None:
    if _print_zahlung_check(intent):
        return

    titel = intent.get("firma") or intent.get("mieter") or "Ergebnis"
    if intent.get("kostenstelle"):
        titel += f"  ·  {intent['kostenstelle']}"
    if intent.get("konto_zweck"):
        titel += f"  ·  {intent['konto_zweck']}"

    print()
    print(_divider("═"))
    print(f"  {titel.upper()}")
    print(_divider("═"))

    if df is None or df.empty:
        print("  Keine Buchungen gefunden.")
        print(_divider())
        return

    if intent.get("von") or intent.get("bis"):
        print(f"  Zeitraum : {intent.get('von', '–')}  →  {intent.get('bis', '–')}")

    konten = intent.get("konten", [])
    if konten:
        print(f"  Konten   : {', '.join(str(k) for k in konten)}")

    print()

    summe = df["betrag_signed"].sum() if "betrag_signed" in df.columns else df["betrag"].sum()
    anzahl = len(df)

    print(f"  {'Summe':<12} {_fmt_eur(summe):>18}")
    print(f"  {'Buchungen':<12} {anzahl:>15}")
    print()
    print(_divider())

    max_rows = 10
    zeige = df.sort_values("datum").head(max_rows)
    col_datum = 12
    col_betrag = 14
    col_ks = 5

    print(f"  {'Datum':<{col_datum}}{'Betrag':>{col_betrag}}  {'KS':<{col_ks}}  Buchungstext")
    print(_divider("·"))

    betrag_col = "betrag_signed" if "betrag_signed" in df.columns else "betrag"

    for _, row in zeige.iterrows():
        print(
            f"  {_fmt_datum(row.get('datum')):<{col_datum}}"
            f"{_fmt_eur(float(row.get(betrag_col, 0))):>{col_betrag}}"
            f"  {str(row.get('kostenstelle', '')).strip():<{col_ks}}"
            f"  {_trunc(str(row.get('buchungstext', '')))}"
        )

    rest = anzahl - max_rows
    if rest > 0:
        print(_divider("·"))
        print(f"  … {rest} weitere Buchungen nicht angezeigt")

    print(_divider())
    print()
