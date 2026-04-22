import pandas as pd


class MietmatrixViewer:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.df = None

    def load(self):
        self.df = pd.read_csv(self.file_path)
        self._prepare()

    def _prepare(self):
        columns = [
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
        self.df = self.df[columns].copy()
        self.df = self.df.rename(
            columns={
                "mieter_name_1": "mieter_1",
                "mieter_name_2": "mieter_2",
            }
        )

    def get_view(self):
        result_columns = [
            "vertragid",
            "objekt",
            "wohnung",
            "mieter_1",
            "mieter_2",
            "konto",
            "sollbetrag",
            "vertragsart",
        ]

        return (
            self.df.sort_values(["einheit", "vertragid", "konto"])[result_columns]
            .reset_index(drop=True)
        )
