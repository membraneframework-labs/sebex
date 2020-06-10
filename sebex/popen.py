import subprocess
from os import PathLike
from typing import List, Union

from sebex.log import logcontext, log, warn, error


def popen(args: Union[str, PathLike, List[str]], log_stdout: bool = False,
          **kwargs) -> subprocess.CompletedProcess:
    if isinstance(args, str):
        lc = args
    else:
        lc = args[0]

    lc = str(lc)[:12]

    with logcontext(lc):
        try:
            proc = subprocess.run(args, stdin=subprocess.DEVNULL, capture_output=True,
                                  check=True, encoding='utf-8', **kwargs)
            if log_stdout:
                for line in proc.stdout.splitlines():
                    log(line)
            return proc
        except subprocess.CalledProcessError as e:
            if e.stdout:
                for line in e.stdout.splitlines():
                    warn(line)

            if e.stderr:
                for line in e.stderr.splitlines():
                    error(line)

            raise
