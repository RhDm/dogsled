"""Default constants are stored here.
vips tiff compression options:
https://libvips.github.io/pyvips/enums.html#pyvips.enums.ForeignTiffCompression
 none, jpeg, deflate, packbits, ccittfax4, lzw, webp, zstd, jp2k
"""
import numpy as np
import numba
from dataclasses import dataclass
from enum import Enum
from typing import List


class StainTypes(Enum):
    """All possible values for stain output types"""
    norm = 'norm'
    he = 'he'
    eo = 'eo'


# TODO implement enum for some parameters
# TODO refine ram to megapixel mapping
DEFAULTS_VALS = {
    "show_results": False,
    "ram_megapixel": {12000: 12000,
                      12001: 24500},  # {MB: pixel} under 8000MB: 12000px; over: 24500px
    # normalisation parameters:
    # "output_type": [StainTypes.norm, StainTypes.he, StainTypes.eo],
    "output_type": [StainTypes.norm],
    "dtype": np.float32,
    "numba_dtype": numba.float32,
    "normalising_c": 255,  # normalising constant
    # (alpha_th - (100 - alpha_th)) percentiles for stain vectors
    "alpha": 0.0001,
    "beta": 0.0015,  # threshold value for for pixels with low OD values
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
    "libvips_md5": "9a5dc27f6e9aae423ea620447dc67f1e"
}

# pseudo-maximum scaled?
DEFAULTS_VALS["he_ref"] = np.array([[0.68923328, 0.17593921],
                                    [0.69707646, 0.82865536],
                                    [0.67372909, 0.53139034]]).astype(DEFAULTS_VALS["dtype"])
# DEFAULTS["he_ref"] = np.array([[0.74749443,  0.00552991],
#                                [0.66302766,  0.16416982],
#                                [-0.04057596,  0.98641659]]).astype(DEFAULTS["dtype"])
DEFAULTS_VALS["max_s_ref"] = np.array(
    [0.49806655, 0.92659484]).astype(DEFAULTS_VALS["dtype"])

# used only for testing & not exposed to the user => can stay as a dictionary
DEFAULTS_TESTS = {
    "test_data_url": "https://openslide.cs.cmu.edu/download/openslide-testdata/Aperio/",
    "test_slide_names": ["CMU-1-Small-Region.svs", "JP2K-33003-1.svs"],
    "md5": ["1ad6e35c9d17e4d85fb7e3143b328efe", "a38c8a8f747e3858c615614e4e0f6d30"]
}


@dataclass
class Defaults:
    """Class for holding explicit attributes
    will not allow the user set an incorrect attribute e.g. misspell
    """
    __slots__ = ['show_results', 'ram_megapixel', 'output_type', 'dtype', 'numba_dtype', 'normalising_c', 'alpha', 'beta', 'temporary_folder_name', 'remove_temporary_files',
                 'jpeg_quality', 'vips_tiff_compression', 'thumbnail', 'thumbnail_max_side', 'vips_stitcher', 'OpenSlide_formats', 'first_tile', 'libvips_url', 'libvips_md5', 'he_ref', 'max_s_ref']

    def __init__(self, defaults_dict) -> None:
        """Take dictionary as an input, assign atributes & their values"""
        for variable in self.__slots__:
            setattr(self, variable, defaults_dict[variable])

    def stain_types(self) -> List[str]:
        """Return defined explicit stain types as a list of strings"""
        return [stain_type.name for stain_type in self.output_type]


DEFAULTS = Defaults(DEFAULTS_VALS)
