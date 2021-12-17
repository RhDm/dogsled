import os
import platform
import pickle
import logging
from pathlib import Path
from distutils import dir_util

import numpy as np
import pytest

from dogsled.libvips_downloader import GetLibvips
from dogsled.errors import LibVipsError
from dogsled.defaults import StainTypes

#### pyvips import block ####
# ugly, but works for windows
if platform.system() == "Windows":
    """If pyvips could nor be imported & Windows is used
    => download libvips, register DLLs
    """
    vips_getter = GetLibvips()
    vips_home = vips_getter.get_path()
    os.environ["PATH"] = str(vips_home) + ";" + os.environ["PATH"]
    import pyvips
else:
    try:
        import pyvips
    except ModuleNotFoundError:
        raise LibVipsError(
            message="was not able to load libvips; please follow https://www.libvips.org/install.html")


from dogsled.normaliser import Normalisation, SlideTiler, NormaliseSlides
from dogsled.defaults import DEFAULTS

logger = logging.getLogger(__name__)

DATA_PATH = Path(Path(__file__).parent, "data")
NORM_PATH = Path(DATA_PATH, "normalised")
DEFAULTS.output_type = [StainTypes.he, StainTypes.eo, StainTypes.norm]

# try creating a testing data folder if it does not exist already
try:
    NORM_PATH.mkdir(parents=True, exist_ok=False)
except FileExistsError:
    pass


@pytest.fixture(scope="module", autouse=True)
def test_data(test_slides):
    """Move all test data.
    Data located at the folder with the same name
    as the test file to the data folder, re-defines DATA_PATH.
    """
    module_name = Path(__file__).stem
    test_data_path = Path(Path(__file__).parent / module_name)
    if test_data_path.exists():
        dir_util.copy_tree(str(test_data_path), str(DATA_PATH))
    yield


@pytest.fixture(scope="function")
def slice_sector_ref(test_data):
    cutout = np.load(Path(DATA_PATH, "slide_sector.npz"))
    yield cutout["sector"]


@pytest.fixture(scope="function")
def slice_od_ref(test_data):
    od = np.load(Path(DATA_PATH, "sector_od.npz"))
    yield od["sector_od"]


@pytest.fixture(scope="function")
def slice_he_ref(test_data):
    he = np.load(Path(DATA_PATH, "sector_he.npz"))
    yield he["sector_he"]


@pytest.fixture(scope="function")
def slice_s_cut_ref(test_data):
    s_cut = np.load(Path(DATA_PATH, "sector_s_cut.npz"))
    yield s_cut["sector_s_cut"]


@pytest.fixture(scope="function")
def slice_max_s_ref(test_data):
    max_s = np.load(Path(DATA_PATH, "sector_max_s.npz"))
    yield max_s["sector_max_s"]


@pytest.fixture(scope="function")
def slice_wrapper_ref(test_data):
    wrapped_arrays = np.load(Path(DATA_PATH, "sector_wrapped_arrays.npz"))
    data = [wrapped_arrays[key] for key in wrapped_arrays]
    yield data


@pytest.fixture(scope="function")
def slice_s_ref(test_data):
    s_final = np.load(Path(DATA_PATH, "sector_s_final.npz"))
    yield s_final["sector_s_final"]


@pytest.fixture(scope="function")
def slice_img_ref(test_data):
    img = np.load(Path(DATA_PATH, "sector_img.npz"))
    yield img["sector_img"]


