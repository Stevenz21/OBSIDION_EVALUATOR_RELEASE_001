import sys
from pathlib import Path
import subprocess
import re
from datetime import datetime

ROOT = Path(__file__).resolve().parents[3]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Engine.IntelligenceFramework.Core.FrameworkSubsystem import FrameworkSubsystem
from Engine.IntelligenceFramework.Analyzers.ErrorFamilyAnalyzer import analyze_build_log


class BuildIntelligence(FrameworkSubsystem):

    NAME = "BuildIntelligence"
    VERSION = "2.0.0"
    CATEGORY = "Analysis"

    def __init__(self):
        self.analysis = None

    def startup(self):
        self.analysis = None
        return True


    def analyze(self):

        # Runtime.csproj already built before EIF starts.
        # BuildIntelligence only analyzes the existing build log.
        self.analysis = analyze_build_log()
        return self.analysis

    def health(self):
        if self.analysis is None:
            return "IDLE"

        if not self.analysis.get("exists"):
            return "NO BUILD LOG"

        return "ONLINE"

    def compiler_codes(self):
        if not self.analysis:
            return {}

        return self.analysis["codes"]

    def missing_members(self):
        if not self.analysis:
            return {}

        return self.analysis["members"]

    def missing_types(self):
        if not self.analysis:
            return {}

        return self.analysis["types"]

    def conversions(self):
        if not self.analysis:
            return {}

        return self.analysis["conversions"]

    def total_families(self):
        if not self.analysis:
            return 0

        return (
            len(self.analysis["members"])
            + len(self.analysis["types"])
            + len(self.analysis["conversions"])
        )


if __name__ == "__main__":

    subsystem = BuildIntelligence()
    subsystem.startup()

    print("=" * 70)
    print("BUILD INTELLIGENCE")
    print("=" * 70)
    print("Health         :", subsystem.health())
    print("Compiler Codes :", len(subsystem.compiler_codes()))
    print("Error Families :", subsystem.total_families())
    print("=" * 70)
