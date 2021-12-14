'''
default constants are stored here

vips tiff compression options:
https://libvips.github.io/pyvips/enums.html#pyvips.enums.ForeignTiffCompression
 none, jpeg, deflate, packbits, ccittfax4, lzw, webp, zstd, jp2k
'''
import numpy as np
import numba

# TODO implement enum for some parameters
# TODO refine ram to megapixel mapping
DEFAULTS = {
    'show_results': False,
    'ram_megapixel': {12000: 12000,
                      12001: 24500},  # {MB: pixel} under 8000MB: 12000px; over: 24500px
    # normalisation parameters:
    # 'output_type' : ['norm', 'he', 'eo'],
    'output_type': ['norm'],
    'dtype': np.float32,
    'numba_dtype': numba.float32,
    'normalising_c': 255,  # normalising constant
    # (alpha_th - (100 - alpha_th)) percentiles for stain vectors
    'alpha': 0.0001,
    'beta': 0.0015,  # threshold value for for pixels with low OD values
    'temporary_folder_name': 'dogsled_temp',
    'remove_temporary_files': True,
    'jpeg_quality': 95,
    'vips_tiff_compression': 'lzw',
    'thumbnail': True,
    'thumbnail_max_side': 6000,
    'vips_sticher': False,
    'OpenSlide_formats': ['.svs', '.tif', '.tiff', '.scn',
                          '.vms', '.vmu', '.ndpi', '.mrxs',
                          '.svslide', '.bif'],
    'first_tile': 'middle',
    'libvips_url': 'https://github.com/libvips/build-win64-mxe/releases/download/v8.12.1/vips-dev-w64-all-8.12.1.zip',
    'libvips_md5': '372821f34518e57dc4d311f28269e292'
}

# pseudo-maximum scaled?
DEFAULTS['he_ref'] = np.array([[0.68923328, 0.17593921],
                              [0.69707646, 0.82865536],
                               [0.67372909, 0.53139034]]).astype(DEFAULTS['dtype'])
# DEFAULTS['he_ref'] = np.array([[0.74749443,  0.00552991],
#                                [0.66302766,  0.16416982],
#                                [-0.04057596,  0.98641659]]).astype(DEFAULTS['dtype'])
DEFAULTS['max_s_ref'] = np.array(
    [0.49806655, 0.92659484]).astype(DEFAULTS['dtype'])


DEFAULTS_TESTS = {
    'test_data_url': 'https://openslide.cs.cmu.edu/download/openslide-testdata/Aperio/',
    'test_slide_names': ['CMU-1-Small-Region.svs', 'JP2K-33003-1.svs'],
    'md5': ['1ad6e35c9d17e4d85fb7e3143b328efe', 'a38c8a8f747e3858c615614e4e0f6d30']
}
