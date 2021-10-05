import click

from sebex.analysis.version import Version
from sebex.config.manifest import ProjectHandle, Manifest
from sebex.context import Context
from typing import Tuple


class SourceType(click.ParamType):
    name = "source"

    def convert(self, value, param, ctx) -> Tuple[Version, ProjectHandle]:
        project_str, version_str = self._parse_source(value, param, ctx)
        project = self._validate_project(project_str, param, ctx)
        version = self._validate_version(version_str, param, ctx)
        return project, version

    def _parse_source(self, value, param, ctx):
        try:
            project_str, version_str = value.split(':')
            return project_str, version_str
        except ValueError:
            self.fail(f'{value}\nthe source format should be `<project>:<version>` i.e. `membrane_framework:0.8.0`', param, ctx)

    def _validate_project(self, value, param, ctx) -> ProjectHandle:
        try:
            handle = ProjectHandle.parse(value)
        except ValueError:
            self.fail(f'{value!r} is not a valid project name', param, ctx)

        manifest = Manifest.open()

        for repo_manifest in manifest.iter_repositories():
            for project in repo_manifest.project_handles():
                if project == handle:
                    return project

        self.fail(f'Unknown project {handle}')

    def _validate_version(self, value, param, ctx) -> Version:
        try:
            return Version.parse(value)
        except ValueError:
            self.fail(f'{value!r} is not a valid version', param, ctx)

SOURCE = SourceType()


def confirm(text: str) -> bool:
    ctx = Context.current()
    if ctx.assume_yes:
        return True
    else:
        return click.confirm(text)
