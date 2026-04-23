# agents/datenimport_agent/run.py

import sys
from pathlib import Path

# Projekt-Root hinzufügen
ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from agents.datenimport_agent.datenimport_agent import DatenimportAgent


if __name__ == "__main__":
    agent = DatenimportAgent()

    # 👉 HIER deinen Input-Pfad anpassen
    input_path = Path(r"C:\llm-project\data\raw\BB_Buchungsstapel - 2026-04-17T184137.857.csv")

    result = agent.run({
        "file_path": str(input_path)
    })

    print(result["text"])