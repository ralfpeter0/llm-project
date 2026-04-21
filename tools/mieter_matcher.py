import pandas as pd
import re
from rapidfuzz import process, fuzz

MIETMATRIX_FILE = "data/raw/mietmatrix.csv"


def normalize(text):
    text = str(text).lower()
    text = text.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def load_mieter():
    df = pd.read_csv(MIETMATRIX_FILE)

    namen = []
    vertragids = []
    konten = []

    for _, row in df.iterrows():
        vid = row["vertragid"]
        konto = row.get("konto")

        fields = [
            row.get("mieter_name_1"),
            row.get("mieter_name_2"),
            row.get("name"),
            row.get("laden")
        ]

        for f in fields:
            if pd.notna(f):
                namen.append(normalize(f))
                vertragids.append(vid)
                konten.append(konto)

    return namen, vertragids, konten


def match_mieter(text, konto_buchung, namen, vertragids, konten):
    norm_text = normalize(text)

    # Top 5 Kandidaten holen
    matches = process.extract(
        norm_text,
        namen,
        scorer=fuzz.partial_ratio,
        limit=5
    )

    best_vid = None
    best_score = 0

    for match, score, idx in matches:
        konto = konten[idx]
        vid = vertragids[idx]

        # Konto-Logik
        if pd.notna(konto_buchung) and pd.notna(konto):
            if int(konto_buchung) != int(konto):
                continue

        if score > best_score:
            best_score = score
            best_vid = vid

    if best_score >= 75:
        return best_vid, best_score
    else:
        return None, best_score


def run(df):
    namen, vertragids, konten = load_mieter()

    vids = []
    scores = []

    for _, row in df.iterrows():
        text = row["Buchungstext"]
        konto_buchung = row["Habenkonto"]  # wichtig!

        vid, score = match_mieter(text, konto_buchung, namen, vertragids, konten)

        vids.append(vid)
        scores.append(score)

    df["vertragid"] = vids
    df["mieter_score"] = scores

    return df