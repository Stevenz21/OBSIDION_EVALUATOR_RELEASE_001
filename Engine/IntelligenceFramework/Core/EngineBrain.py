import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Engine.IntelligenceFramework.Core.FrameworkSubsystem import FrameworkSubsystem
from Engine.IntelligenceFramework.Core.DecisionEngine import evaluate_targets
from Engine.IntelligenceFramework.Registry.DecisionRegistry import DecisionRegistry


class EngineBrain(FrameworkSubsystem):

    NAME = "EngineBrain"
    VERSION = "4.0.0"
    CATEGORY = "Core"

    def __init__(self):

        self.registry = None
        self.history = None
        self.knowledge = None

        self.architecture = None
        self.reference = None
        self.build_intelligence = None
        self.provenance = None
        self.evolution = None

        self.last_decisions = []
        self.last_events = []

        self.online = False

    def wire(
        self,
        registry=None,
        history=None,
        knowledge=None,
        architecture=None,
        reference=None,
        build_intelligence=None,
        provenance=None,
        evolution=None,
    ):

        if registry is not None:
            self.registry = registry

        if history is not None:
            self.history = history

        if knowledge is not None:
            self.knowledge = knowledge

        if architecture is not None:
            self.architecture = architecture

        if reference is not None:
            self.reference = reference

        if build_intelligence is not None:
            self.build_intelligence = build_intelligence

        if provenance is not None:
            self.provenance = provenance

        if evolution is not None:
            self.evolution = evolution

        return True

    def startup(self):

        if self.registry is None:
            self.registry = DecisionRegistry()

        self.online = True
        return True

    def _conversion_evidence(
        self,
        source,
        target,
    ):

        evidence = []

        verdict = "UNRESOLVED CONVERSION"
        confidence = "MEDIUM"
        action = None

        if self.architecture is not None:

            try:

                target_parents = (
                    self.architecture.inheritance_parents(
                        target
                    )
                )

            except Exception:
                target_parents = []

            try:

                source_parents = (
                    self.architecture.inheritance_parents(
                        source
                    )
                )

            except Exception:
                source_parents = []

            if source in target_parents:

                verdict = (
                    "DOWNCAST CONTRACT BOUNDARY"
                )

                confidence = "HIGH"

                action = (
                    "INVESTIGATE SHARED CONTRACT"
                )

                evidence.append(
                    f"{target} derives from {source}"
                )

                evidence.append(
                    "Compiler direction is base-to-derived"
                )

            elif target in source_parents:

                verdict = (
                    "ARCHITECTURE-SUPPORTED UPCAST"
                )

                confidence = "HIGH"

                action = (
                    "VALIDATE CANONICAL CONTRACT"
                )

                evidence.append(
                    f"{source} derives from {target}"
                )

        if self.reference is not None:

            try:
                source_known = self.reference.knows(
                    source
                )
            except Exception:
                source_known = False

            try:
                target_known = self.reference.knows(
                    target
                )
            except Exception:
                target_known = False

            if source_known:

                evidence.append(
                    f"Reference knows {source}"
                )

            if target_known:

                evidence.append(
                    f"Reference knows {target}"
                )

            if source_known and not target_known:

                evidence.append(
                    "Reference supports source-side contract"
                )

                if verdict == "UNRESOLVED CONVERSION":

                    verdict = (
                        "REFERENCE CONTRACT MISMATCH"
                    )

                    confidence = "HIGH"

                    action = (
                        "INSPECT CANONICAL OWNER"
                    )

        if self.provenance is not None:

            lineage = self.provenance.relationship(
                source,
                target,
                relation="DERIVED_FROM",
            )

            if lineage is not None:

                evidence.extend(lineage.get("evidence", []))
                evidence.append(
                    "Provenance confirms active derived-contract evidence"
                )

                if verdict == "UNRESOLVED CONVERSION":
                    verdict = "DERIVED CONTRACT BOUNDARY"
                    confidence = "HIGH"
                    action = "INVESTIGATE SHARED CONTRACT"

            compatibility = self.provenance.relationship(
                f"ServUO::{source}",
                source,
                relation="COMPATIBILITY_WITH",
            )

            if compatibility is not None:
                evidence.append(
                    "Provenance confirms ServUO structural correspondence for source contract"
                )

        evidence = list(dict.fromkeys(evidence))

        return {
            "verdict": verdict,
            "confidence": confidence,
            "action": action,
            "evidence": evidence,
        }

    def _enrich_decision(self, decision):

        enriched = dict(decision)

        enriched.setdefault(
            "verdict",
            "IMPACT PRIORITY"
        )

        enriched.setdefault(
            "confidence",
            "MEDIUM"
        )

        enriched.setdefault(
            "evidence",
            []
        )

        if (
            decision.get("category")
            == "Conversion"
        ):

            target = decision.get(
                "target",
                ""
            )

            if "->" in target:

                source, destination = [
                    value.strip()
                    for value in target.split(
                        "->",
                        1,
                    )
                ]

                result = (
                    self._conversion_evidence(
                        source,
                        destination,
                    )
                )

                enriched["verdict"] = (
                    result["verdict"]
                )

                enriched["confidence"] = (
                    result["confidence"]
                )

                enriched["evidence"] = (
                    result["evidence"]
                )

                if result["action"]:

                    enriched["action"] = (
                        result["action"]
                    )

        if self.evolution is not None:

            try:

                status = (
                    self.evolution.status()
                )

                enriched[
                    "build_trend"
                ] = status.get(
                    "trend"
                )

                enriched[
                    "build_error_delta"
                ] = status.get(
                    "error_delta"
                )

            except Exception:
                pass

        return enriched

    def _enrich_decisions(
        self,
        decisions,
    ):

        return [
            self._enrich_decision(
                decision
            )
            for decision in decisions
        ]

    def update(self):

        if not self.online:
            return False

        if self.registry is None:
            self.registry = DecisionRegistry()

        previous_decisions = list(
            self.registry.decisions
        )

        raw_decisions = evaluate_targets()

        self.last_decisions = (
            self._enrich_decisions(
                raw_decisions
            )
        )

        if self.history is not None:

            self.last_events = (
                self.history.process(
                    previous_decisions,
                    self.last_decisions,
                )
            )

        else:

            self.last_events = []

        self.registry.replace(
            self.last_decisions
        )

        self.registry.save()

        if self.knowledge is not None:

            self.knowledge.add(
                "Intelligence",
                "CurrentDecisions",
                len(self.last_decisions),
            )

            self.knowledge.add(
                "Intelligence",
                "DecisionEvents",
                len(self.last_events),
            )

            if self.last_decisions:

                top = self.last_decisions[0]

                self.knowledge.add(
                    "Intelligence",
                    "TopVerdict",
                    top.get("verdict"),
                )

                self.knowledge.add(
                    "Intelligence",
                    "TopConfidence",
                    top.get("confidence"),
                )

                self.knowledge.add(
                    "Intelligence",
                    "TopEvidence",
                    top.get("evidence"),
                )

        return True

    def shutdown(self):

        if self.registry is not None:
            self.registry.save()

        self.online = False
        return True

    def health(self):

        return (
            "ONLINE"
            if self.online
            else "OFFLINE"
        )

    def status(self):

        print("=" * 70)
        print("ENGINE BRAIN")
        print("=" * 70)

        print(
            f"Health            : "
            f"{self.health()}"
        )

        tracked = (
            self.registry.total()
            if self.registry is not None
            else 0
        )

        print(
            f"Tracked Decisions : "
            f"{tracked}"
        )

        print(
            f"Current Decisions : "
            f"{len(self.last_decisions)}"
        )

        if self.last_decisions:

            top = self.last_decisions[0]

            print()
            print("TOP DECISION")
            print("-" * 70)

            print(
                f"Category   : "
                f"{top['category']}"
            )

            print(
                f"Target     : "
                f"{top['target']}"
            )

            print(
                f"Impact     : "
                f"{top['impact']}"
            )

            print(
                f"Priority   : "
                f"{top['priority']}"
            )

            print(
                f"Verdict    : "
                f"{top.get('verdict')}"
            )

            print(
                f"Confidence : "
                f"{top.get('confidence')}"
            )

            print(
                f"Action     : "
                f"{top['action']}"
            )

            evidence = top.get(
                "evidence",
                []
            )

            if evidence:

                print("Evidence   :")

                for item in evidence:
                    print(
                        f"  - {item}"
                    )

        print("=" * 70)


if __name__ == "__main__":

    brain = EngineBrain()

    brain.startup()
    brain.update()
    brain.status()
    brain.shutdown()
