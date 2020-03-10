from contextlib import contextmanager
from contextvars import ContextVar
from itertools import chain
from typing import NoReturn, Optional, List

import click

_logcontext_var = ContextVar('sebex_logcontext')


def log(*msg, color=None):
    message = ' '.join(chain(
        (click.style(f'[{c}]', fg='bright_black') for c in _logcontext_var.get([])),
        (str(m) for m in msg)
    ))
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
    ok_message: str = click.style('OK', fg='green')

    def reporter(message: Optional[str]):
        nonlocal ok_message
        if message:
            ok_message = message

    log(*msg, '...')
    try:
        yield reporter
        log(*msg, ok_message)
    except:
        log(*msg, click.style('ERROR', fg='red'))
        raise


@contextmanager
def logcontext(ctx: str):
    lst: List[str] = _logcontext_var.get([])
    token = _logcontext_var.set([*lst, ctx])
    try:
        yield None
    finally:
        _logcontext_var.reset(token)
