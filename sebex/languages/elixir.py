import json
import subprocess
from pathlib import Path

from sebex.analysis.types import AnalysisEntry, Dependency, Release, Language, LanguageSupport
from sebex.analysis.version import VersionSpec, Version
from sebex.config import ProjectHandle
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

        def load_dependency(dep):
            name = dep['name']

            raw_version_lock = dep['version_lock']
            if raw_version_lock is not None:
                version_lock = Version.parse(raw_version_lock)
            else:
                version_lock = None

            return Dependency(
                name=name,
                defined_in=package,
                version_spec=VersionSpec.parse(dep['version_spec']),
                version_spec_span=Span.from_raw(dep['version_spec_span']),
                version_lock=version_lock
            )

        dependencies = list(map(load_dependency, raw['dependencies']))

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
