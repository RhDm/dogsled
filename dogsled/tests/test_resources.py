import logging

import pytest
import psutil

from dogsled.resources import ResourceEstimator, ResourceChecker
from dogsled.defaults import DEFAULTS

LOGGER = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def space_required(test_slides):
    jpeg_sizes = [int(-2.28 + 1.51 * x.stat().st_size) for x in test_slides]
    slide_sizes = [x.stat().st_size for x in test_slides]
    yield sum(jpeg_sizes) + max(slide_sizes)


def test_space_estimator(test_slides, space_required):
    """Uses -2.28 + 1.51 * svs_size."""
    required = ResourceEstimator(test_slides).space_required
    assert space_required == required


def test_tile_size():
    ram_available = psutil.virtual_memory().available >> 20
    if ram_available <= min(DEFAULTS.ram_megapixel.keys()):
        side = DEFAULTS.ram_megapixel[min(DEFAULTS.ram_megapixel.keys())]
    else:
        side = DEFAULTS.ram_megapixel[max(DEFAULTS.ram_megapixel.keys())]
    assert side == ResourceChecker().tile_size


def test_space(test_slides, norm_path, space_required):
    _, required, all_svs = ResourceChecker.space(test_slides, norm_path)
    assert space_required >> 20 == required
    assert all_svs == True
