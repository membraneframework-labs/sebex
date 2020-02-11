from concurrent.futures import ThreadPoolExecutor
from typing import TypeVar, Iterable, Callable, List, Union

from sebex.context import Context
from sebex.log import error

T = TypeVar('T')
R = TypeVar('R')


class JobError(Exception):
    pass


def for_each(iterable: Iterable[T], f: Callable[[T], R],
             desc: str, item_desc: Callable[[T], Union[str, None]] = str) -> List[R]:
    context = Context.current()

    whole_iterable = list(iterable)

    def run(item: T) -> R:
        this_item_desc = item_desc(item)

        if this_item_desc is not None:
            job_desc = f'{desc}: {this_item_desc}'
        else:
            job_desc = desc

        try:
            with Context.activate(context):
                return f(item)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            error(f'Job "{job_desc}" failed!')
            raise JobError(job_desc) from e

    with ThreadPoolExecutor(max_workers=context.jobs) as executor:
        return list(executor.map(run, whole_iterable))
