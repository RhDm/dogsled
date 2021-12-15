from pathlib import Path
import pytest
import logging

from dogsled.slides import QuPathSlides
from dogsled.errors import UserInputError

LOGGER = logging.getLogger(__name__)


def test_with_qpproj_path(qupath_project):
    qp_proj = QuPathSlides(qpproj_path=Path(qupath_project.path))
    assert qp_proj.qpproj_path == qupath_project.path
    assert isinstance(qp_proj.pq, type(qupath_project))


def test_with_qpproj_str(qupath_project):
    qp_proj = QuPathSlides(qpproj_path=qupath_project.path)
    assert qp_proj.qpproj_path == qupath_project.path
    assert isinstance(qp_proj.pq, type(qupath_project))


def test_with_wrong_path():
    with pytest.raises(UserInputError):
        _ = QuPathSlides(qpproj_path=Path("random/path"))
    with pytest.raises(UserInputError):
        _ = QuPathSlides(qpproj_path="random/path")
