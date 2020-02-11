import json
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from semver import parse_version_info

from sebex.analysis.analyzer import AnalysisEntry
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
    version = parse_version_info(raw['version'])
    version_span = Span.from_raw(raw['version_span'])
    return AnalysisEntry(version=version, version_span=version_span)
