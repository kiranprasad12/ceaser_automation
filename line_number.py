"""Line number matching helper (DUMMY example code for the test branch).

Matches a line number from a drawing against a line list, ignoring spaces,
quote marks and the size prefix.
"""

import re

_SIZE_PREFIX = re.compile(r"^\d+(?:\.\d+)?-")


def normalize_line_number(text):
    """Return a key for matching, e.g. 12"-ST-30108-B24S-HI -> ST-30108-B24S-HI."""
    cleaned = re.sub(r"[\s\"'“”″]", "", text).upper()
    return _SIZE_PREFIX.sub("", cleaned, count=1)


def same_line(a, b):
    """True if two line numbers are the same after normalizing."""
    return normalize_line_number(a) == normalize_line_number(b)
