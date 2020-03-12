import json
import subprocess
from pathlib import Path
from typing import List

from sebex.analysis.types import AnalysisEntry, Dependency, Release, Language, LanguageSupport, \
    DependencyUpdate
from sebex.analysis.version import VersionSpec, Version
from sebex.config import ProjectHandle, RepositoryHandle
from sebex.context import Context
from sebex.edit import Span


def mix_file(project: ProjectHandle) -> Path:
    return project.location / 'mix.exs'


class ElixirLanguageSupport(LanguageSupport):
    @classmethod
    def language(cls) -> Language:
        return Language.ELIXIR

    @classmethod
    def test_project(cls, project: ProjectHandle) -> bool:
        return mix_file(project).exists()

    def analyze(self, project: ProjectHandle) -> AnalysisEntry:
        proc = subprocess.run([Context.current().elixir_analyzer, '--mix', mix_file(project)],
                              capture_output=True, check=True)
        raw = json.loads(proc.stdout)

        package = raw['package']
        version = Version.parse(raw['version'])
        version_span = Span.from_raw(raw['version_span'])

        dependencies = [
            Dependency(
                name=(dep['name']),
                defined_in=package,
                version_spec=VersionSpec.parse(dep['version_spec']),
                version_spec_span=Span.from_raw(dep['version_spec_span']),
            )
            for dep in raw['dependencies']]

        hex_info = raw['hex']
        if hex_info['published']:
            def load_release(rel):
                return Release(
                    version=Version.parse(rel['version']),
                    retired=bool(rel.get('retired', False))
                )

            releases = list(map(load_release, hex_info['versions']))
        else:
            releases = []

        return AnalysisEntry(package=package, version=version, version_span=version_span,
                             dependencies=dependencies, releases=releases)

    def write_release(self, to_version: Version, to_version_span: Span,
                      dependencies: List[DependencyUpdate]):
        print(to_version, to_version_span)
        print(dependencies)

        raise NotImplementedError


def _is_tracked(file: Path, repo: RepositoryHandle):
    file = file.resolve()
    for line in repo.git.git.ls_files().split('\n'):
        path = Path(line).resolve()
        if file == path:
            return True
    return False
