'''
Normaliser
'''

import gc
import sys
import logging
from time import time
from collections import OrderedDict
from pathlib import Path
from typing import Optional, Union, Any, Tuple, List, OrderedDict

import numpy as np
import numpy.typing as npt
from PIL import Image
from openslide import OpenSlide

from dogsled.user_input import FileData
from dogsled.defaults import DEFAULTS
from dogsled.errors import CleaningError, UserInputError
from dogsled.paths import PathCreator
from dogsled.slides import CurrentSlide
from dogsled.resources import ResourceChecker

Image.MAX_IMAGE_PIXELS = DEFAULTS['PIL_MAX_IMAGE_PIXELS']

LOGGER = logging.getLogger(__name__)
# not setting the leven in config.py to filter vips etc messages
LOGGER.setLevel(logging.DEBUG)

try:
    import pyvips
except ModuleNotFoundError:  # pragma: no cover
    LOGGER.info('pyvips not imported')


try:
    from IPython.core.display import clear_output
except ModuleNotFoundError:  # pragma: no cover
    def clear_output(wait=True):
        '''deactivate Jupyter's clear_output if it is not used'''
        pass


if 'line_profiler' not in dir() or 'memory_profiler' not in dir():
    def profile(func):
        '''line_profiler/memory_profiler decorator deactivation'''
        return func


# yet to be done
# TODO profile
# TODO from pil to opencv
# TODO add more tests


class ProcessLogger:
    '''
    class for user-friendly logging:
        regular logging with newlines in terminal
        logging with clearing previous output in Jupyter
    '''

    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger
        self.slide_name = None  # for testing runs set initially to None
        self.slide_names = None
        self.slide_n = None
        self.tiles = None

    def info_regular(self, message: str):
        '''for regular .info logging'''
        self.logger.info(message)

    def slide_list(self, slides: List[Path]) -> None:
        '''all slide names to be normalised '''
        slide_names = [slide.name for slide in slides]
        self.slide_names = slide_names

    def current_slide(self, slide: Path) -> None:
        '''
        current slide info: current tile, slide name,
        slide's order within all other slides
        '''
        self.tile_n = 0  # starting tile number; set to 0 with each next slide
        self.slide_name = slide.name
        self.slide_n = self.slide_names.index(slide.name)

    def total_tiles(self, tiles):
        '''total number of tiles of the current slide'''
        self.tiles = len(tiles)

    def next_tile(self):
        '''currently processed tile number increment'''
        self.tile_n += 1

    def info(self, message: str):
        '''
        main status logger
        format:
                Slide 1/12 SlideName.svs tile 1/12 operation_name
        '''
        if not self.slide_name:  # for testing runs or status logging outside of normalisation
            self.info_regular(message)
        else:  # formatted logging when slide actually normalised
            self.logger.info(
                f'Slide {self.slide_n + 1}/{len(self.slide_names)} {self.slide_name} tile {self.tile_n}/{self.tiles} {message}')
        clear_output(wait=True)

    def warning(self, message: str):
        '''regular .warning logging'''
        self.logger.warning(message)

    def addHandler(self, handler):
        '''for adding file handler while normalising'''
        self.logger.addHandler(handler)


LOGGER = ProcessLogger(LOGGER)


