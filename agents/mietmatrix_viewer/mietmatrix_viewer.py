import pandas as pd


class MietmatrixViewer:
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.df: pd.DataFrame | None = None

    def load(self) -> None:
        self.df = pd.read_csv(self.file_path, sep=";")

    def _prepare(self) -> pd.DataFrame:
        if self.df is None:
            raise ValueError("Dataframe not loaded. Call load() first.")

        cols = [
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

        return self.df[cols].rename(
            columns={
                "mieter_name_1": "mieter_1",
                "mieter_name_2": "mieter_2",
            }
        )

    def get_full_list(self) -> pd.DataFrame:
        df = self._prepare().sort_values(["einheit", "vertragid", "konto"])
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
