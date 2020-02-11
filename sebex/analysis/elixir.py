import re
from pathlib import Path
from typing import TYPE_CHECKING

from semver import VersionInfo, parse_version_info

from sebex.analysis.analyzer import Analyzer, AnalysisError

if TYPE_CHECKING:
    from sebex.config import ProjectHandle


def mix_file(project: 'ProjectHandle') -> Path:
    return project.location / 'mix.exs'


version_attr_re = re.compile(r'^\s*@version\s+"(?P<version>[^"]+)"')


class ElixirAnalyzer(Analyzer):
    def package_version(self, project: 'ProjectHandle') -> VersionInfo:
        with open(mix_file(project), 'r', encoding='utf-8') as f:
            for line in f:
                match = version_attr_re.match(line)
                if match:
                    return parse_version_info(match['version'])

        raise AnalysisError('Could not find @version attribute.')
