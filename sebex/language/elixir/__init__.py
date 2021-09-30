import json
import os
from importlib import resources
from pathlib import Path
from typing import List

from sebex.analysis.model import AnalysisEntry, Dependency, Release, Language, DependencyUpdate
from sebex.analysis.version import VersionSpec, Version
from sebex.cli import confirm
from sebex.config.manifest import ProjectHandle
from sebex.edit.patch import patch_file
from sebex.edit.span import Span
from sebex.language.abc import LanguageSupport
from sebex.log import operation, warn, fatal
from sebex.popen import popen


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
        import re
        with resources.path(__name__, 'elixir_analyzer') as elixir_analyzer:
            proc = popen([elixir_analyzer, '--mix', mix_file(project)])
            analyzer_report = re.findall("<SEBEX_ELIXIR_ANALYZER_REPORT>(.*?)</SEBEX_ELIXIR_ANALYZER_REPORT>", proc.stdout, re.DOTALL)
            analyzer_report = analyzer_report[0]
            raw = json.loads(analyzer_report)

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

            project.repo.vcs.commit(f'bump to {to_version}', [mix_file(project)])

        if project.repo.vcs.is_tracked(mix_lock(project)):
            with operation('Update lockfile'):
                if popen(['mix', 'deps.update', '--all'], log_stdout=True, check=False, cwd=project.location).returncode == 0 \
                    or confirm('There was an error updating dependencies, that will have to be resolved manually. Continue anyway?'):
                    if project.repo.vcs.is_changed(mix_lock(project)):
                        project.repo.vcs.commit('update lockfile', [mix_lock(project)])
                else:
                    fatal('Error updating lockfile')

    def publish(self, project: ProjectHandle) -> bool:
        if not os.getenv('HEX_API_KEY'):
            warn('The HEX_API_KEY environment variable seems not to be set.',
                 'Mix will probably be unable to authenticate and will fail.',
                 'To generate API key, run this command: mix hex.user key generate')

        with operation('Dry run'):
            popen(['mix', 'deps.get'], log_stdout=True, cwd=project.location)
            popen(['mix', 'hex.publish', '--yes', '--dry-run'], log_stdout=True,
                  cwd=project.location)

        if not confirm('Please review dry run logs, proceed'):
            return False

        with operation('Publishing for real'):
            if 'sebex_test' in str(project):
                proc = popen(['mix', 'hex.publish', '--yes', '--replace'], log_stdout=True, cwd=project.location)
            else:
                proc = popen(['mix', 'hex.publish', '--yes'], log_stdout=True, cwd=project.location)

            # https://github.com/hexpm/hex/blob/3362c4abea51525d6c435ebb30bacfa603e0213a/lib/mix/tasks/hex.publish.ex#L536
            if 'Package published to ' in proc.stdout:
                return True
            else:
                fatal('Failed to publish Hex package')

    @classmethod
    def _translate_version_spec(cls, spec: VersionSpec) -> str:
        if spec.is_version:
            return f'"{spec.value}"'
        else:
            raise NotImplementedError
