import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Engine.IntelligenceFramework.Core.FrameworkSubsystem import FrameworkSubsystem
from Engine.IntelligenceFramework.Reports.EngineIntelligenceReport import EngineIntelligenceReport


class ReportingSystem(FrameworkSubsystem):

    NAME = "ReportingSystem"
    VERSION = "3.0.0"
    CATEGORY = "Reporting"

    def __init__(self):

        self.reporter = EngineIntelligenceReport()
        self.last_output = None

    def startup(self):

        return True

    def _safe_call(self, obj, method, default=None):

        if obj is None:
            return default

        fn = getattr(obj, method, None)

        if not callable(fn):
            return default

        try:
            return fn()
        except Exception:
            return default

    def _knowledge(self, knowledge, category):

        if knowledge is None:
            return {}

        try:
            result = knowledge.get(category)

            if isinstance(result, dict):
                return result

        except Exception:
            pass

        return {}

    def _count(self, value):

        if value is None:
            return 0

        if isinstance(value, int):
            return value

        try:
            return len(value)
        except Exception:
            return 0

    def render_console(self, manager):

        brain = manager.registry.get(
            "EngineBrain"
        )

        architecture = manager.registry.get(
            "ArchitectureIntelligence"
        )

        reference = manager.registry.get(
            "ReferenceLearningSystem"
        )

        provenance = manager.registry.get(
            "ProvenanceIntelligence"
        )

        evolution = manager.registry.get(
            "EvolutionIntelligence"
        )

        build = manager.registry.get(
            "BuildIntelligence"
        )

        knowledge = manager.registry.get(
            "KnowledgeSystem"
        )

        registry = manager.registry.get(
            "DecisionRegistry"
        )

        history = manager.registry.get(
            "DecisionHistory"
        )

        build_knowledge = self._knowledge(
            knowledge,
            "Build"
        )

        architecture_knowledge = self._knowledge(
            knowledge,
            "Architecture"
        )

        reference_knowledge = self._knowledge(
            knowledge,
            "Reference"
        )

        intelligence = self._knowledge(
            knowledge,
            "Intelligence"
        )

        compiler_codes = self._safe_call(
            build,
            "compiler_codes",
            []
        )

        missing_members = self._safe_call(
            build,
            "missing_members",
            []
        )

        missing_types = self._safe_call(
            build,
            "missing_types",
            []
        )

        conversions = self._safe_call(
            build,
            "conversions",
            []
        )

        total_families = self._safe_call(
            build,
            "total_families",
            0
        )

        decisions = (
            brain.last_decisions
            if brain is not None
            else []
        )

        top = decisions[0] if decisions else {}

        print()
        print("=" * 72)
        print("OBSIDION ENGINE INTELLIGENCE")
        print("=" * 72)

        print()
        print("BUILD INTELLIGENCE")
        print("-" * 72)

        print(
            f"Error Families       : {total_families}"
        )

        print(
            f"Compiler Codes       : {self._count(compiler_codes)}"
        )

        print(
            f"Missing Members      : {self._count(missing_members)}"
        )

        print(
            f"Missing Types        : {self._count(missing_types)}"
        )

        print(
            f"Conversions          : {self._count(conversions)}"
        )

        print()
        print("ARCHITECTURE INTELLIGENCE")
        print("-" * 72)

        if architecture is not None:

            types = getattr(
                architecture,
                "types",
                {}
            )

            print(
                f"Types Discovered     : {len(types)}"
            )

            print(
                f"Graph Nodes          : "
                f"{architecture.node_count()}"
            )

            print(
                f"Graph Edges          : "
                f"{architecture.edge_count()}"
            )

        else:
            print("Architecture         : UNAVAILABLE")

        print()
        print("REFERENCE INTELLIGENCE")
        print("-" * 72)

        if reference is not None:

            reference_types = getattr(
                reference,
                "types",
                {}
            )

            print(
                f"ServUO Types         : "
                f"{len(reference_types)}"
            )

            item = reference.get_type(
                "Server.Item"
            )

            print(
                "ServUO Server.Item    : "
                + (
                    "KNOWN"
                    if item is not None
                    else "UNKNOWN"
                )
            )

        else:
            print("Reference            : UNAVAILABLE")

        print()
        print("PROVENANCE INTELLIGENCE")
        print("-" * 72)

        print(
            f"Concepts             : "
            f"{provenance.total_concepts() if provenance is not None else 0}"
        )

        print(
            f"Relationships        : "
            f"{provenance.total_relationships() if provenance is not None else 0}"
        )

        print()
        print("EVOLUTION INTELLIGENCE")
        print("-" * 72)

        evolution_status = (
            evolution.status()
            if evolution is not None
            else {}
        )

        print(
            f"Trend                : "
            f"{evolution_status.get('trend', 'UNKNOWN')}"
        )

        print(
            f"Error Delta          : "
            f"{evolution_status.get('error_delta')}"
        )

        print(
            f"New Signatures       : "
            f"{evolution_status.get('new_signatures', 0)}"
        )

        print(
            f"Resolved Signatures  : "
            f"{evolution_status.get('resolved_signatures', 0)}"
        )

        print()
        print("DECISION INTELLIGENCE")
        print("-" * 72)

        print(
            f"Current Decisions    : {len(decisions)}"
        )

        print(
            f"Registry Decisions   : "
            f"{registry.total() if registry is not None else 0}"
        )

        print(
            f"History Events       : "
            f"{history.total_events() if history is not None else 0}"
        )

        if top:

            print()
            print("TOP INTELLIGENCE DECISION")
            print("-" * 72)

            print(
                f"Category             : "
                f"{top.get('category', 'UNKNOWN')}"
            )

            print(
                f"Target               : "
                f"{top.get('target', 'UNKNOWN')}"
            )

            print(
                f"Impact               : "
                f"{top.get('impact', 0)}"
            )

            print(
                f"Priority             : "
                f"{top.get('priority', 'UNKNOWN')}"
            )

            print(
                f"Verdict              : "
                f"{top.get('verdict', 'UNKNOWN')}"
            )

            print(
                f"Confidence           : "
                f"{top.get('confidence', 'UNKNOWN')}"
            )

            print(
                f"Action               : "
                f"{top.get('action', 'UNKNOWN')}"
            )

            evidence = top.get("evidence", [])

            if evidence:
                print("Evidence             :")
                for item in evidence:
                    print(f"  - {item}")

        print()
        print("ITEM CONTRACT CHAIN")
        print("-" * 72)

        if architecture is not None:

            chain = (
                "OBSIDION_ENGINE.Runtime.Item",
                "Server.Item",
                "Server.Items.Item",
            )

            for name in chain:

                known = architecture.knows_type(name)

                print(
                    f"{name:<34} : "
                    f"{'KNOWN' if known else 'UNKNOWN'}"
                )

                if known:

                    parents = (
                        architecture
                        .inheritance_parents(name)
                    )

                    if parents:
                        print(
                            "  Parents"
                            f"{'':<26} : "
                            + ", ".join(parents)
                        )

        print()
        print("KNOWLEDGE CHANNELS")
        print("-" * 72)

        print(
            f"Build Facts          : "
            f"{len(build_knowledge)}"
        )

        print(
            f"Architecture Facts   : "
            f"{len(architecture_knowledge)}"
        )

        print(
            f"Reference Facts      : "
            f"{len(reference_knowledge)}"
        )

        print(
            f"Intelligence Facts   : "
            f"{len(intelligence)}"
        )

        print()
        print("=" * 72)

        return True

    def generate(self, manager):

        # Immediate operator-facing intelligence.
        self.render_console(manager)

        # Persistent deep-inspection report.
        self.last_output = self.reporter.generate(
            manager
        )

        return self.last_output

    def health(self):

        return "ONLINE"


if __name__ == "__main__":

    system = ReportingSystem()

    print("=" * 70)
    print("REPORTING SYSTEM")
    print("=" * 70)
    print("Health :", system.health())
    print("=" * 70)
