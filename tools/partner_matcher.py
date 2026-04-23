import pandas as pd
import re
from rapidfuzz import process, fuzz

PARTNER_FILE = "config/partner_mapping.csv"


def normalize(text):
    text = str(text).lower()
    text = text.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def run(df):
    partner_df = pd.read_csv(PARTNER_FILE)
    partner_df["norm"] = partner_df["partner"].apply(normalize)

    partner_list = partner_df["norm"].tolist()

    partner_ids = []
    scores = []

    for i, text in enumerate(df["buchungstext"]):

        # wenn Mieter erkannt → kein Partner
        if pd.notna(df.loc[i, "vertragid"]):
            partner_ids.append(None)
            scores.append(None)
            continue

        norm_text = normalize(text)

        match, score, idx = process.extractOne(
            norm_text,
            partner_list,
            scorer=fuzz.partial_ratio
        )

        partner_id = partner_df.iloc[idx]["partnerid"]

        partner_ids.append(partner_id)
        scores.append(score)

    df["partnerid"] = partner_ids
    df["partner_score"] = scores

    return df