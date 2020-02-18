import click

from sebex.analysis import Version
from sebex.config import ProjectHandle, Manifest


class ProjectType(click.ParamType):
    name = "project"

    def convert(self, value, param, ctx):
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


PROJECT = ProjectType()


class VersionType(click.ParamType):
    name = "version"

    def convert(self, value, param, ctx):
        try:
            return Version.parse(value)
        except ValueError:
            self.fail(f'{value!r} is not a valid version')

VERSION = VersionType()
