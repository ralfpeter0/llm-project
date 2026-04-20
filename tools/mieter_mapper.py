import json
import os

import pandas as pd

from tools.fuzzy_matcher import best_token_match, normalize

MIETMATRIX_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "mietmatrix.csv")
PARTNER_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "partner_mapping.json")
FUZZY_THRESHOLD = 85


def _load_partner_mapping() -> list[dict]:
    with open(PARTNER_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def _get_mieter_aliases() -> list[str]:
    for entry in _load_partner_mapping():
        if entry.get("canonical") == "MIETER":
            return [str(alias) for alias in entry.get("aliases", [])]
    return []


def _find_exact_mieter_alias(user_input: str) -> str | None:
    normalized_input = normalize(user_input)
    if not normalized_input:
        return None

    input_tokens = set(normalized_input.split(" "))
    for alias in _get_mieter_aliases():
        normalized_alias = normalize(alias)
        if normalized_input == normalized_alias or normalized_alias in input_tokens:
            return alias
    return None


def get_vertragids(mieter: str) -> list[int]:
    if not os.path.exists(MIETMATRIX_PATH):
        return []

    df = pd.read_csv(MIETMATRIX_PATH)
    if df.empty:
        return []

    df["mieter_all"] = (
        df.get("mieter_name_1", "").fillna("").astype(str)
        + " "
        + df.get("mieter_name_2", "").fillna("").astype(str)
    ).str.lower()
    df["mieter_all_norm"] = df["mieter_all"].map(normalize)

    mieter_input = str(mieter).strip()
    exact_alias = _find_exact_mieter_alias(mieter_input)

    if exact_alias:
        mask = df["mieter_all_norm"].str.contains(normalize(exact_alias), na=False)
        vertragids = df.loc[mask, "vertragid"].dropna().astype(int).unique().tolist()
        if vertragids:
            return vertragids

    best_idx = None
    best_score = 0
    for idx, candidate in df["mieter_all_norm"].items():
        score = best_token_match(mieter_input, str(candidate))
        if score > best_score:
            best_score = score
            best_idx = idx

    if best_idx is not None and best_score >= FUZZY_THRESHOLD:
        best_name = str(df.loc[best_idx, "mieter_all"]).strip()
        vertragids = (
            df.loc[df["mieter_all_norm"] == df.loc[best_idx, "mieter_all_norm"], "vertragid"]
            .dropna()
            .astype(int)
            .unique()
            .tolist()
        )
        print(f"UNMATCHED (Mapping fehlt): {mieter_input}")
        print(
            f"Fuzzy Mieter: {mieter_input} -> {best_name} | "
            f"Score: {best_score} | VertragIDs: {vertragids}"
        )
        return vertragids

    return []
