"""
Test slide "getter" and QuPath project initialiser live here.
"""
import shutil
import hashlib
import logging
import tempfile
import urllib.request
from pathlib import Path
import pytest

from paquo.projects import QuPathProject

from dogsled.defaults import DEFAULTS_TESTS

LOGGER = logging.getLogger(__name__)
DATA_PATH = Path(Path(__file__).parent, "data")


def md5_gen(file):
    """Calculate md5 of a file."""
    md5_h = hashlib.md5()
    with open(file, "rb") as f:
        while True:
            chunk = f.read(1000 * 1000)
            if not chunk:
                break
            md5_h.update(chunk)
    return md5_h.hexdigest()


@pytest.fixture(scope="session", autouse=True)
def test_slides():
    """Download slides defined in DEFAULTS (if not previously downloaded).
    Checks md5, if all fine- returns slide list
    in DEFAULTS:    url with slides
                    slide names
                    md5 of the slides
    """
    slides = []
    DATA_PATH.mkdir(exist_ok=True)
    for i, test_slide in enumerate(DEFAULTS_TESTS["test_slide_names"]):
        slide_file = Path(DATA_PATH, test_slide)
        if not slide_file.is_file():
            LOGGER.info(f"downloading {test_slide}")
            url = DEFAULTS_TESTS["test_data_url"] + test_slide
            with urllib.request.urlopen(url) as response, open(slide_file, "wb") as out_file:
                shutil.copyfileobj(response, out_file)
        if md5_gen(slide_file) != DEFAULTS_TESTS["md5"][i]:
            LOGGER.error("slide md5 does not match md5 of the downloaded file")
            LOGGER.error("exiting")
            slide_file.unlink()
            pytest.fail("md5 mismatch")
        else:
            slides.append(slide_file)
    yield slides


@pytest.fixture(scope="session")
def test_slides_names(test_slides):
    yield [str(slide.name) for slide in test_slides]


@pytest.fixture(scope="session")
def test_slides_i(test_slides):
    yield list(range(len(test_slides)))


@pytest.fixture(scope="session")
def qupath_project(test_slides):
    """Initialise new qpproj using paquo."""
    with tempfile.TemporaryDirectory(prefix="qpproj_", dir=DATA_PATH) as qpproj_dir:
        qupath_proj = QuPathProject(qpproj_dir, mode="x")
        for slide in test_slides:
            qupath_proj.add_image(slide)
        yield qupath_proj


@pytest.fixture(scope="session")
def norm_path():
    norm_path_ = Path(DATA_PATH, "normalised")
    if not norm_path_.exists():
        norm_path_.mkdir(exist_ok=True)
    yield norm_path_
