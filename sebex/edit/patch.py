from collections import defaultdict
from io import StringIO
from pathlib import Path
from typing import Tuple, Iterable, TextIO, Iterator, Dict, Optional

from sebex.edit import Span

Patch = Tuple[Span, str]
Point = Tuple[int, int]


def patch_file(file: Path, patches: Iterable[Patch]):
    with open(file, 'r+', encoding='utf-8') as f:
        text = _run_patch(f, patches)
        f.seek(0)
        f.write(text)
        f.truncate()


def patch_str(text: str, patches: Iterable[Patch]) -> str:
    return _run_patch(StringIO(text), patches)


def _run_patch(text: TextIO, patches: Iterable[Patch]) -> str:
    patchmap = defaultdict(lambda: ((0, 0), ''))
    for span, replacement in patches:
        if span.end >= patchmap[span.start][0]:
            patchmap[span.start] = (span.end, replacement)

    return ''.join(_apply_patch(text, dict(patchmap)))


def _apply_patch(text: TextIO, patchmap: Dict[Point, Tuple[Point, str]]) -> Iterator[str]:
    skip: Optional[Point] = None
    for start, char in _enumerate_line_col(text):
        if skip is not None:
            if start >= skip:
                skip = None
                yield char
        elif start in patchmap:
            skip, replacement = patchmap[start]
            yield replacement

            if start >= skip:
                skip = None
                yield char
        else:
            yield char


def _enumerate_line_col(text: TextIO) -> Iterator[Tuple[Point, str]]:
    lineno, colno = 1, 1
    nl = False
    for lineno, line in enumerate(text, start=1):
        nl = False
        for colno, char in enumerate(line, start=1):
            nl = char == '\n'
            yield (lineno, colno), char

    # Emit pseudo-EOF character
    yield (lineno, colno), ''

    # If last line character was \n, then emit next line psuedo-EOF
    if nl:
        yield (lineno + 1, 1), ''