class Normalisation:
    '''
    all heavylifting is defined here
    '''

    @staticmethod
    def read_sector(slide: OpenSlide, location: Tuple[int, int],
                    size_wh: Tuple[int, int]) -> npt.NDArray[Any]:
        '''
        reads a slide sector, swaps the channels, returns as numpy array
        '''
        LOGGER.info('reading slide sector')
        img = np.asarray(slide.read_region(location, 0, size_wh))
        return img[..., 0:3].reshape((-1, 3))

    @staticmethod
    def convert_od(img: npt.NDArray[Any], normalising_c: int) -> npt.NDArray[Any]:
        '''normalises the RGB raw values, converts to optical density'''
        LOGGER.info('od calculation')
        return -np.log((img.astype(DEFAULTS['dtype']) + 1) / normalising_c)

    @staticmethod
    def calculate_hem(od: npt.NDArray[Any], beta: float, alpha: float) -> npt.NDArray[Any]:
        '''
        calculates hematoxylin stain
        '''
        LOGGER.info('thresholdinf OD values')
        od_clean = od[~np.any(od < beta, axis=1)]
        LOGGER.info('calculating eigenvectors & eigenvalues')
        _, eigenvecs = np.linalg.eigh(np.cov(od_clean.T))
        gc.collect()
        # eigenvectors are returned in ascending order, largest two are used
        LOGGER.info('projecting OD values onto the plane')
        projection = od_clean.dot(eigenvecs[:, 1:3].astype(DEFAULTS['dtype']))

        LOGGER.info('calculation angles of the points')
        angs = np.arctan2(projection[:, 1], projection[:, 0])

        ang_min = np.percentile(angs, alpha)
        ang_max = np.percentile(angs, 100 - alpha)

        c_min = eigenvecs[:, 1:3].dot(
            np.array([(np.cos(ang_min), np.sin(ang_min))]).T)
        c_max = eigenvecs[:, 1:3].dot(
            np.array([(np.cos(ang_max), np.sin(ang_max))]).T)

        if c_min[0] > c_max[0]:
            hem = np.array((c_min[:, 0], c_max[:, 0])).T
        else:
            hem = np.array((c_max[:, 0], c_min[:, 0])).T
        del projection
        del od_clean
        del angs
        gc.collect()
        return hem

    @staticmethod
    def calculate_lstsq(y: npt.NDArray[Any], he: npt.NDArray[Any],
                        s_cut: npt.NDArray[Any]) -> npt.NDArray[Any]:
        '''
        calculates lstsq in batches (saturation of the stains)
        '''
        t1 = time()
        LOGGER.info('calculating lstsq in batches (stain saturation)')
        for _, batch in enumerate(np.array_split(y, 80, axis=1)):
            saturation = (
                np.linalg.lstsq(
                    he.astype(np.float32), batch.astype(np.float32), rcond=None
                )[0]
            ).astype(DEFAULTS['dtype'])
            s_cut = np.concatenate((s_cut, saturation), axis=1)
            gc.collect()
        t2 = time()
        LOGGER.info(f'batches done in {int(t2-t1)} seconds')
        return s_cut

    @staticmethod
    def calculate_sp(s_cut: npt.NDArray[Any]) -> npt.NDArray[Any]:
        '''calculates saturation percentiles'''
        return np.array(
            [np.percentile(s_cut[0, :], 99), np.percentile(s_cut[1, :], 99)]
        )

    @staticmethod
    def region_s(img: npt.NDArray[Any], normalising_c: int,
                 alpha: float, beta: float,
                 max_s_ref: npt.NDArray[Any],
                 he_vals: Optional[npt.NDArray[Any]] = None,
                 ) -> Tuple[npt.NDArray[Any], npt.NDArray[Any], npt.NDArray[Any]]:
        '''
        calculates saturation of region
        '''
        od = Normalisation.convert_od(img, normalising_c)

        del img
        gc.collect()

        if he_vals is not None:
            hem = he_vals
        else:
            hem = Normalisation.calculate_hem(od, beta, alpha)
        y = np.reshape(od, (-1, 3)).T

        del od
        gc.collect()

        s_cut = np.empty(shape=[2, 0], dtype=DEFAULTS['dtype'])
        s_cut = Normalisation.calculate_lstsq(y, hem, s_cut)
        max_s = Normalisation.calculate_sp(s_cut)
        tmp = np.divide(max_s, max_s_ref).astype(DEFAULTS['dtype'])

        gc.collect()
        return s_cut, tmp, hem

    @staticmethod
    def s_final(s_cut: npt.NDArray[Any], tmp: npt.NDArray[Any]) -> npt.NDArray[Any]:
        '''
        finilising saturation normalisation
        '''
        LOGGER.info('final saturation normalisation')
        saturation = np.divide(
            s_cut, tmp[:, np.newaxis]).astype(DEFAULTS['dtype'])
        return saturation

    @staticmethod
    def image_restore(s2: npt.NDArray[Any], normalising_c: int,
                      he_ref: npt.NDArray[Any], wh: tuple,
                      output_type: str = 'norm') -> npt.NDArray[Any]:
        '''
        restores image
        '''
        width, height = wh  # for convinient np.reshape use
        LOGGER.info(f'{output_type} image generation')
        if output_type == 'norm':
            img = np.multiply(
                normalising_c, np.exp(-he_ref.dot(
                    s2).astype(DEFAULTS['dtype']))
            )
        else:
            # TODO check if re-definition is less efficient
            i = 0  # if output_type == 'he'
            if output_type == 'eo':
                i = 1
            img = np.multiply(
                normalising_c,
                np.exp(
                    np.expand_dims(-he_ref[:, i], axis=1)
                    .dot(np.expand_dims(s2[i, :], axis=0))
                    .astype(DEFAULTS['dtype'])
                ),
            )
        img = img.astype(np.uint8)
        img[img > 255] = 254
        img = np.reshape(img.T, (height, width, 3))
        return img

    @staticmethod
    def save_jpeg(path: Path, img: Union[npt.NDArray[Any], Image.Image]) -> None:
        '''
        converts to Image object; saves jpeg at path
        '''
        if not isinstance(img, Image.Image):
            img = Image.fromarray(img)
        LOGGER.info(f'saving jpeg image: {path.stem}')
        img.save(path.with_suffix('.jpeg'), 'jpeg',
                 quality=DEFAULTS['jpeg_quality'])

