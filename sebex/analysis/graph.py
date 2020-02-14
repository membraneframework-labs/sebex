from dataclasses import dataclass
from typing import Dict, List, Optional

from graphviz import Digraph

from sebex.analysis.analyzer import Dependency
from sebex.analysis.database import AnalysisDatabase
from sebex.config import ProjectHandle
from sebex.log import operation

_Edges = Dict[str, Dependency]
_Graph = Dict[str, _Edges]


@dataclass
class DependencyGraph:
    _graph: _Graph

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
    def build(cls, db: AnalysisDatabase) -> 'DependencyGraph':
        with operation('Building dependency graph'):
            return cls(cls._guard_cycle({
                db.about(project).package: cls._collect_edges(project, db)
                for project in db.projects()
            }))

    @classmethod
    def _collect_edges(cls, project: ProjectHandle, db: AnalysisDatabase) -> _Edges:
        return {
            dep.name: dep
            for dep in db.about(project).dependencies
            if db.is_package_managed(dep.name)
        }

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