def test_normalisation(slice_sector_ref, slice_od_ref, slice_he_ref,
                       slice_s_cut_ref, slice_max_s_ref, slice_wrapper_ref,
                       slice_s_ref, slice_img_ref):
    """Full normalisation workflow."""
    # call explicitly test_slides to download the data
    # slide_names = [slide.name for slide in test_slides]
    slide = pyvips.Image.new_from_file(
        str(Path(DATA_PATH, "CMU-1-Small-Region.svs")), access="sequential")
    cutout = Normalisation.read_sector(
        slide, location=(550, 550), size_wh=(1110, 1110))
    od = Normalisation.convert_od(cutout, DEFAULTS.normalising_c)
    he = Normalisation.calculate_hem(od, DEFAULTS.beta, DEFAULTS.alpha)
    y = np.reshape(od, (-1, 3)).T
    s_cut = np.empty(shape=[2, 0], dtype=DEFAULTS.dtype)
    s_cut = Normalisation.nb_lstsq(y, he, s_cut)
    max_s = Normalisation.calculate_sp(s_cut)
    wrapper_s_cut, wrapper_tmp, wrapper_he = Normalisation.region_s(
        cutout, DEFAULTS.normalising_c,
        DEFAULTS.alpha, DEFAULTS.beta,
        DEFAULTS.max_s_ref, DEFAULTS.he_ref)
    c2 = Normalisation.s_final(wrapper_s_cut, wrapper_tmp)
    img = Normalisation.image_restore(c2, DEFAULTS.normalising_c,
                                      DEFAULTS.he_ref, (1110, 1110),
                                      output_type="norm")
    res = img.shape[0]*img.shape[1]*3

    np.testing.assert_array_equal(slice_sector_ref, cutout)
    np.testing.assert_array_almost_equal(slice_od_ref, od, decimal=16)
    np.testing.assert_array_almost_equal(slice_he_ref, he, decimal=12)
    np.testing.assert_array_almost_equal(slice_s_cut_ref, s_cut, decimal=6)
    np.testing.assert_array_almost_equal(slice_max_s_ref, max_s, decimal=6)
    np.testing.assert_array_almost_equal(
        slice_wrapper_ref[0], wrapper_s_cut, decimal=5)
    np.testing.assert_array_almost_equal(
        slice_wrapper_ref[1], wrapper_tmp, decimal=6)
    np.testing.assert_array_almost_equal(
        slice_wrapper_ref[2], wrapper_he, decimal=6)
    np.testing.assert_allclose(slice_s_ref, c2, atol=2e-6)
    # allow for 1% of mismatched pixels
    assert (np.count_nonzero(slice_img_ref != img)/res)*100 < 1


############################################################################


@pytest.fixture(scope="module")
def small_test_data(test_data):
    # TODO this is quite ugly, should change..
    with open(Path(DATA_PATH, "small_test_data.pkl"), "rb") as pkl_file:
        data = pickle.load(pkl_file)
    yield data


@pytest.fixture(scope="module")
def slice_points(small_test_data):
    slice_points_, _, _ = small_test_data
    yield slice_points_


@pytest.fixture(scope="function")
def coordinates_dct(small_test_data):
    _, coordinates_dict, _ = small_test_data
    yield coordinates_dict


@pytest.fixture(scope="function")
def slices(small_test_data):
    _, _, slices_ = small_test_data
    yield slices_


def test_rows_columns():
    """If the maximum tile side size is 900 and the slide size is 2780
    => has to split in 4 rows/columns.
    """
    mn = SlideTiler.rows_columns(slide_width_px=2780,
                                 slide_height_px=2780,
                                 max_side_px=900)
    assert mn == (4, 4)


def test_slice_points(slice_points):
    """If the slide size is 3451x7463 px and mn = 4x3
    =>  ((0,0) (1150,1865)) etc.
    """
    result = SlideTiler.slice_points(slide_width_px=3451,
                                     slide_height_px=7463, mn=(4, 3))
    assert result == slice_points


def test_coordinates_dict(coordinates_dct, slice_points):
    result = SlideTiler.coordinates_dict(slice_points)
    assert result == coordinates_dct


def test_slicer(slices):
    result = SlideTiler.slicer(width_height_px=(3451, 7463),
                               max_side_px=1500)
    assert result == slices


def test_thumbnail_size():
    """If the slide size is 577392x464930 & max thumbnail size is 1200
    => 0.01039155374*577392 x 0.01039155374*464930
    => 6000x4831
    """
    rescaled1 = SlideTiler.thumbnail_size((577392, 464930))
    rescaled2 = SlideTiler.thumbnail_size((464930, 577392))
    assert rescaled1 == (6000, 4831)
    assert rescaled2 == (4831, 6000)


############################################################################
# testing full normalisation including interfaces


@pytest.fixture(scope="function")
def small_slide_ref():
    jpeg_norm = SlideTiler.vips_imread(
        str(Path(DATA_PATH, "norm_CMU-1-Small-Region.jpeg")))
    jpeg_he = SlideTiler.vips_imread(
        str(Path(DATA_PATH, "he_CMU-1-Small-Region.jpeg")))
    jpeg_eo = SlideTiler.vips_imread(
        str(Path(DATA_PATH, "eo_CMU-1-Small-Region.jpeg")))
    yield jpeg_norm, jpeg_he, jpeg_eo


