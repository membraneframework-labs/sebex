import json
from pathlib import Path
from typing import List

from sebex.analysis.model import AnalysisEntry, Dependency, Release, Language, DependencyUpdate
from sebex.language.abc import LanguageSupport
from sebex.analysis.version import VersionSpec, Version
from sebex.config.manifest import ProjectHandle
from sebex.context import Context
from sebex.edit.patch import patch_file
from sebex.edit.span import Span
from sebex.log import operation
from sebex.popen import popen
from sebex.release.git import commit


def mix_file(project: ProjectHandle) -> Path:
    return project.location / 'mix.exs'


def mix_lock(project: ProjectHandle) -> Path:
    return project.location / 'mix.lock'


class ElixirLanguageSupport(LanguageSupport):
    @classmethod
    def language(cls) -> Language:
        return Language.ELIXIR

    @classmethod
    def test_project(cls, project: ProjectHandle) -> bool:
        return mix_file(project).exists()

    def analyze(self, project: ProjectHandle) -> AnalysisEntry:
        proc = popen(Context.current().elixir_analyzer, ['--mix', mix_file(project)])
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

    def write_release(self, project: ProjectHandle, to_version: Version, to_version_span: Span,
                      dependencies: List[DependencyUpdate]):
        with operation('Update mix.exs'):
            patch_file(mix_file(project), [
                (to_version_span, f'"{to_version}"'),
                *[(dep.to_spec_span, self._translate_version_spec(dep.to_spec))
                  for dep in dependencies]
            ])

            commit(project.repo, f'bump to {to_version}', [mix_file(project)])

        if project.repo.is_tracked(mix_lock(project)):
            with operation('Update lockfile'):
                popen('mix', ['deps.update', '--all'], log_stdout=True, cwd=project.location)
                if project.repo.is_changed(mix_lock(project)):
                    commit(project.repo, 'update lockfile', [mix_lock(project)])

    @classmethod
    def _translate_version_spec(cls, spec: VersionSpec) -> str:
        if spec.is_version:
            return f'"{spec.value}"'
        else:
            raise NotImplementedError
