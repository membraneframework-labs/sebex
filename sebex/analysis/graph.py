from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from graphviz import Digraph

from sebex.analysis.model import Dependency
from sebex.analysis.database import AnalysisDatabase
from sebex.config.manifest import ProjectHandle
from sebex.log import operation

_Edges = Dict[str, Dependency]
_Graph = Dict[str, _Edges]


@dataclass(frozen=True)
class DependentsGraph:
    _graph: _Graph

    def __len__(self):
        return len(self._graph)

    def dependents_of(self, package: str) -> Dict[str, Set[Dependency]]:
        result = defaultdict(set)

        for dep in self._graph[package].values():
            result[dep.defined_in].add(dep)

        return dict(result)

    def upgrade_phases(self, package: str) -> List[Set[str]]:
        """
        Collect all dependents of `package`, sorted topologically,
        with dependencies which are independent of each other grouped together into `phases`.
        """

        depths = defaultdict(lambda: 0)

        def visit(pkg: str, depth: int):
            depths[pkg] = max(depths[pkg], depth)

            for dep in self._graph[pkg].keys():
                visit(dep, depth + 1)

        visit(package, 0)

        inversion = defaultdict(set)
        for pkg, depth in sorted(depths.items(), key=lambda t: t[1]):
            inversion[depth].add(pkg)

        return list(inversion.values())

    def graphviz(self, db: AnalysisDatabase) -> Digraph:
        dot = Digraph()

        for package in self._graph.keys():
            project = db.get_project_by_package(package)
            about = db.about(project)
            dot.node(package, label=f'{project} ({about.version})')

        for package, dependencies in self._graph.items():
            for dependency, meta in dependencies.items():
                dot.edge(package, dependency, label=meta.version_str())

        return dot

    @classmethod
    def build(cls, db: AnalysisDatabase) -> 'DependentsGraph':
        with operation('Building dependency graph'):
            return cls(cls._invert(cls._guard_cycle(cls._build_graph(db))))

    @classmethod
    def _build_graph(cls, db):
        return {
            db.about(project).package: cls._collect_edges(project, db)
            for project in db.projects()
        }

    @classmethod
    def _collect_edges(cls, project: ProjectHandle, db: AnalysisDatabase) -> _Edges:
        return {
            dep.name: dep
            for dep in db.about(project).dependencies
            if db.is_package_managed(dep.name)
        }

    @classmethod
    def _invert(cls, graph: _Graph) -> _Graph:
        inversion = {pkg: {} for pkg in graph.keys()}

        for edges in graph.values():
            for dep in edges.values():
                inversion[dep.name][dep.defined_in] = dep

        return inversion

    @classmethod
    def _guard_cycle(cls, graph: _Graph) -> _Graph:
        cycle = cls._detect_cycle(graph)
        if cycle is None:
            return graph
        else:
            raise ValueError(f'Cycle in dependency graph detected: {"->".join(cycle)}')

    @classmethod
    def _detect_cycle(cls, graph: _Graph) -> Optional[List[str]]:
        def visit(pkg: str, stack: List[str]) -> Optional[List[str]]:
            for dep in graph[pkg].keys():
                new_stack = [*stack, dep]
                if dep in stack:
                    return new_stack
                else:
                    res = visit(dep, new_stack)
                    if res is not None:
                        return res

            return None

        for package in graph.keys():
            result = visit(package, [package])
            if result is not None:
                return result

        return None
