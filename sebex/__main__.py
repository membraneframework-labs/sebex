import os
from importlib import metadata

import click
from dotenv import load_dotenv, find_dotenv

from sebex.cmd.bootstrap import bootstrap
from sebex.cmd.foreach import foreach
from sebex.cmd.graph import graph
from sebex.cmd.ls import ls
from sebex.cmd.release import release
from sebex.cmd.sync import sync
from sebex.context import Context
from sebex.log import FatalError, warn


@click.group()
@click.version_option(metadata.version('sebex'))
@click.option('-y', '--assumeyes', is_flag=True, help='Automatically answer yes for all questions.')
@click.option('--workspace', type=click.Path(exists=True, file_okay=False, writable=True),
              default='.', required=True, show_default=True, show_envvar=True,
              help='Path to the workspace directory.')
@click.option('-p', '--profile', default='all', required=True, show_default=True, show_envvar=True,
              metavar='NAME', help='Name of the workspace profile to operate in.')
# Default value same as for ThreadPoolExecutor on Python 3.8
@click.option('-j', '--jobs', type=click.IntRange(min=1), default=max(32, os.cpu_count() + 4),
              required=True, show_default=True, show_envvar=True, metavar='COUNT',
              help='Set number of parallel running jobs.')
@click.option('--github_access_token', required=True, show_envvar=True, metavar='TOKEN',
              help='Github private access token.')
def cli(**kwargs):
    Context.initial(**kwargs)


cli.add_command(bootstrap)
cli.add_command(foreach)
cli.add_command(graph)
cli.add_command(ls)
cli.add_command(release)
cli.add_command(sync)


def main():
    try:
        try:
            load_dotenv(find_dotenv(usecwd=True))
        except Exception as e:
            warn('Failed to find and load .env:', e)

        cli(auto_envvar_prefix="SEBEX")
    except FatalError:
        pass


if __name__ == '__main__':
    main()
