import json
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from sebex.analysis.analyzer import AnalysisEntry, Dependency, VersionInfo
from sebex.context import Context
from sebex.edit import Span

if TYPE_CHECKING:
    from sebex.config import ProjectHandle


def mix_file(project: 'ProjectHandle') -> Path:
    return project.location / 'mix.exs'


def analyze(project: 'ProjectHandle') -> AnalysisEntry:
    proc = subprocess.run([Context.current().elixir_analyzer, '--mix', mix_file(project)],
                          capture_output=True, check=True)
    raw = json.loads(proc.stdout)

    version = VersionInfo.parse(raw['version'])
    version_span = Span.from_raw(raw['version_span'])

    def load_dependency(dep):
        raw_version_lock = dep['version_lock']
        if raw_version_lock is not None:
            version_lock = VersionInfo.parse(raw_version_lock)
        else:
            version_lock = None

        return Dependency(
            name=dep['name'],
            version_spec=dep['version_spec'],
            version_spec_span=Span.from_raw(dep['version_spec_span']),
            version_lock=version_lock
        )

    dependencies = [load_dependency(dep) for dep in raw['dependencies']]

    return AnalysisEntry(version=version, version_span=version_span, dependencies=dependencies)
