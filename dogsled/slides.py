'''
Slide manager
Creates paquo project instance

TODO probably should remove the whole module
'''

from typing import Union
from pathlib import Path
import logging
from typing import Tuple
from dataclasses import dataclass
from collections import OrderedDict

from openslide import OpenSlide
from paquo.projects import QuPathProject

from dogsled.paths import PathChecker

LOGGER = logging.getLogger(__name__)
path_checker = PathChecker()


@dataclass
class CurrentSlide:
    '''
    class for holding data on the current slide processed
    to be shared between functions and classes for convinient slide info managing
    '''
    # source slide path
    slide_path: Path = None
    # folder for keeping normalised slides
    norm_path: Path = None
    # folder for keeping temporary subfolders
    temp_path: Path = None
    # for holding tiles of the current tile
    temp_subpath: Path = None
    # OpenSlide instance
    os_slide: OpenSlide = None
    # original slide width x height
    wh: Tuple[int, int] = None
    # tile m x n matrix
    mn: Tuple[int, int] = None
    # tile location size tuples
    tile_map: OrderedDict[int, Tuple[Tuple[int, int], Tuple[int, int]]] = None


class QuPathSlides:
    '''
    accepts .qpproj path, passes it to paquo
    returns paquo project class instance
    '''

    def __init__(self,
                 qpproj_path: Union[str, Path]):
        self.qpproj_path = qpproj_path
        self.pq = self.path_to_paquo()

    def path_to_paquo(self) -> QuPathProject:
        '''
        tests the provided path
        passes the path to paquo; returns paquo instance
        '''
        qupath_path = path_checker.str_to_path(self.qpproj_path)
        try:
            return QuPathProject(qupath_path)
        except Exception as paquo_error:
            LOGGER.exception(
                f'Error occured when opening project with paquo: {paquo_error}')
