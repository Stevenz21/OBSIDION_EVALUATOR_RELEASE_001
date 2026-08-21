import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Engine.IntelligenceFramework.Core.FrameworkSubsystem import FrameworkSubsystem


DB = Path("Engine/IntelligenceFramework/History/DecisionHistory.json")


class DecisionRegistry(FrameworkSubsystem):

    NAME = "DecisionRegistry"
    VERSION = "1.1.0"
    CATEGORY = "Registry"

    def __init__(self):

        self.decisions = []

        if DB.exists():
            try:
                loaded = json.loads(DB.read_text(encoding="utf-8"))

                if isinstance(loaded, list):
                    self.decisions = loaded

            except (json.JSONDecodeError, OSError):
                self.decisions = []

    def replace(self, decisions):

        self.decisions = list(decisions)

    def add(self, decision):

        if decision not in self.decisions:
            self.decisions.append(decision)

    def total(self):

        return len(self.decisions)

    def clear(self):

        self.decisions = []

    def save(self):

        DB.parent.mkdir(parents=True, exist_ok=True)

        DB.write_text(
            json.dumps(self.decisions, indent=4),
            encoding="utf-8"
        )

        return True


if __name__ == "__main__":

    registry = DecisionRegistry()

    print("=" * 70)
    print("ENGINE DECISION REGISTRY")
    print("=" * 70)
    print(f"Tracked Decisions : {registry.total()}")
    print("=" * 70)
