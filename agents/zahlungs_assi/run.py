from pathlib import Path
import sys

# Projekt-Root in den Path aufnehmen
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from agents.zahlungs_assi.zahlungs_assi import ZahlungsAssi


if __name__ == "__main__":
    agent = ZahlungsAssi()

    # 👉 Testfrage hier ändern
    result = agent.run("was hat flury 2025 an nebenkosten bezahlt?")

    print("RESULT RAW:", result)

    # Dynamischer Output je nach operation
    if "buchungen" in result:
        import pandas as pd
        df = pd.DataFrame(result["buchungen"])
        print("\n--- BUCHUNGEN ---")
        print(df.head())

    elif "summe" in result:
        print("\n--- SUMME ---")
        print("Summe:", result["summe"])

    elif "exists" in result:
        print("\n--- CHECK ---")
        print("Exists:", result["exists"])

    else:
        print("\n--- UNBEKANNTER OUTPUT ---")
        print(result)
