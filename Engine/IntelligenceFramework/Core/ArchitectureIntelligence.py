import re
import fnmatch
import json
import subprocess
import xml.etree.ElementTree as ET

from collections import defaultdict
from pathlib import Path

from Engine.IntelligenceFramework.Core.FrameworkSubsystem import FrameworkSubsystem


class ArchitectureIntelligence(FrameworkSubsystem):

    NAME = "ArchitectureIntelligence"
    VERSION = "3.0.0"
    CATEGORY = "Architecture"

    EXCLUDED_DIRS = {
        ".git",
        ".idea",
        ".vs",
        ".venv",
        "__pycache__",
        "bin",
        "obj",
    }

    TYPE_PATTERN = re.compile(
        r"""
        \b
        (?P<kind>class|interface|struct|enum)
        \s+
        (?P<name>[A-Za-z_][A-Za-z0-9_]*)
        (?P<generic>\s*<[^>{;\n]+>)?
        (?P<inheritance>\s*:\s*[^{\n]+)?
        """,
        re.VERBOSE,
    )

    NAMESPACE_PATTERN = re.compile(
        r"\bnamespace\s+([A-Za-z_][A-Za-z0-9_.]*)"
    )

    BLOCK_COMMENT_PATTERN = re.compile(
        r"/\*.*?\*/",
        re.DOTALL,
    )

    LINE_COMMENT_PATTERN = re.compile(
        r"//.*?$",
        re.MULTILINE,
    )

    def __init__(self):

        self.online = False
        self.root = None
        self.project_file = None

        # ------------------------------------------------------
        # ACTIVE architecture graph
        # ------------------------------------------------------

        self.nodes = {}
        self.edges = []

        self.outgoing = defaultdict(list)
        self.incoming = defaultdict(list)
        self._edge_index = set()

        self.types = {}
        self.simple_names = defaultdict(set)

        # ------------------------------------------------------
        # HISTORICAL / EXCLUDED architecture graph
        # ------------------------------------------------------

        self.historical_nodes = {}
        self.historical_edges = []

        self.historical_outgoing = defaultdict(list)
        self.historical_incoming = defaultdict(list)
        self._historical_edge_index = set()

        self.historical_types = {}
        self.historical_simple_names = defaultdict(set)

        # ------------------------------------------------------
        # Project/source model
        # ------------------------------------------------------

        self.project_includes = []
        self.project_removes = []

        self.active_sources = set()
        self.excluded_sources = set()

        self.stats = {}

    # ==========================================================
    # Lifecycle
    # ==========================================================

    def startup(self):

        self.online = True
        return True

    def shutdown(self):

        self.online = False
        return True

    def health(self):

        return "ONLINE" if self.online else "OFFLINE"

    # ==========================================================
    # Graph
    # ==========================================================

    def add_node(self, node_type, name, **metadata):

        # One graph node per qualified type identity. Kind is metadata,
        # never part of identity.
        key = f"Type:{name}"

        node = self.nodes.get(key)

        if node is None:
            node = {
                "type": node_type,
                "name": name,
            }
            self.nodes[key] = node

        elif node.get("type") == "Type" and node_type != "Type":
            node["type"] = node_type

        node.update(metadata)
        return key

    def add_edge(self, source, relation, target, **metadata):

        edge_key = (
            source,
            relation,
            target,
            metadata.get("source_file"),
        )

        if edge_key in self._edge_index:
            return None

        edge = {
            "source": source,
            "relation": relation,
            "target": target,
        }

        edge.update(metadata)

        self.edges.append(edge)
        self.outgoing[source].append(edge)
        self.incoming[target].append(edge)

        self._edge_index.add(edge_key)

        return edge

    def _add_historical_node(
        self,
        node_type,
        name,
        **metadata,
    ):

        key = f"Type:{name}"

        node = self.historical_nodes.get(key)

        if node is None:
            node = {
                "type": node_type,
                "name": name,
            }
            self.historical_nodes[key] = node

        elif node.get("type") == "Type" and node_type != "Type":
            node["type"] = node_type

        node.update(metadata)
        return key

    def _add_historical_edge(
        self,
        source,
        relation,
        target,
        **metadata,
    ):

        edge_key = (
            source,
            relation,
            target,
            metadata.get("source_file"),
        )

        if edge_key in self._historical_edge_index:
            return None

        edge = {
            "source": source,
            "relation": relation,
            "target": target,
        }

        edge.update(metadata)

        self.historical_edges.append(edge)
        self.historical_outgoing[source].append(edge)
        self.historical_incoming[target].append(edge)

        self._historical_edge_index.add(edge_key)

        return edge

    def node_count(self):

        return len(self.nodes)

    def edge_count(self):

        return len(self.edges)

    def children_of(self, node):

        return [
            edge["target"]
            for edge in self.outgoing.get(node, [])
            if edge["relation"] == "inherits"
        ]

    def parents_of(self, node):

        return [
            edge["source"]
            for edge in self.incoming.get(node, [])
            if edge["relation"] == "inherits"
        ]

    # ==========================================================
    # Runtime.csproj intelligence
    # ==========================================================

    def load_project(
        self,
        project_file=None,
    ):

        if self.root is None:
            raise RuntimeError(
                "Architecture root has not been configured"
            )

        if project_file is None:
            project_file = self.root / "Runtime.csproj"

        project_file = Path(project_file).resolve()

        if not project_file.exists():
            raise FileNotFoundError(
                f"Runtime project not found: {project_file}"
            )

        self.project_file = project_file

        tree = ET.parse(project_file)
        xml_root = tree.getroot()

        includes = []
        removes = []

        default_compile_items = True

        for element in xml_root.iter():

            tag = element.tag.split("}")[-1]

            if tag == "EnableDefaultCompileItems":

                value = (element.text or "").strip().lower()

                default_compile_items = (
                    value not in {
                        "false",
                        "0",
                        "no",
                    }
                )

            if tag != "Compile":
                continue

            include = element.attrib.get("Include")
            remove = element.attrib.get("Remove")

            if include:
                includes.append(
                    self._normalize_pattern(include)
                )

            if remove:
                removes.append(
                    self._normalize_pattern(remove)
                )

        self.project_includes = includes
        self.project_removes = removes

        return {
            "project": str(
                project_file.relative_to(self.root)
            ),
            "default_compile_items": default_compile_items,
            "includes": list(includes),
            "removes": list(removes),
        }

    def _normalize_pattern(self, value):

        value = str(value).strip()

        value = value.replace("\\", "/")

        while value.startswith("./"):
            value = value[2:]

        return value

    def _relative_source(self, path):

        path = Path(path).resolve()

        try:
            return path.relative_to(
                self.root
            ).as_posix()

        except ValueError:
            return path.as_posix()

    def _glob_match(self, relative_path, pattern):

        relative_path = self._normalize_pattern(
            relative_path
        )

        pattern = self._normalize_pattern(
            pattern
        )

        # Paths outside the project root cannot be part of the
        # active Runtime.csproj source surface.
        if pattern.startswith("../"):
            return False

        return fnmatch.fnmatchcase(
            relative_path,
            pattern,
        )

    def _matches_any(self, relative_path, patterns):

        return any(
            self._glob_match(
                relative_path,
                pattern,
            )
            for pattern in patterns
        )

    def _hard_excluded(self, path):

        return any(
            part in self.EXCLUDED_DIRS
            for part in path.parts
        )

    def source_status(self, path):

        if self.root is None:
            return "UNKNOWN"

        path = Path(path)

        if not path.is_absolute():
            path = self.root / path

        path = path.resolve()

        if self._hard_excluded(path):
            return "EXCLUDED"

        relative = self._relative_source(path)

        if self._matches_any(
            relative,
            self.project_removes,
        ):
            return "EXCLUDED"

        if self._matches_any(
            relative,
            self.project_includes,
        ):
            return "ACTIVE"

        return "HISTORICAL"

    def discover_active_sources(self):

        if self.root is None:
            raise RuntimeError(
                "Architecture root has not been configured"
            )

        if self.project_file is None:
            raise RuntimeError(
                "Runtime project has not been loaded"
            )

        command = [
            "dotnet",
            "msbuild",
            str(self.project_file),
            "-getItem:Compile",
            "-getProperty:EnableDefaultCompileItems",
        ]

        try:
            result = subprocess.run(
                command,
                cwd=self.root,
                capture_output=True,
                text=True,
                check=True,
            )
        except FileNotFoundError as exc:
            raise RuntimeError(
                "dotnet was not found; MSBuild compile "
                "surface cannot be evaluated"
            ) from exc
        except subprocess.CalledProcessError as exc:
            message = (
                exc.stderr.strip()
                or exc.stdout.strip()
                or "unknown MSBuild failure"
            )

            raise RuntimeError(
                "MSBuild compile-surface evaluation failed: "
                + message
            ) from exc

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "MSBuild did not return a valid JSON "
                "compile surface"
            ) from exc

        compile_items = (
            data
            .get("Items", {})
            .get("Compile", [])
        )

        sources = set()

        for item in compile_items:

            full_path = item.get("FullPath")

            if not full_path:
                identity = item.get("Identity")

                if not identity:
                    continue

                source = self.root / identity

            else:
                source = Path(full_path)

            if source.suffix.lower() != ".cs":
                continue

            if not source.is_file():
                continue

            sources.add(source)

        self.active_sources = {
            self._relative_source(source)
            for source in sources
        }

        return sorted(
            sources,
            key=lambda p: p.as_posix(),
        )

    def discover_excluded_sources(self):

        # Architecture Intelligence 2.1
        #
        # Normal architecture analysis is ACTIVE-PROJECT ONLY.
        #
        # Runtime.csproj Compile Remove entries are filters, not
        # additional discovery roots. Expanding patterns such as
        # **/backup/**/*.cs causes pathlib to recursively crawl the
        # entire OBSIDION repository.
        #
        # Historical/reference architecture will be learned by a
        # separate assimilation/reference pass when explicitly
        # requested.

        self.excluded_sources = set()

        return []

    # ==========================================================
    # Source parsing
    # ==========================================================

    def _strip_comments(self, text):

        text = self.BLOCK_COMMENT_PATTERN.sub(
            "",
            text,
        )

        text = self.LINE_COMMENT_PATTERN.sub(
            "",
            text,
        )

        return text

    def _namespace_for_position(
        self,
        text,
        position,
    ):

        namespace = None

        for match in self.NAMESPACE_PATTERN.finditer(
            text,
            0,
            position,
        ):
            namespace = match.group(1)

        return namespace

    def _clean_type_name(self, value):

        value = value.strip()

        value = value.replace(
            "global::",
            "",
        )

        value = re.sub(
            r"<.*>",
            "",
            value,
        )

        value = value.split(
            "where",
            1,
        )[0].strip()

        return value

    def _qualify(self, name, namespace):

        name = self._clean_type_name(name)

        if not name:
            return None

        if "." in name:
            return name

        if namespace:
            return f"{namespace}.{name}"

        return name

    # ==========================================================
    # Type registration
    # ==========================================================

    def _register_type(
        self,
        kind,
        name,
        namespace,
        source,
        historical=False,
    ):

        full_name = self._qualify(
            name,
            namespace,
        )

        if not full_name:
            return None

        if historical:

            store = self.historical_types
            simple_names = (
                self.historical_simple_names
            )

        else:

            store = self.types
            simple_names = self.simple_names

        record = store.get(full_name)

        if record is None:

            record = {
                "name": name,
                "full_name": full_name,
                "namespace": namespace,
                "kind": kind,
                "sources": [],
                "status": (
                    "HISTORICAL"
                    if historical
                    else "ACTIVE"
                ),
            }

            store[full_name] = record

        if source not in record["sources"]:
            record["sources"].append(source)

        simple_names[name].add(full_name)

        if historical:

            self._add_historical_node(
                kind.capitalize(),
                full_name,
                namespace=namespace,
                source=source,
                status="HISTORICAL",
            )

        else:

            self.add_node(
                kind.capitalize(),
                full_name,
                namespace=namespace,
                source=source,
                status="ACTIVE",
            )

        return full_name

    def _resolve_parent(
        self,
        parent,
        namespace,
        historical=False,
    ):

        parent = self._clean_type_name(
            parent
        )

        if not parent:
            return None

        if "." in parent:
            return parent

        simple_names = (
            self.historical_simple_names
            if historical
            else self.simple_names
        )

        candidates = simple_names.get(
            parent,
            set(),
        )

        same_namespace = (
            f"{namespace}.{parent}"
            if namespace
            else parent
        )

        if same_namespace in candidates:
            return same_namespace

        if len(candidates) == 1:
            return next(iter(candidates))

        # If active resolution failed, an active parent may still
        # be a known active type registered under a simple name.
        if not historical:

            active_candidates = self.simple_names.get(
                parent,
                set(),
            )

            if len(active_candidates) == 1:
                return next(iter(active_candidates))

        # Preserve unresolved identity instead of inventing one.
        return parent

    def _scan_file(
        self,
        path,
        historical=False,
    ):

        try:

            raw = path.read_text(
                encoding="utf-8",
                errors="ignore",
            )

        except OSError:
            return []

        text = self._strip_comments(raw)

        declarations = []

        source = self._relative_source(path)

        for match in self.TYPE_PATTERN.finditer(text):

            kind = match.group("kind")
            name = match.group("name")

            namespace = self._namespace_for_position(
                text,
                match.start(),
            )

            full_name = self._register_type(
                kind,
                name,
                namespace,
                source,
                historical=historical,
            )

            if full_name is None:
                continue

            inheritance = match.group(
                "inheritance"
            )

            parents = []

            if inheritance:

                inheritance = inheritance.lstrip()
                inheritance = inheritance[1:].strip()

                for parent in inheritance.split(","):

                    parent = self._clean_type_name(
                        parent
                    )

                    if parent:
                        parents.append(parent)

            declarations.append(
                {
                    "kind": kind,
                    "name": name,
                    "full_name": full_name,
                    "namespace": namespace,
                    "parents": parents,
                    "source": source,
                    "status": (
                        "HISTORICAL"
                        if historical
                        else "ACTIVE"
                    ),
                }
            )

        return declarations

    # ==========================================================
    # Relationship construction
    # ==========================================================

    def _build_relationships(
        self,
        declarations,
        historical=False,
    ):

        count = 0

        for declaration in declarations:

            child = declaration["full_name"]
            namespace = declaration["namespace"]

            if historical:

                child_key = self._add_historical_node(
                    declaration["kind"].capitalize(),
                    child,
                    namespace=namespace,
                    source=declaration["source"],
                    status="HISTORICAL",
                )

            else:

                child_key = self.add_node(
                    declaration["kind"].capitalize(),
                    child,
                    namespace=namespace,
                    source=declaration["source"],
                    status="ACTIVE",
                )

            for parent in declaration["parents"]:

                parent_name = self._resolve_parent(
                    parent,
                    namespace,
                    historical=historical,
                )

                if not parent_name:
                    continue

                if historical:

                    parent_key = (
                        self._add_historical_node(
                            "Type",
                            parent_name,
                            status="HISTORICAL",
                        )
                    )

                    before = len(
                        self.historical_edges
                    )

                    self._add_historical_edge(
                        parent_key,
                        "inherits",
                        child_key,
                        source_file=declaration[
                            "source"
                        ],
                        status="HISTORICAL",
                    )

                    if (
                        len(self.historical_edges)
                        > before
                    ):
                        count += 1

                else:

                    parent_key = self.add_node(
                        "Type",
                        parent_name,
                        status="ACTIVE",
                    )

                    before = self.edge_count()

                    self.add_edge(
                        parent_key,
                        "inherits",
                        child_key,
                        source_file=declaration[
                            "source"
                        ],
                        status="ACTIVE",
                    )

                    if self.edge_count() > before:
                        count += 1

        return count

    # ==========================================================
    # Main analysis
    # ==========================================================

    def analyze(
        self,
        root,
        project_file=None,
    ):

        self.root = Path(root).resolve()

        # Active graph
        self.nodes.clear()
        self.edges.clear()
        self.outgoing.clear()
        self.incoming.clear()
        self._edge_index.clear()

        self.types.clear()
        self.simple_names.clear()

        # Historical graph
        self.historical_nodes.clear()
        self.historical_edges.clear()
        self.historical_outgoing.clear()
        self.historical_incoming.clear()
        self._historical_edge_index.clear()

        self.historical_types.clear()
        self.historical_simple_names.clear()

        self.active_sources.clear()
        self.excluded_sources.clear()

        project = self.load_project(
            project_file
        )

        active_paths = self.discover_active_sources()

        historical_paths = (
            self.discover_excluded_sources()
        )

        active_declarations = []
        historical_declarations = []

        # ------------------------------------------------------
        # Pass 1A: ACTIVE project architecture
        # ------------------------------------------------------

        for path in active_paths:

            active_declarations.extend(
                self._scan_file(
                    path,
                    historical=False,
                )
            )

        # ------------------------------------------------------
        # Pass 1B: historical/excluded repository knowledge
        #
        # This is intentionally separate. It NEVER contributes
        # edges to the active graph.
        # ------------------------------------------------------

        for path in historical_paths:

            historical_declarations.extend(
                self._scan_file(
                    path,
                    historical=True,
                )
            )

        # ------------------------------------------------------
        # Pass 2: relationships
        # ------------------------------------------------------

        active_inheritance_edges = (
            self._build_relationships(
                active_declarations,
                historical=False,
            )
        )

        historical_inheritance_edges = (
            self._build_relationships(
                historical_declarations,
                historical=True,
            )
        )

        self.stats = {
            # Backward-compatible keys.
            "files_scanned": len(active_paths),
            "types_discovered": len(self.types),
            "nodes": self.node_count(),
            "edges": self.edge_count(),
            "inheritance_edges":
                active_inheritance_edges,

            # Architecture Intelligence 2.0.
            "active_files": len(active_paths),
            "active_types": len(self.types),
            "active_nodes": len(self.nodes),
            "active_edges": len(self.edges),

            "historical_files":
                len(historical_paths),

            "historical_types":
                len(self.historical_types),

            "historical_nodes":
                len(self.historical_nodes),

            "historical_edges":
                len(self.historical_edges),

            "historical_inheritance_edges":
                historical_inheritance_edges,

            "project_includes":
                len(self.project_includes),

            "project_removes":
                len(self.project_removes),
        }

        return dict(self.stats)

    # ==========================================================
    # Active queries
    # ==========================================================

    def knows_type(self, full_name):

        return full_name in self.types

    def get_type(self, full_name):

        return self.types.get(full_name)

    def get_node(self, name):

        key = f"Type:{name}"
        return key if key in self.nodes else None

    def inheritance_children(self, full_name):

        key = self.get_node(full_name)

        if key is None:
            return []

        return sorted({
            self.nodes[child]["name"]
            for child in self.children_of(key)
            if child in self.nodes
        })

    def inheritance_parents(self, full_name):

        key = self.get_node(full_name)

        if key is None:
            return []

        return sorted({
            self.nodes[parent]["name"]
            for parent in self.parents_of(key)
            if parent in self.nodes
        })

    def active_inheritance_parents(
        self,
        full_name,
    ):

        return self.inheritance_parents(
            full_name
        )

    # ==========================================================
    # Historical queries
    # ==========================================================

    def knows_historical_type(
        self,
        full_name,
    ):

        return (
            full_name
            in self.historical_types
        )

    def get_historical_type(
        self,
        full_name,
    ):

        return self.historical_types.get(
            full_name
        )

    def _historical_node(
        self,
        name,
    ):

        key = f"Type:{name}"
        return key if key in self.historical_nodes else None

    def historical_inheritance_parents(
        self,
        full_name,
    ):

        key = self._historical_node(
            full_name
        )

        if key is None:
            return []

        parents = []

        for edge in self.historical_incoming.get(
            key,
            [],
        ):

            if edge["relation"] != "inherits":
                continue

            parent = edge["source"]

            if parent in self.historical_nodes:

                parents.append({
                    "name":
                        self.historical_nodes[
                            parent
                        ]["name"],

                    "source_file":
                        edge.get(
                            "source_file"
                        ),

                    "status":
                        "HISTORICAL",
                })

        return parents

    def historical_relationships_for(
        self,
        full_name,
    ):

        key = self._historical_node(
            full_name
        )

        if key is None:
            return []

        results = []

        for edge in self.historical_incoming.get(
            key,
            [],
        ):

            source = edge["source"]

            results.append({
                "direction": "incoming",
                "relation": edge["relation"],
                "other": (
                    self.historical_nodes[
                        source
                    ]["name"]
                    if source
                    in self.historical_nodes
                    else source
                ),
                "source_file":
                    edge.get("source_file"),
                "status": "HISTORICAL",
            })

        for edge in self.historical_outgoing.get(
            key,
            [],
        ):

            target = edge["target"]

            results.append({
                "direction": "outgoing",
                "relation": edge["relation"],
                "other": (
                    self.historical_nodes[
                        target
                    ]["name"]
                    if target
                    in self.historical_nodes
                    else target
                ),
                "source_file":
                    edge.get("source_file"),
                "status": "HISTORICAL",
            })

        return results

    # ==========================================================
    # General queries
    # ==========================================================

    def relationship(
        self,
        source_name,
        target_name,
    ):

        source = self.get_node(
            source_name
        )

        target = self.get_node(
            target_name
        )

        if (
            source is None
            or target is None
        ):
            return []

        return [
            edge
            for edge
            in self.outgoing.get(
                source,
                [],
            )
            if edge["target"] == target
        ]

    def summary(self):

        return {
            "status": self.health(),
            "version": self.VERSION,
            "project": (
                str(self.project_file)
                if self.project_file
                else None
            ),
            "stats": dict(self.stats),
        }


if __name__ == "__main__":

    intelligence = (
        ArchitectureIntelligence()
    )

    intelligence.startup()

    stats = intelligence.analyze(
        Path.cwd()
    )

    print("=" * 70)
    print("ARCHITECTURE INTELLIGENCE")
    print("=" * 70)

    for key, value in stats.items():
        print(f"{key:<30}: {value}")

    print("=" * 70)
