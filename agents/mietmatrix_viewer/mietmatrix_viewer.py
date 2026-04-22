import pandas as pd


class MietmatrixViewer:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.df = None

    def load(self):
        self.df = pd.read_csv(self.file_path, sep=";", encoding="utf-8")
        self.df.columns = self.df.columns.str.strip().str.lower()

    def get_full_list(self):
        if self.df is None:
            raise ValueError("Dataframe not loaded")

        df = self.df.copy()

        # Spalten prüfen (Debug)
        required = [
            "vertragid",
            "objekt",
            "wohnung",
            "mieter_name_1",
            "mieter_name_2",
            "einheit",
            "konto",
            "sollbetrag",
            "vertragsart",
        ]

        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Fehlende Spalten: {missing}")

        df["mieter_1"] = df["mieter_name_1"]
        df["mieter_2"] = df["mieter_name_2"]

        # Sortierung
        df = df.sort_values(by=["einheit", "vertragid", "konto"])

        # Ausgabe
        return df[
            [
                "vertragid",
                "objekt",
                "wohnung",
                "mieter_1",
                "mieter_2",
                "konto",
                "sollbetrag",
                "vertragsart",
            ]
        ]