############# NPZ HANDLING CURRENTLY DISABLED #############
    # @staticmethod
    # def save_npz(path: Path, img: npt.NDArray[Any]) -> None:
    #     '''
    #     saves compressed np at path
    #     '''
    #     LOGGER.info(f'saving npz: {path.name}')
    #     np.savez_compressed(path, slide_sector=img)


class SlideTiler:
    '''
    behaviour class for slide tiling
                        ..and stitching back together
    '''

    @staticmethod
    def rows_columns(slide_width_px: int, slide_height_px: int,
                     max_side_px: int) -> Tuple[int, int]:
        '''
        calculates number of rows and columns
        given slide size and maximum side size
        '''
        m_rows = -(slide_width_px // -max_side_px)
        n_columns = -(slide_height_px // -max_side_px)
        return (m_rows, n_columns)

    @staticmethod
    def slice_points(slide_width_px: int, slide_height_px: int,
                     mn: Tuple[int, int]) -> List[Tuple[Tuple[int, int],
                                                        Tuple[int, int]]]:
        '''
        creates a list of tuples with coordinates at which the sldide is sliced
        coordinates defined in row - column order
        returns a list of tuples containing tuples:
                                        - location of the slice
                                        - size of the slice
        '''
        # TODO too bruteforcy, should be rewritten
        m_rows, n_columns = mn
        cutting_cooridinates = []
        column_width_px = slide_width_px // n_columns
        row_height_px = slide_height_px // m_rows

        for m in range(0, m_rows):
            for n in range(0, n_columns):
                location = (n * column_width_px, m * row_height_px)
                current_width_px, current_height_px = column_width_px, row_height_px
                if n == (n_columns - 1):  # last column gets the rest of the slide
                    current_width_px = slide_width_px - n * column_width_px
                if m == (m_rows - 1):  # last row gets the rest of the slide
                    current_height_px = slide_height_px - m * row_height_px
                size = (current_width_px, current_height_px)
                cutting_cooridinates.append((location, size))
        return cutting_cooridinates

    @staticmethod
    def coordinates_dict(cutting_cooridinates: List[Tuple[Tuple[int, int], Tuple[int, int]]]
                         ) -> OrderedDict[int, Tuple[Tuple[int, int], Tuple[int, int]]]:
        '''
        generates dictionary {tile index: (location, size)}

        for better estimation of the slide-specific parameters (tmp and he
        are calculated during the first run) the tile in the middle of the slide
        is normalised at first, as the first ones may not contain any information
        apart from the background
        => move the central tile to the beginning of the "queue"
        '''
        mapping = OrderedDict()
        for i, location_size in enumerate(cutting_cooridinates):
            mapping[i] = location_size

        if DEFAULTS['first_tile'] == 'middle':
            middle_tile = max(mapping.keys()) // 2
            mapping.move_to_end(middle_tile, last=False)
        else:  # TODO implement interactive selection in jupyter
            mapping.move_to_end(DEFAULTS['first_tile'], last=False)
        return mapping

    @staticmethod
    def slicer(width_height_px: Tuple[int, int],
               max_side_px: int) -> Tuple[Tuple[int, int], OrderedDict[int,
                                                                       Tuple[Tuple[int, int], Tuple[int, int]]]]:
        '''
        combines calculation of row/column number and slice points/sizes
        '''
        width_px, height_px = width_height_px
        m_n = SlideTiler.rows_columns(width_px, height_px, max_side_px)
        slices = SlideTiler.slice_points(width_px, height_px, m_n)
        slices = SlideTiler.coordinates_dict(slices)
        return m_n, slices


############# NPZ HANDLING CURRENTLY DISABLED #############
    # @staticmethod
    # def npz_sticher(stain_type: str, current_slide: CurrentSlide) -> None:
    #     '''
    #     stitches normalised NumPy batches (located in the temporary folder) together
    #     '''
    #     m_rows, n_cols = current_slide.mn
    #     slice_index = 0
    #     stacked_rows = ()
    #     for m in range(m_rows):
    #         row = ()
    #         for n in range(n_cols):
    #             slice = np.load(Path(current_slide.temp_subpath, f'{slice_index}_{stain_type}.npz'))[
    #                 'slide_sector'
    #             ]
    #             row += (slice,)
    #             slice_index += 1
    #         row_stitched = np.concatenate(row, axis=1)
    #         stacked_rows += (row_stitched,)
    #     image_stitched = np.concatenate(stacked_rows, axis=0)
    #     Normalisation.save_jpeg(Path(current_slide.norm_path, current_slide.slide_path.stem),
    #                             image_stitched)

    @staticmethod
    def jpeg_stitcher(*args) -> None:
        '''
        stitches normalised slide tiles (located in the temporary folder) together
        '''
        LOGGER.info('stitching image together')
        # if libvips is installed, and prefered by the user
        if 'pyvips' in sys.modules and DEFAULTS['prefer_vips']:
            SlideTiler.vips_stitcher(*args)
        else:
            SlideTiler.pil_stitcher(*args)

    @staticmethod
    def pil_stitcher(stain_type: str, current_slide: CurrentSlide) -> None:
        '''
        uses Pil for stitching if libvips is not installed
        works fine for 20x zoomed slides
        '''
        LOGGER.info('stitching using PIL')
        LOGGER.info(f'stitching slide: {current_slide.slide_path.name}')
        new_slide = Image.new(
            mode='RGB', size=current_slide.wh, color=(0, 0, 0))
        for i, (location, _) in current_slide.tile_map.items():
            tile = Image.open(Path(current_slide.temp_subpath,
                              f'{i}_{stain_type}.jpeg'), 'r')
            new_slide.paste(tile, location)
        LOGGER.info('stitching finished')
        Normalisation.save_jpeg(Path(current_slide.norm_path,
                                     f'{stain_type}_{current_slide.slide_path.stem}'),
                                new_slide)
        if DEFAULTS['thumbnail']:
            SlideTiler.pil_thumbnail(current_slide, new_slide, stain_type)

    @staticmethod
    def pil_thumbnail(current_slide: CurrentSlide,
                      slide: Union[npt.NDArray[Any], Image.Image],
                      stain_type: str) -> None:
        '''creates thumbnail if pil is used'''
        LOGGER.info('creating normalised thumbnail')
        if not isinstance(slide, Image.Image):
            slide = Image.fromarray(slide)
        twidth_height = SlideTiler.thumbnail_size(current_slide.wh)
        slide.thumbnail(twidth_height)
        slide.save(
            Path(current_slide.norm_path,
                 f'thumbnail_{stain_type}_{current_slide.slide_path.stem}.jpeg'))

    # SlideTiler.jpeg_stitcher(stain_type, self.current_slide)
    @staticmethod
    def vips_stitcher(stain_type: str, current_slide: CurrentSlide) -> None:
        '''
        uses libvips-based pyvips for stitching if installed
        more efficient and works with large slides (40x zoom)
        '''
        LOGGER.info('stitching using vips')
        LOGGER.info(f'stitching slide: {current_slide.slide_path.name}')
        tile_paths = [Path(current_slide.temp_subpath, f'{i}_{stain_type}.jpeg')
                      for i in range(len(current_slide.tile_map))]
        tiles = [pyvips.Image.new_from_file(str(tile_path), access='sequential')
                 for tile_path in tile_paths]
        normalised_slide = pyvips.Image.arrayjoin(tiles,
                                                  across=current_slide.mn[1])
        # TODO check for size limit 65535
        mpp_x = current_slide.os_slide.properties['openslide.mpp-x']
        # mpp_y = current_slide.os_slide.properties['openslide.mpp-y'] # used for Aperio metadata
        magnification = current_slide.os_slide.properties['openslide.objective-power']
        # currently spoofs Aperio metadata ( Magnification in OME Schema is not recognised by QuPath..)
        normalised_slide.set_type(pyvips.GValue.gstr_type,
                                  'image-description',
                                  f'''Aperio Image Library v12.4.0 {normalised_slide.width}x{normalised_slide.height}] | AppMag = {magnification}| MPP={mpp_x}
            ''',
                                  )
        # writes a binary file
        normalised_slide.tiffsave(str(Path(current_slide.norm_path,
                                           f'{stain_type}_{current_slide.slide_path.stem}.tif')),
                                  compression=DEFAULTS['vips_tiff_compression'],
                                  bigtiff=True,
                                  tile=True,
                                  Q=DEFAULTS['jpeg_quality'])

        if DEFAULTS['thumbnail']:
            SlideTiler.vips_thumbnail(stain_type, current_slide)

    @staticmethod
    def vips_thumbnail(stain_type: str, current_slide: CurrentSlide) -> None:
        '''creates thumbnail if vips is used'''
        LOGGER.info('creating normalised thumbnail')
        twidth, theight = SlideTiler.thumbnail_size(current_slide.wh)
        slide_path = Path(current_slide.norm_path,
                          f'{stain_type}_{current_slide.slide_path.stem}.tif')
        thumbnail = pyvips.Image.thumbnail(
            str(slide_path), twidth, height=theight)
        thumbnail.jpegsave(str(Path(current_slide.norm_path,
                                    f'thumbnail_{stain_type}_{current_slide.slide_path.stem}.jpeg')))
        # thumbnail = normalised_slide.thumbnail_image(twidth,
        #                                              height=theight,
        #                                              access='seqiential')
        # LOGGER.info('thumbnail created')
        # thumbnail.jpegsave(str(result_path.with_suffix('.jpeg')))

    @staticmethod
    def slide_thumbnail(slide: CurrentSlide) -> None:
        '''creates thumbnail from the original slide'''
        LOGGER.info('creating thumbnail')
        twidth, theight = SlideTiler.thumbnail_size(slide.wh)
        thumbnail = slide.os_slide.get_thumbnail((twidth, theight))
        thumbnail.save(Path(slide.norm_path,
                            f'thumbnail_{slide.slide_path.stem}.jpeg'))

    @staticmethod
    def thumbnail_size(slide_width_height: Tuple[int, int]) -> Tuple[int, int]:
        '''
        calculates size of the thumbnail given max thumbnail side size and
        original slide size
        '''
        scale = DEFAULTS['thumbnail_max_side'] / max(slide_width_height)
        return int(scale * slide_width_height[0]), int(scale * slide_width_height[1])


class NormaliseSlides:
    '''
    wrapper for user input forwarding to the FileData
    & further slide normalisation
    '''

    def __init__(self, rewrite, **kwargs) -> None:
        """
        Creates a NormaliseSlides

        NormaliseSlides is the main interface and, first of all, forwards all of
        the provided `kwargs` to the :class:`dogsled.user_input.FileData` class
        which check if the arguments are correct (whether the paths exist/have to be
        created etc.). Thiis class is also used to start the normalisation and, if
        required, repeat the stitching of the tiled normalised slide. All provided
        paths can be of type :class:`str` or :class:`pathlib.Path`

        Parameters
        ----------
        norm_path:
            [required] path which should hold the normalised versions (JPEG or TIF) of the slides
        slide_names:
            names of the slides to be normalised; if several slides have to be
            normalised, provide the names in a list
        qpproj_path:
            [required or svs_path] specifies the path to the .qpproj file in case the slides of a QuPath
            project have to be normalised
        slides_indexes:
            when `qpproj_path` is specified, the slides to be normalised can also be
            specified using their index. In this case, the index corresponds to the
            index in the QuPath project (check in QuPath GUI of by using paquo)
        svs_path:
            [required or qpproj_path] the slides can be also specified by providing the path to the folder they
            are located in. In this case, it is possible to specify their subset using
            `slide_names`
        temp_path:
            folder for holding the temporary data- slide tiles which have been already
            normalised and will be stitched together late on
        rewrite:
            in case the temporary folder already exists (if the normalisation of the
            slides in the specified folder was done previously), it is important to
            set this flag to `True`, otherwise, an error will be fired
        Returns
        -------
            NormaliseSlides class instance
        """
        self.file_data = FileData(rewrite=rewrite, **kwargs)
        self.slide_paths = self.file_data.slide_info.to_process_paths
        self.current_slide = CurrentSlide(temp_path=self.file_data.path_info.temp_path,
                                          norm_path=self.file_data.path_info.norm_slide_path)
        self.check_resources()

        logger_fh = logging.FileHandler(
            Path(self.file_data.path_info.norm_slide_path, 'dogsled.log'))
        logger_fh.setLevel(logging.INFO)
        logger_fh.setFormatter(logging.Formatter(
            '%(asctime)s %(module)s %(levelname)s: [ %(message)s ]', '%m/%d/%Y %I:%M:%S %p'))
        LOGGER.addHandler(logger_fh)
        LOGGER.slide_list(self.slide_paths)

        # intercepting rewrite kwarg for temp path creation
        # as the temporary subfolders are creaetd when the actual normalisation starts
        self.rewrite = rewrite

    def check_resources(self) -> None:
        '''
        checks required resources (RAM and space)
        '''
        self.max_side_px = ResourceChecker().tile_size
        LOGGER.warning(
            f'based on the available RAM, maximum tile side size will be used: {self.max_side_px} px')

        free_space, space_required, all_svs = ResourceChecker().space(self.slide_paths,
                                                                      self.current_slide.norm_path)
        if all_svs:
            LOGGER.warning(
                f'normalisation of the selected slides may take up to {space_required} MB')
            LOGGER.warning(
                f'available on the seleced disk (norm_path): {free_space} MB')
        else:
            LOGGER.warning(
                f'normalisation of the selected slides might require significant space')
            LOGGER.warning(
                f'available on the seleced disk (norm_path): {free_space} MB')

    def start(self) -> None:
        '''
        full :strike:`fire` normalisation starter
        '''
        for slide_path in self.slide_paths:
            self.current_slide.slide_path = slide_path
            LOGGER.current_slide(self.current_slide.slide_path)
            self.process_slide(max_side_px=self.max_side_px)
        LOGGER.info_regular('so far, so good')  # when everything is finisehed

    def slide_pre_processing(self, max_side_px: int) -> None:
        '''
        re-usable slide pre-processing
        '''
        os_slide = OpenSlide(str(self.current_slide.slide_path))
        slide_wh = os_slide.dimensions
        self.current_slide.wh = slide_wh
        self.current_slide.os_slide = os_slide
        LOGGER.info_regular(f'using maximum tile size of {max_side_px} pixel')
        self.current_slide.mn, self.current_slide.tile_map = SlideTiler.slicer(
            slide_wh, max_side_px)
        LOGGER.total_tiles(self.current_slide.tile_map)

    def repeat_stitching(self, stain_types: Union[str, List[str]] = DEFAULTS['output_type']) -> None:
        '''
        in case the slide tiles were processed, but the stitching caused a crash
        repeats stitching only
        '''
        if len(self.slide_paths) > 1:
            raise UserInputError(
                message='only one slide has to be selected for repeated stitching')
        self.current_slide.slide_path = self.slide_paths[0]
        self.slide_pre_processing(max_side_px=self.max_side_px)
        self.current_slide.temp_subpath = Path(self.current_slide.temp_path,
                                               self.current_slide.slide_path.stem)
        for stain_type in stain_types:
            SlideTiler.jpeg_stitcher(stain_type, self.current_slide)
        LOGGER.info_regular('so far, so good')  # when everything is finisehed

    def cleaner(self, stain_type: str, current_slide: CurrentSlide) -> None:
        '''
        removes temporary files after finished normalisation
        if detects that the normalised slide and tiles are present
        !! does not remove the temporary folder !!
        '''
        LOGGER.info('removing temporary files')
        norm_path = Path(current_slide.norm_path,
                         f'{stain_type}_{current_slide.slide_path.stem}')
        i_range = len(current_slide.tile_map)
        if norm_path.with_suffix('.jpeg').exists() or norm_path.with_suffix('.tif').exists():
            if not (False in [Path(current_slide.temp_subpath, f'{i}_{stain_type}.jpeg').exists() for i in range(i_range)]):
                for i in range(i_range):
                    Path(current_slide.temp_subpath,
                         f'{i}_{stain_type}.jpeg').unlink()
        else:
            raise CleaningError(
                message=f'removing temporary files was not possible')

    def process_slide(self, max_side_px: int) -> None:
        '''
        wrapper for full slide processing
        '''
        self.slide_pre_processing(max_side_px)
        LOGGER.info_regular(
            f'normalising {self.current_slide.slide_path.name}')
        thumbnail_path = Path(self.current_slide.norm_path,
                              f'thumbnail_{self.current_slide.slide_path.stem}.jpeg')
        # creates thumbnail only if it is defined in DEFAULTS and if it does not exist already
        if DEFAULTS['thumbnail'] and not thumbnail_path.exists():
            SlideTiler.slide_thumbnail(self.current_slide)
        # for the first run of the normaliser on the tile in the middle:
        first_run = True
        # flag indicates whether there is only one tile
        single_run = len(self.current_slide.tile_map) == 1
        if not single_run:
            # create a subfolder for the tiles
            self.current_slide.temp_subpath = Path(self.current_slide.temp_path,
                                                   self.current_slide.slide_path.stem)
            PathCreator.create_path(path=self.current_slide.temp_subpath,
                                    rewrite=self.rewrite)

        # run normalisation for all tiles in tile_map
        for i, location_size in self.current_slide.tile_map.items():
            LOGGER.next_tile()
            LOGGER.info(f'first run execution: {first_run}')
            self.slice_normalisation(i, location_size, single_run, first_run)
            first_run = False
        # run tile stitching
        if not single_run:
            for stain_type in DEFAULTS['output_type']:
                SlideTiler.jpeg_stitcher(stain_type, self.current_slide)
                if (DEFAULTS['remove_temporary_files'] is True):  # check explicitly for True
                    self.cleaner(stain_type, self.current_slide)

    def slice_normalisation(self, slice_index: int,
                            location_size: Tuple[Tuple[int, int], Tuple[int, int]],
                            single_run: bool, first_run: bool):
        '''
        wrapper for slide slice processing
        '''
        location, size = location_size
        img = Normalisation.read_sector(
            self.current_slide.os_slide, location, size)
        LOGGER.info('slide sector in memory')
        if first_run:  # use first slice as a reference for tmp and he calculation
            # TODO check if temp and he are overwritten
            s_cut, self.tmp, self.he = Normalisation.region_s(img,
                                                              DEFAULTS['normalising_c'],
                                                              DEFAULTS['alpha'],
                                                              DEFAULTS['beta'],
                                                              DEFAULTS['max_s_ref'])
        else:
            s_cut, _, _ = Normalisation.region_s(img,
                                                 DEFAULTS['normalising_c'],
                                                 DEFAULTS['alpha'],
                                                 DEFAULTS['beta'],
                                                 DEFAULTS['max_s_ref'],
                                                 self.he)
        LOGGER.info('s_cut, tmp, calculated')
        c2 = Normalisation.s_final(s_cut, self.tmp)
        del s_cut
        gc.collect()
        for stain_type in DEFAULTS['output_type']:
            restored_img = Normalisation.image_restore(c2,
                                                       DEFAULTS['normalising_c'],
                                                       DEFAULTS['he_ref'],
                                                       size,
                                                       output_type=stain_type)
            LOGGER.info('image restored')
            if not single_run:
                # np.savez_compressed(Path(self.temp_path, f'{slice_index}_{stain_type}.npz'),
                #                     slide_sector=restored_img)
                # save as a tile in temp path
                Normalisation.save_jpeg(Path(self.current_slide.temp_subpath,
                                             f'{slice_index}_{stain_type}'),
                                        restored_img)
            else:
                # ..or as an end-result in the norm_path
                Normalisation.save_jpeg(Path(self.current_slide.norm_path,
                                             f'{stain_type}_{self.current_slide.slide_path.stem}'),
                                        restored_img)
                # create additional tile TODO consider removing?
                if DEFAULTS['thumbnail']:
                    SlideTiler.pil_thumbnail(
                        self.current_slide, restored_img, stain_type)
            del restored_img
            gc.collect()
