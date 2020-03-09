from contextlib import contextmanager
from typing import NoReturn

import click


def log(*msg, color=None):
    message = ' '.join(str(m) for m in msg)
    if color is not None:
        message = click.style(message, fg=color)
    click.echo(message)


def success(*msg):
    log(*msg, color='green')


def warn(*msg):
    log(*msg, color='yellow')


def error(*msg):
    log(*msg, color='red')


class FatalError(Exception):
    pass


def fatal(*msg) -> NoReturn:
    error('FATAL:', *msg)
    raise FatalError()


@contextmanager
def operation(*msg):
    log(*msg, '...')
    try:
        yield None
        log(*msg, click.style('OK', fg='green'))
    except:
        log(*msg, click.style('ERROR', fg='red'))
        raise
