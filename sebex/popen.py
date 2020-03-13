import subprocess
from typing import List

from sebex.log import logcontext, log, warn, error


def popen(prog: str, args: List[str], log_stdout: bool = False,
          **kwargs) -> subprocess.CompletedProcess:
    with logcontext(prog):
        try:
            proc = subprocess.run([prog, *args], capture_output=True, check=True, encoding='utf-8',
                                  **kwargs)
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
