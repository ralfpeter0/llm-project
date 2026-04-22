from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from agents.zahlungs_assi.zahlungs_assi import ZahlungsAssi


if __name__ == "__main__":
    agent = ZahlungsAssi()
    result = agent.run("was hat flury 2025 an nebenkosten bezahlt?")
    print(result)