def test_full_small_svs(small_slide_ref, test_slides):
    """Normalises small slides compares the result to the reference."""
    # enforce use of test_slides at this point
    i = [str(slide.name)
         for slide in test_slides].index("CMU-1-Small-Region.svs")
    normaliser = NormaliseSlides(source_path=DATA_PATH,
                                 slide_names=str(test_slides[i].name),
                                 norm_path=Path(DATA_PATH, "normalised"),
                                 rewrite=True)
    normaliser.start()
    ref_norm, ref_he, ref_eo = small_slide_ref
    # compare norm
    jpeg_norm = SlideTiler.vips_imread(
        str(Path(NORM_PATH, "norm_CMU-1-Small-Region.jpeg")))
    np.testing.assert_allclose(ref_norm, jpeg_norm, rtol=3)
    # compare he
    jpeg_he = SlideTiler.vips_imread(
        str(Path(NORM_PATH, "he_CMU-1-Small-Region.jpeg")))
    np.testing.assert_allclose(ref_he, jpeg_he, rtol=3)
    # compare eo
    jpeg_eo = SlideTiler.vips_imread(
        str(Path(NORM_PATH, "eo_CMU-1-Small-Region.jpeg")))
    res = jpeg_eo.shape[0]*jpeg_eo.shape[1]*3
    # allow for 1% of mismatched pixels
    assert (np.count_nonzero(ref_eo != jpeg_eo)/res)*100 < 1

# "biggish" slide


def test_full_big_svs():
    """Make dogsled treat small slide as a big slide."""
    DEFAULTS.ram_megapixel = {8000: 1500, 8001: 1500}
    # disable removing temporary files
    DEFAULTS.remove_temporary_files = False
    normaliser = NormaliseSlides(source_path=DATA_PATH,
                                 slide_names="CMU-1-Small-Region.svs",
                                 norm_path=Path(DATA_PATH, "normalised"),
                                 rewrite=True)
    normaliser.start()
    temp_folder = Path(
        NORM_PATH, DEFAULTS.temporary_folder_name, "CMU-1-Small-Region")
    # check if the temporary folder was not cleaned
    assert next((file for file in temp_folder.iterdir()
                if not str(file.name).startswith(".")), False)
    # check if the repeated stitching works
    normaliser.repeat_stitching()
    # clean temporary folder
    for stain_type in DEFAULTS.stain_types():
        normaliser.cleaner(stain_type, normaliser.current_slide)
    # check if the temporary folder was cleaned, excluding hidden files
    assert not next((file for file in temp_folder.iterdir()
                    if not str(file.name).startswith(".")), False)
    # restore the values for further tests
    DEFAULTS.ram_megapixel = {8000: 12000, 8001: 24500}


@pytest.fixture(scope="function")
def small_slide_ref_vips_tiff():
    tif_norm = SlideTiler.vips_imread(
        str(Path(DATA_PATH, "norm_CMU-1-Small-Region.tif")))
    tif_he = SlideTiler.vips_imread(
        str(Path(DATA_PATH, "he_CMU-1-Small-Region.tif")))
    tif_eo = SlideTiler.vips_imread(
        str(Path(DATA_PATH, "eo_CMU-1-Small-Region.tif")))
    yield tif_norm, tif_he, tif_eo


def test_vips_stitching(small_slide_ref_vips_tiff):
    """Make dogsled treat small slide as a big slide and use vips stitcher."""
    DEFAULTS.vips_stitcher = True
    DEFAULTS.ram_megapixel = {8000: 1500, 8001: 1500}
    normaliser = NormaliseSlides(source_path=DATA_PATH,
                                 slide_names="CMU-1-Small-Region.svs",
                                 norm_path=NORM_PATH,
                                 rewrite=True)
    normaliser.start()
    temp_folder = Path(
        NORM_PATH, DEFAULTS.temporary_folder_name, "CMU-1-Small-Region")
    # check if the temporary folder was not cleaned
    assert next((file for file in temp_folder.iterdir()
                if not str(file.name).startswith(".")), False)
    # check if the repeated stitching works
    normaliser.repeat_stitching()
    # clean temporary folder
    for stain_type in DEFAULTS.stain_types():
        normaliser.cleaner(stain_type, normaliser.current_slide)
    # check if the temporary folder was cleaned, excluding hidden files
    assert not next((file for file in temp_folder.iterdir()
                    if not str(file.name).startswith(".")), False)

    ref_norm, ref_he, ref_eo = small_slide_ref_vips_tiff
    # compare norm
    tif_norm = SlideTiler.vips_imread(
        str(Path(NORM_PATH, "norm_CMU-1-Small-Region.tif")))
    np.testing.assert_allclose(ref_norm, tif_norm, rtol=3)
    # compare he
    tif_he = SlideTiler.vips_imread(
        str(Path(NORM_PATH, "he_CMU-1-Small-Region.tif")))
    np.testing.assert_allclose(ref_he, tif_he, rtol=3)
    # compare eo
    tif_eo = SlideTiler.vips_imread(
        str(Path(NORM_PATH, "eo_CMU-1-Small-Region.tif")))
    res = ref_eo.shape[0]*ref_eo.shape[1]*3
    # allow for 1% of mismatched pixels
    assert (np.count_nonzero(ref_eo != tif_eo)/res)*100 < 1
    # restore default values for further tests
    DEFAULTS.ram_megapixel = {8000: 12000, 8001: 24500}
