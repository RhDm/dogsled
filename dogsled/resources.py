'''
all reaource estimators live here
'''
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
import logging
import psutil

from dogsled.defaults import DEFAULTS

LOGGER = logging.getLogger(__name__)


@dataclass
class ResourceInfo:
    '''simple class for holding the resource data'''
    reource_name: str
    resource_required: int
    resource_available: int


class ResourceEstimator:
    '''
    class for estimation of the resources (available space and RAM)
    '''

    def __init__(self,
                 slide_paths: List[Path]) -> None:

        self.space_required = self.space_estimator(slide_paths)

    def space_estimator(self,
                        slide_paths) -> int:
        '''
        estimates the size of th normalised jpeg file given svs size
        uses simple linear regression based on data on 56 normalised slides
        '''
        svs_file_sizes = [slide.stat().st_size for slide in slide_paths]
        jpeg_file_sizes = [self.mapping_equation(slide.stat().st_size)
                           for slide in slide_paths]
        total_required = max(svs_file_sizes) + sum(jpeg_file_sizes)
        return total_required

    def mapping_equation(self, svs_size: int) -> int:
        '''mapping of svs to jpeg'''
        return int(-2.28 + 1.51 * svs_size)


class ResourceChecker:
    '''
    checks how much RAM is available
    => tile side size estimation
    .. and how much space is present/required using ResourceEstimator
    '''

    def __init__(self):
        self._mpx: Optional[int] = None

    @property
    def tile_size(self) -> int:
        '''uses RAM size to map to the tile size'''
        available_mb = psutil.virtual_memory().available >> 20
        closest_mb = min(DEFAULTS['ram_megapixel'].keys(),
                         key=lambda x: abs(x - available_mb))
        self._mpx = DEFAULTS['ram_megapixel'][closest_mb]
        return self._mpx

    @staticmethod
    def space(slide_paths: List[Path], norm_path: Path) -> Tuple[int, Optional[int], bool]:
        '''calculates required space for normalisation of the slides selected'''
        free_space = psutil.disk_usage(norm_path).free >> 20
        space_required = None
        # if any(True for path in slide_paths if path.suffix != '.svs'):
        #     # calculate only if all slides are .svs
        #     pass
        # else:
        all_svs = all(map(lambda x: x.suffix == '.svs', slide_paths))
        space_required = ResourceEstimator(
            slide_paths).space_required >> 20
        return free_space, space_required, all_svs
