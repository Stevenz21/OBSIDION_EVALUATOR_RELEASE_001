import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Engine.IntelligenceFramework.Core.SubsystemRegistry import SubsystemRegistry
from Engine.IntelligenceFramework.Core.SubsystemLoader import SubsystemLoader


class FrameworkManager:

    OBSIDION_ROOT = ROOT
    SERVUO_REFERENCE = Path(
        "/home/steven/Downloads/ServUO-57"
    )

    ORIONUO_REFERENCE = Path(
        "/home/steven/Desktop/Opened sources_Used For Refrences Only/OrionUO_Linux_Test"
    )

    REQUIRED_SUBSYSTEMS = {
        "ArchitectureIntelligence",
        "BuildIntelligence",
        "DecisionHistory",
        "DecisionRegistry",
        "EngineBrain",
        "EvolutionIntelligence",
        "KnowledgeSystem",
        "ProvenanceIntelligence",
        "ReferenceLearningSystem",
        "ReportingSystem",
    }

    def __init__(self):

        self.registry = SubsystemRegistry()
        self.loader = SubsystemLoader()
        self.brain = None
        self.online = False
        self.connections = []

    def register(self, name, subsystem):

        self.registry.register(name, subsystem)

    def _system(self, name):

        return self.registry.get(name)

    def _start_subsystems(self):

        print()
        print("[FRAMEWORK] Starting subsystems...")

        for name in self.registry.names():

            subsystem = self.registry.get(name)

            try:
                startup = getattr(subsystem, "startup", None)

                if startup is None:
                    # FrameworkSubsystem may provide behavior through
                    # inheritance; otherwise discovery itself is sufficient.
                    print(f"[ONLINE] {name}")
                    continue

                if startup():
                    print(f"[ONLINE] {name}")
                else:
                    print(f"[FAILED] {name}")

            except Exception as ex:
                print(f"[FAILED] {name}: {ex}")

    def _bind(self, source_name, target_name, channel):

        source = self._system(source_name)
        target = self._system(target_name)

        if source is None:
            raise RuntimeError(
                f"Cannot wire missing source subsystem: {source_name}"
            )

        if target is None:
            raise RuntimeError(
                f"Cannot wire missing target subsystem: {target_name}"
            )

        bindings = getattr(target, "bindings", None)

        if bindings is None:
            bindings = {}
            setattr(target, "bindings", bindings)

        bindings[source_name] = source

        connection = {
            "source": source_name,
            "target": target_name,
            "channel": channel,
        }

        if connection not in self.connections:
            self.connections.append(connection)

        print(
            f"[WIRED] {source_name} -> {target_name} [{channel}]"
        )

        return True

    def _wire_ecosystem(self):

        self.connections = []

        self.brain = self._system("EngineBrain")

        if self.brain is None:
            raise RuntimeError(
                "EngineBrain subsystem was not discovered"
            )

        systems = {
            name: self._system(name)
            for name in self.REQUIRED_SUBSYSTEMS
        }

        missing = [
            name
            for name, subsystem in systems.items()
            if subsystem is None
        ]

        if missing:
            raise RuntimeError(
                "Cannot wire incomplete EIF ecosystem: "
                + ", ".join(sorted(missing))
            )

        self.brain.wire(
            registry=systems["DecisionRegistry"],
            history=systems["DecisionHistory"],
            knowledge=systems["KnowledgeSystem"],
            architecture=systems["ArchitectureIntelligence"],
            reference=systems["ReferenceLearningSystem"],
            build_intelligence=systems["BuildIntelligence"],
            provenance=systems["ProvenanceIntelligence"],
            evolution=systems["EvolutionIntelligence"],
        )

        print()
        print("[FRAMEWORK] Wiring complete EIF ecosystem...")

        edges = [
            ("ArchitectureIntelligence", "ProvenanceIntelligence", "active architecture evidence"),
            ("ReferenceLearningSystem", "ProvenanceIntelligence", "reference architecture evidence"),
            ("BuildIntelligence", "EvolutionIntelligence", "completed build state"),
            ("ArchitectureIntelligence", "KnowledgeSystem", "architecture facts"),
            ("ReferenceLearningSystem", "KnowledgeSystem", "reference facts"),
            ("ProvenanceIntelligence", "KnowledgeSystem", "provenance facts"),
            ("BuildIntelligence", "KnowledgeSystem", "build facts"),
            ("EvolutionIntelligence", "KnowledgeSystem", "evolution facts"),
            ("DecisionRegistry", "EngineBrain", "decision registry"),
            ("DecisionHistory", "EngineBrain", "decision history"),
            ("KnowledgeSystem", "EngineBrain", "shared knowledge"),
            ("ArchitectureIntelligence", "EngineBrain", "architecture evidence"),
            ("ReferenceLearningSystem", "EngineBrain", "reference evidence"),
            ("BuildIntelligence", "EngineBrain", "compiler evidence"),
            ("ProvenanceIntelligence", "EngineBrain", "lineage evidence"),
            ("EvolutionIntelligence", "EngineBrain", "build evolution evidence"),
            ("EngineBrain", "DecisionRegistry", "current decisions"),
            ("EngineBrain", "DecisionHistory", "decision evolution"),
            ("ArchitectureIntelligence", "ReportingSystem", "architecture report"),
            ("ReferenceLearningSystem", "ReportingSystem", "reference report"),
            ("ProvenanceIntelligence", "ReportingSystem", "provenance report"),
            ("BuildIntelligence", "ReportingSystem", "build report"),
            ("EvolutionIntelligence", "ReportingSystem", "evolution report"),
            ("KnowledgeSystem", "ReportingSystem", "knowledge report"),
            ("DecisionRegistry", "ReportingSystem", "decision registry report"),
            ("DecisionHistory", "ReportingSystem", "decision history report"),
            ("EngineBrain", "ReportingSystem", "intelligence report"),
        ]

        for source, target, channel in edges:
            self._bind(source, target, channel)

        knowledge = systems["KnowledgeSystem"]
        knowledge.add(
            "Framework",
            "Subsystems",
            sorted(self.REQUIRED_SUBSYSTEMS),
        )
        knowledge.add(
            "Framework",
            "Connections",
            list(self.connections),
        )
        knowledge.add(
            "Framework",
            "ConnectionCount",
            len(self.connections),
        )

        print()
        print(
            f"[FRAMEWORK] Ecosystem connections : {len(self.connections)}"
        )

        return True

    def _run_architecture_intelligence(self):

        architecture = self._system(
            "ArchitectureIntelligence"
        )

        knowledge = self._system(
            "KnowledgeSystem"
        )

        if architecture is None:
            return

        print()
        print(
            "[ARCHITECTURE] Analyzing OBSIDION architecture..."
        )

        try:
            stats = architecture.analyze(
                self.OBSIDION_ROOT
            )

            print(
                "[ARCHITECTURE] "
                f"{stats.get('files_scanned', 0)} files, "
                f"{stats.get('types_discovered', 0)} types, "
                f"{stats.get('inheritance_edges', 0)} "
                "inheritance edges"
            )

            if knowledge is not None:

                for key, value in stats.items():
                    knowledge.add(
                        "Architecture",
                        key,
                        value
                    )

                for type_name in (
                    "OBSIDION_ENGINE.Runtime.Item",
                    "Server.Item",
                    "Server.Items.Item",
                ):

                    knowledge.add(
                        "ArchitectureTypes",
                        type_name,
                        architecture.get_type(type_name)
                    )

                    knowledge.add(
                        "ArchitectureParents",
                        type_name,
                        architecture.inheritance_parents(
                            type_name
                        )
                    )

        except Exception as ex:
            print(
                f"[ARCHITECTURE] Analysis failed: {ex}"
            )

    def _run_reference_learning(self):

        reference = self._system(
            "ReferenceLearningSystem"
        )

        knowledge = self._system(
            "KnowledgeSystem"
        )

        if reference is None:
            return

        print()
        print(
            "[REFERENCE] Learning ServUO architecture..."
        )

        try:

            if not self.SERVUO_REFERENCE.exists():
                print(
                    "[REFERENCE] ServUO reference not found:",
                    self.SERVUO_REFERENCE
                )
                return

            stats = reference.learn_servuo(
                self.SERVUO_REFERENCE
            )

            print(
                "[LEARNED] ServUO : "
                f"{stats['files_scanned']} files, "
                f"{stats['types_learned']} types"
            )

            if knowledge is not None:

                knowledge.add(
                    "Reference",
                    "ServUOFiles",
                    stats["files_scanned"]
                )

                knowledge.add(
                    "Reference",
                    "ServUOTypes",
                    stats["types_learned"]
                )

                knowledge.add(
                    "Reference",
                    "Server.Item",
                    reference.get_type(
                        "Server.Item"
                    )
                )

                knowledge.add(
                    "Reference",
                    "Server.Items.Item",
                    reference.get_type(
                        "Server.Items.Item"
                    )
                )

        except Exception as ex:
            print(
                f"[REFERENCE] ServUO learning failed: {ex}"
            )

        print()
        print(
            "[REFERENCE] Learning OrionUO architecture..."
        )

        try:

            if not self.ORIONUO_REFERENCE.exists():
                print(
                    "[REFERENCE] OrionUO reference not found:",
                    self.ORIONUO_REFERENCE
                )
                return

            stats = reference.learn_orionuo(
                self.ORIONUO_REFERENCE
            )

            print(
                "[LEARNED] OrionUO : "
                f"{stats['files_scanned']} files, "
                f"{stats['types_learned']} types, "
                f"{stats['inheritance_edges']} inheritance edges"
            )

            if knowledge is not None:

                knowledge.add(
                    "Reference",
                    "OrionUOFiles",
                    stats["files_scanned"]
                )

                knowledge.add(
                    "Reference",
                    "OrionUOTypes",
                    stats["types_learned"]
                )

                knowledge.add(
                    "Reference",
                    "OrionUONodes",
                    stats["nodes"]
                )

                knowledge.add(
                    "Reference",
                    "OrionUOEdges",
                    stats["edges"]
                )

                knowledge.add(
                    "Reference",
                    "OrionUOInheritance",
                    stats["inheritance_edges"]
                )

        except Exception as ex:
            print(
                f"[REFERENCE] OrionUO learning failed: {ex}"
            )

    def _run_provenance_intelligence(self):

        provenance = self._system(
            "ProvenanceIntelligence"
        )

        architecture = self._system(
            "ArchitectureIntelligence"
        )

        reference = self._system(
            "ReferenceLearningSystem"
        )

        knowledge = self._system(
            "KnowledgeSystem"
        )

        if provenance is None:
            return

        print()
        print("[PROVENANCE] Building evidence lineage...")

        stats = provenance.analyze(
            architecture=architecture,
            reference=reference,
        )

        print(
            "[PROVENANCE] "
            f"{stats.get('concepts', 0)} concepts, "
            f"{stats.get('relationships', 0)} relationships, "
            f"{stats.get('compatibility_links', 0)} compatibility links"
        )

        if knowledge is not None:
            for key, value in stats.items():
                knowledge.add(
                    "Provenance",
                    key,
                    value,
                )

    def _run_build_intelligence(self):

        build = self._system(
            "BuildIntelligence"
        )

        knowledge = self._system(
            "KnowledgeSystem"
        )

        if build is None:
            return

        print()
        print("[BUILD] Running build intelligence...")

        try:
            result = build.analyze()

            print("[BUILD] Analysis complete")

            if knowledge is not None:

                knowledge.add(
                    "Build",
                    "CompilerCodes",
                    build.compiler_codes()
                )

                knowledge.add(
                    "Build",
                    "MissingMembers",
                    build.missing_members()
                )

                knowledge.add(
                    "Build",
                    "MissingTypes",
                    build.missing_types()
                )

                knowledge.add(
                    "Build",
                    "Conversions",
                    build.conversions()
                )

                knowledge.add(
                    "Build",
                    "TotalFamilies",
                    build.total_families()
                )

        except Exception as ex:
            print(
                f"[BUILD] Analysis failed: {ex}"
            )

    def _run_evolution_intelligence(self):

        evolution = self._system(
            "EvolutionIntelligence"
        )

        knowledge = self._system(
            "KnowledgeSystem"
        )

        if evolution is None:
            return

        print()
        print(
            "[EVOLUTION] Comparing runtime builds..."
        )

        try:

            status = evolution.analyze()

            print(
                "[EVOLUTION] Trend      : "
                f"{status['trend']}"
            )

            delta = status.get(
                "error_delta"
            )

            if delta is None:
                delta_text = "BASELINE"
            elif delta > 0:
                delta_text = f"+{delta}"
            else:
                delta_text = str(delta)

            print(
                "[EVOLUTION] Error Delta: "
                f"{delta_text}"
            )

            print(
                "[EVOLUTION] New        : "
                f"{status['new_signatures']}"
            )

            print(
                "[EVOLUTION] Resolved   : "
                f"{status['resolved_signatures']}"
            )

            if knowledge is not None:

                for key, value in status.items():

                    knowledge.add(
                        "Evolution",
                        key,
                        value,
                    )

        except Exception as ex:

            print(
                "[EVOLUTION] Analysis failed: "
                f"{ex}"
            )

    def _run_brain(self):

        print()
        print("[INTELLIGENCE] Running integrated analysis...")

        if not self.brain.update():
            raise RuntimeError(
                "EngineBrain update failed"
            )

        knowledge = self._system(
            "KnowledgeSystem"
        )

        history = self._system(
            "DecisionHistory"
        )

        if knowledge is not None:

            knowledge.add(
                "Intelligence",
                "CurrentDecisions",
                len(self.brain.last_decisions)
            )

            knowledge.add(
                "Intelligence",
                "HistoryEvents",
                history.total_events()
                if history is not None
                else 0
            )

            if self.brain.last_decisions:

                top = self.brain.last_decisions[0]

                knowledge.add(
                    "Intelligence",
                    "TopCategory",
                    top["category"]
                )

                knowledge.add(
                    "Intelligence",
                    "TopTarget",
                    top["target"]
                )

                knowledge.add(
                    "Intelligence",
                    "TopImpact",
                    top["impact"]
                )

                knowledge.add(
                    "Intelligence",
                    "TopPriority",
                    top["priority"]
                )

                knowledge.add(
                    "Intelligence",
                    "TopAction",
                    top["action"]
                )

    def _generate_report(self):

        reporting = self._system(
            "ReportingSystem"
        )

        if reporting is None:
            return

        try:
            report_path = reporting.generate(self)

            print()
            print(
                f"[REPORT] Generated : {report_path}"
            )

        except Exception as ex:
            print()
            print(
                f"[REPORT] Failed : {ex}"
            )

    def _print_status(self):

        print()
        print("Subsystem Status")
        print("-" * 70)

        for name in self.registry.names():

            subsystem = self.registry.get(name)

            try:
                health = getattr(
                    subsystem,
                    "health",
                    None
                )

                status = (
                    health()
                    if health is not None
                    else "ONLINE"
                )

            except Exception:
                status = "UNKNOWN"

            print(f"[{status}] {name}")

        print()
        print(
            f"Subsystems Registered : "
            f"{self.registry.total()}"
        )

        print(
            f"Current Decisions     : "
            f"{len(self.brain.last_decisions)}"
        )

        architecture = self._system(
            "ArchitectureIntelligence"
        )

        if architecture is not None:
            print(
                "Architecture Types    : "
                f"{len(architecture.types)}"
            )

            print(
                "Architecture Edges    : "
                f"{architecture.edge_count()}"
            )

        reference = self._system(
            "ReferenceLearningSystem"
        )

        if reference is not None:
            print(
                "Reference Types       : "
                f"{len(reference.types)}"
            )

        decision_registry = self._system(
            "DecisionRegistry"
        )

        if decision_registry is not None:
            print(
                "Registry Decisions    : "
                f"{decision_registry.total()}"
            )

        if self.brain.last_decisions:

            top = self.brain.last_decisions[0]

            print()
            print("TOP INTELLIGENCE DECISION")
            print("-" * 70)
            print(
                f"Category : {top['category']}"
            )
            print(
                f"Target   : {top['target']}"
            )
            print(
                f"Impact   : {top['impact']}"
            )
            print(
                f"Priority : {top['priority']}"
            )
            print(
                f"Action   : {top['action']}"
            )


    def _framework_ecosystem_inventory(self):

        import ast
        import json

        framework_root = (
            self.OBSIDION_ROOT
            / "Engine"
            / "IntelligenceFramework"
        )

        files = []
        modules = []
        import_edges = []

        for path in sorted(framework_root.rglob("*")):

            if not path.is_file():
                continue

            if "__pycache__" in path.parts:
                continue

            if path.suffix.lower() == ".pyc":
                continue

            relative = path.relative_to(
                framework_root
            ).as_posix()

            lower_name = path.name.lower()

            if (
                ".bak." in lower_name
                or ".backup." in lower_name
                or lower_name.endswith("~")
            ):
                classification = "BACKUP"

            elif path.name == "FRAMEWORK_MANIFEST.json":
                classification = "MANIFEST"

            elif relative.startswith("History/"):
                classification = "STATE"

            elif (
                relative.startswith("Reports/")
                and path.suffix.lower() == ".html"
            ):
                classification = "GENERATED_REPORT"

            elif path.suffix.lower() == ".sh":
                classification = "BUILD_SCRIPT"

            elif path.suffix.lower() == ".py":

                if path.name == "__init__.py":
                    classification = "PACKAGE"
                elif relative.startswith("Core/"):
                    classification = "CORE_MODULE"
                elif relative.startswith("Analyzers/"):
                    classification = "ANALYZER"
                elif relative.startswith("Assimilation/"):
                    classification = "ASSIMILATION"
                elif relative.startswith("Build/"):
                    classification = "BUILD_MODULE"
                elif relative.startswith("Knowledge/"):
                    classification = "KNOWLEDGE_MODULE"
                elif relative.startswith("Registry/"):
                    classification = "REGISTRY_MODULE"
                elif relative.startswith("Reports/"):
                    classification = "REPORT_MODULE"
                else:
                    classification = "PYTHON_MODULE"

            else:
                classification = "FRAMEWORK_ASSET"

            files.append(
                {
                    "path": relative,
                    "classification": classification,
                }
            )

            if path.suffix.lower() != ".py":
                continue

            module = (
                path.relative_to(
                    self.OBSIDION_ROOT
                )
                .with_suffix("")
                .as_posix()
                .replace("/", ".")
            )

            modules.append(module)

            try:

                tree = ast.parse(
                    path.read_text(
                        encoding="utf-8",
                        errors="replace",
                    )
                )

            except Exception:
                continue

            for node in ast.walk(tree):

                if isinstance(node, ast.Import):
                    names = [
                        alias.name
                        for alias in node.names
                    ]

                elif isinstance(node, ast.ImportFrom):
                    names = (
                        [node.module]
                        if node.module
                        else []
                    )

                else:
                    continue

                for dependency in names:

                    if (
                        dependency
                        and dependency.startswith(
                            "Engine.IntelligenceFramework"
                        )
                    ):

                        import_edges.append(
                            {
                                "dependency": dependency,
                                "consumer": module,
                                "relation": "IMPORTS",
                            }
                        )

        manifest_path = (
            framework_root
            / "FRAMEWORK_MANIFEST.json"
        )

        manifest = {}

        if manifest_path.exists():

            try:
                manifest = json.loads(
                    manifest_path.read_text(
                        encoding="utf-8"
                    )
                )
            except Exception:
                manifest = {}

        return {
            "files": files,
            "modules": sorted(set(modules)),
            "import_edges": import_edges,
            "manifest": manifest,
        }

    def _print_framework_ecosystem(self):

        inventory = (
            self._framework_ecosystem_inventory()
        )

        files = inventory["files"]

        counts = {}

        for item in files:

            classification = item[
                "classification"
            ]

            counts[classification] = (
                counts.get(
                    classification,
                    0
                )
                + 1
            )

        active = [
            item
            for item in files
            if item["classification"]
            not in {
                "BACKUP",
                "STATE",
                "GENERATED_REPORT",
            }
        ]

        print()
        print(
            "[FRAMEWORK] Complete EIF ecosystem inventory..."
        )

        print(
            "[FRAMEWORK] Physical files       : "
            f"{len(files)}"
        )

        print(
            "[FRAMEWORK] Active artifacts     : "
            f"{len(active)}"
        )

        print(
            "[FRAMEWORK] Python modules       : "
            f"{len(inventory['modules'])}"
        )

        print(
            "[FRAMEWORK] Internal import links: "
            f"{len(inventory['import_edges'])}"
        )

        print(
            "[FRAMEWORK] Runtime subsystems   : "
            f"{self.registry.total()}"
        )

        print()

        for classification in sorted(counts):

            print(
                "[FRAMEWORK CLASS] "
                f"{classification:<18} "
                f"{counts[classification]}"
            )

        print()
        print(
            "[FRAMEWORK] Active component registry"
        )

        for item in active:

            print(
                "[COMPONENT] "
                f"{item['path']} "
                f"[{item['classification']}]"
            )

        return inventory

    def boot(self):

        print("=" * 70)
        print("ENGINE INTELLIGENCE FRAMEWORK")
        print("=" * 70)
        print()

        print(
            "[FRAMEWORK] Discovering subsystems..."
        )

        systems = self.loader.load()

        for subsystem in systems:
            self.register(
                subsystem.NAME,
                subsystem
            )

        self._print_framework_ecosystem()

        self._start_subsystems()

        # Manager is the composition root. All shared dependencies are
        # connected before intelligence processing begins.
        self._wire_ecosystem()

        # Intelligence pipeline.
        self._run_architecture_intelligence()
        self._run_reference_learning()
        self._run_provenance_intelligence()
        self._run_build_intelligence()
        self._run_evolution_intelligence()
        self._run_brain()
        self._generate_report()

        self.online = True

        self._print_status()

        print()
        print("Framework Status : ONLINE")
        print("=" * 70)

        return True

    def shutdown(self):

        print("[FRAMEWORK] Shutting down...")

        for name in reversed(
            self.registry.names()
        ):

            subsystem = self.registry.get(name)

            try:
                shutdown = getattr(
                    subsystem,
                    "shutdown",
                    None
                )

                if shutdown is not None:
                    shutdown()

            except Exception as ex:
                print(
                    f"[SHUTDOWN ERROR] "
                    f"{name}: {ex}"
                )

        self.online = False

        print("[FRAMEWORK] Offline")

        return True


if __name__ == "__main__":

    manager = FrameworkManager()
    manager.boot()
