import pytest

from artifact_tests import marker_for


def pytest_collection_modifyitems(items):
    for item in items:
        marker = marker_for(item.nodeid)
        if marker is not None:
            item.add_marker(getattr(pytest.mark, marker))
