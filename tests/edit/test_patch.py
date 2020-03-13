import pytest

from sebex.edit import patch_str, Span


@pytest.mark.parametrize('original, patches, expected', [
    ('', [], ''),
    ('', [(Span(1, 1, 1, 1), 'XYZ')], 'XYZ'),
    ('ab\n', [(Span(1, 1, 1, 2), 'XYZ')], 'XYZb\n'),
    ('ab\n', [(Span(1, 1, 1, 3), 'XYZ')], 'XYZ\n'),
    ('ab\n', [(Span(1, 1, 1, 1), 'XYZ')], 'XYZab\n'),
    ('ab', [(Span(2, 1, 1, 1), 'XYZ')], 'ab'),
    ('ab\n', [(Span(2, 1, 1, 1), 'XYZ')], 'ab\nXYZ'),
    ('ab\ncd\ned', [], 'ab\ncd\ned'),
    ('ab\ncd\ned', [(Span(2, 1, 2, 3), 'XY')], 'ab\nXY\ned'),
    ('ab\ncd\ned', [(Span(1, 1, 2, 3), 'XY\nOP')], 'XY\nOP\ned'),
    ('ab\ncd\ned', [(Span(2, 1, 3, 3), 'XY\nOP')], 'ab\nXY\nOP'),
])
def test_patch_str(original, patches, expected):
    assert patch_str(original, patches) == expected
