import json
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from sebex.analysis.analyzer import AnalysisEntry, Dependency
from sebex.analysis.version import VersionSpec, Version
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

        return name, Dependency(
            name=name,
            version_spec=VersionSpec.parse(dep['version_spec']),
            version_spec_span=Span.from_raw(dep['version_spec_span']),
            version_lock=version_lock
        )

    dependencies = dict(map(load_dependency, raw['dependencies']))

    return AnalysisEntry(package=package, version=version, version_span=version_span,
                         dependencies=dependencies)
