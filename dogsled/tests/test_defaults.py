import pytest

import numpy as np
import numba

from dogsled.defaults import Defaults, StainTypes, DEFAULTS


@pytest.fixture(scope="function")
def defaults_source_partial():
    source_dict = {
        "show_results": True,
        "ram_megapixel": {1000: 1000,
                          1200100: 24500000},
        "output_type": [StainTypes.norm],
        "dtype": np.float64,
        "numba_dtype": numba.float32}
    yield source_dict


@pytest.fixture(scope="function")
def defaults_source_full():
    DEFAULTS = {
        "show_results": False,
        "ram_megapixel": {1000: 1000, 1200100: 24500000},
        "output_type": [StainTypes.norm],
        "dtype": np.float64,
        "numba_dtype": numba.float32,
        "normalising_c": 255,
        "alpha": 0.0001,
        "beta": 0.0015,
        "temporary_folder_name": "dogsled_temp",
        "remove_temporary_files": True,
        "jpeg_quality": 95,
        "vips_tiff_compression": "lzw",
        "thumbnail": True,
        "thumbnail_max_side": 6000,
        "vips_stitcher": False,
        "OpenSlide_formats": [".svs", ".tif", ".tiff", ".scn",
                              ".vms", ".vmu", ".ndpi", ".mrxs",
                              ".svslide", ".bif"],
        "first_tile": "middle",
        "libvips_url": "https://github.com/libvips/build-win64-mxe/releases/download/v8.12.0/vips-dev-w64-web-8.12.0-static.zip",
        "libvips_md5": "9a5dc27f6e9aae423ea620447dc67f1e",
        "he_ref": np.array([[0.68923328, 0.17593921],
                            [0.69707646, 0.82865536],
                            [0.67372909, 0.53139034]]).astype(np.float32),
        "max_s_ref": np.array([0.49806655, 0.92659484]).astype(np.float32)}
    yield DEFAULTS


@pytest.fixture(scope="function")
def defaults_source_full_wrong():
    DEFAULTS = {
        "show_resultS": False,
        "ram_megapixel": {1000: 1000, 1200100: 24500000},
        "output_type": [StainTypes.norm],
        "dtype": np.float64,
        "numba_dtype": numba.float32,
        "normalising_c": 255,
        "alpha": 0.0001,
        "beta": 0.0015,
        "temporary_folder_name": "dogsled_temp",
        "remove_temporary_files": True,
        "jpeg_quality": 95,
        "vips_tiff_compression": "lzw",
        "thumbnail": True,
        "thumbnail_max_side": 6000,
        "vips_stitcher": False,
        "OpenSlide_formats": [".svs", ".tif", ".tiff", ".scn",
                              ".vms", ".vmu", ".ndpi", ".mrxs",
                              ".svslide", ".bif"],
        "first_tile": "middle",
        "libvips_url": "https://github.com/libvips/build-win64-mxe/releases/download/v8.12.0/vips-dev-w64-web-8.12.0-static.zip",
        "libvips_md5": "9a5dc27f6e9aae423ea620447dc67f1e",
        "he_ref": np.array([[0.68923328, 0.17593921],
                            [0.69707646, 0.82865536],
                            [0.67372909, 0.53139034]]).astype(np.float32),
        "max_s_ref": np.array([0.49806655, 0.92659484]).astype(np.float32)}
    yield DEFAULTS


def test_stain_assignment_wrong():
    with pytest.raises(AttributeError):
        DEFAULTS.output_type = StainTypes.wrong


def test_stain_type_assignment():
    DEFAULTS.output_type = [StainTypes.norm, StainTypes.he, StainTypes.eo]
    assert DEFAULTS.stain_types() == ['norm', 'he', 'eo']


def test_default_assignment_wrong():
    with pytest.raises(AttributeError):
        DEFAULTS.wrong = False


def test_defaults_initialisation_broken(defaults_source_partial):
    with pytest.raises(KeyError):
        DEFAULTS = Defaults(defaults_source_partial)


def test_defaults_initialisation_full(defaults_source_full):
    DEFAULTS = Defaults(defaults_source_full)
    assert DEFAULTS.show_results == False
    assert DEFAULTS.ram_megapixel == {1000: 1000, 1200100: 24500000}
    assert DEFAULTS.output_type == [StainTypes.norm]
    assert DEFAULTS.dtype == np.float64


def test_defaults_initialisation_full_wrong(defaults_source_full_wrong):
    with pytest.raises(KeyError):
        DEFAULTS = Defaults(defaults_source_full_wrong)
