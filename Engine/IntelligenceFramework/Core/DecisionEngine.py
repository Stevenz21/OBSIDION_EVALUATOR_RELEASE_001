import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Engine.IntelligenceFramework.Core.StrikePlanner import plan_strikes


def _reference_evidence(category, target, reference):

    evidence = {
        "checked": False,
        "verdict": "UNVERIFIED",
        "source_known": None,
        "destination_known": None,
    }

    if reference is None:
        return evidence

    if category != "Conversion":
        return evidence

    if "->" not in target:
        return evidence

    source, destination = (
        part.strip()
        for part in target.split("->", 1)
    )

    source_known = reference.knows(source)
    destination_known = reference.knows(destination)

    evidence["checked"] = True
    evidence["source_known"] = source_known
    evidence["destination_known"] = destination_known

    if source_known and not destination_known:
        evidence["verdict"] = "REFERENCE_CONFLICT"

    elif destination_known and not source_known:
        evidence["verdict"] = "REFERENCE_SUPPORT"

    elif source_known and destination_known:
        evidence["verdict"] = "REFERENCE_AMBIGUOUS"

    else:
        evidence["verdict"] = "REFERENCE_UNKNOWN"

    return evidence


def evaluate_targets(targets=None, reference=None):

    if targets is None:
        targets = plan_strikes()

    decisions = []

    for category, target, impact in targets:

        if impact >= 200:
            priority = "★★★★★"
            action = "ATTACK IMMEDIATELY"

        elif impact >= 100:
            priority = "★★★★☆"
            action = "HIGH PRIORITY"

        elif impact >= 50:
            priority = "★★★☆☆"
            action = "PLAN NEXT"

        elif impact >= 20:
            priority = "★★☆☆☆"
            action = "SCHEDULE"

        else:
            priority = "★☆☆☆☆"
            action = "LOW PRIORITY"

        evidence = _reference_evidence(
            category,
            target,
            reference
        )

        if evidence["verdict"] == "REFERENCE_CONFLICT":
            action = "INVESTIGATE DIRECTION"

        decision = {
            "category": category,
            "target": target,
            "impact": impact,
            "priority": priority,
            "action": action,
            "reference": evidence,
        }

        decisions.append(decision)

    return decisions


def print_decisions(decisions, limit=10):

    print("=" * 70)
    print("ENGINE DECISION ENGINE")
    print("=" * 70)
    print()

    for i, decision in enumerate(decisions[:limit], 1):

        print("=" * 70)
        print(f"Decision #{i}")
        print("=" * 70)

        print(f"Category : {decision['category']}")
        print(f"Target   : {decision['target']}")
        print(f"Impact   : {decision['impact']}")
        print(f"Priority : {decision['priority']}")
        print(f"Action   : {decision['action']}")

        reference = decision.get("reference", {})

        if reference.get("checked"):
            print(
                f"Reference: {reference['verdict']}"
            )

        print()

    print("=" * 70)
    print("ENGINE DECISION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":

    decisions = evaluate_targets()
    print_decisions(decisions)
