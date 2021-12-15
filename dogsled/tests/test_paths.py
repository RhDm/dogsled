import logging
from pathlib import Path

import pytest

from dogsled.paths import PathChecker, PathCreator
from dogsled.errors import UserInputError

LOGGER = logging.getLogger(__name__)


def test_str_to_path(norm_path):
    assert isinstance(PathChecker().str_to_path(norm_path), Path)
    assert isinstance(PathChecker().str_to_path(str(norm_path)), Path)


def test_wrong_path():
    with pytest.raises(UserInputError):
        PathChecker().str_to_path("some/non-existent/path")


def test_creating_existing_path(norm_path):
    with pytest.raises(UserInputError):
        PathCreator.create_path(norm_path)
