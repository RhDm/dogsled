''''
User input manager
The user can profide the following data:
    - path to the QuPath project
        - or a path to the folder containing SVS slides
    - indexes of the slides to normalise (paquo- based indexes)
    - names of the slides to normalise (with or without .svs extension)
    - folder for holding temporary data
checks & verifies all user-provided info:
    - all defined paths
    - creates temporary folder if it is not defined
    - collects full paths of the slides which are defined for normalisation
If no names or idexes of the slides are provided, all slides in the folder/Qupath
project are normalised
'''''
import re
import logging
from pathlib import Path
from urllib.parse import unquote
from typing import Union, Optional, Tuple, List
from dataclasses import dataclass, field

from paquo.projects import QuPathProject

from dogsled.slides import QuPathSlides
from dogsled.errors import UserInputError
from dogsled.paths import PathChecker, PathCreator
from dogsled.defaults import DEFAULTS
# TODO extend support to other OpenSlide supported formats

LOGGER = logging.getLogger(__name__)


path_checker = PathChecker()
path_creator = PathCreator()


@dataclass(repr=True)
class UserSlideInput:
    '''
    class for holding all user-selected slide data:
    user-defined names of slides
    user-defined indexes of slides
    processed indexes of slices (ones to normalise)
    '''
    names: List = field(default_factory=list)
    indexes: List = field(default_factory=list)
    to_process_i: List = field(default_factory=list)
    to_process_paths: List = field(default_factory=list)

    def __str__(self) -> str:  # info for the user => __str__
        return f'provided slide indexes: {self.to_process_i},\n\
            names: {self.names}\n\
            slides to normalise: {*[slide.name for slide in self.to_process_paths],}'


@dataclass(repr=True)
class SystemPaths:
    '''
    class for holding all user-defined and derived paths
    '''
    norm_slide_path: Path
    temp_path: Optional[Path] = None
    svs_path: Optional[Path] = None
    qpproj_path: Optional[Path] = None

    def __str__(self) -> str:
        if self.qpproj_path:
            return f'QuPath project at at: {self.qpproj_path}\n\
                path for normalised slides: {self.norm_slide_path},\n\
                temporary path: {self.temp_path}'
        return f'slides at {self.svs_path}\n\
                path for normalised slides: {self.norm_slide_path},\n\
                temporary path: {self.temp_path}'


class InputChecker:
    '''
    class for checking all user-defined constants, i.e. paths & selected slides
    '''

    def __init__(self,
                 slide_names: List[str],
                 provided_slides_names: List[str],
                 provided_slides_i: List[int]) -> None:
        '''take provided info, return valid index list'''
        self.indexes = self.controller(slide_names,
                                       provided_slides_names,
                                       provided_slides_i)

    @classmethod
    def check_indexes(cls,
                      slide_names: List[str],
                      provided_slides_i: Optional[List[int]] = None) -> set:
        '''
        checks if the user-defined indexes are valid
        raises error if not & tells which ones are wrong
        '''
        if not provided_slides_i:
            return set()

        if (out_of_range := InputChecker.check_index_range(provided_slides_i, slide_names)):
            LOGGER.error(
                f'please check provided indexes (must be zero-based): {out_of_range}')
            raise UserInputError(
                incorrect_data=str(out_of_range),
                message=f'please check provided indexes (must be zero-based)'
            )
        return set(provided_slides_i)

    @classmethod
    def check_index_range(cls,
                          provided_slides_i: List[int],
                          slide_names: List[str]):
        '''checks for correctness of the indexes'''
        if max(provided_slides_i) > (len(slide_names) - 1):
            out_of_range = [i for i in provided_slides_i if i >
                            (len(slide_names) - 1)]
            return out_of_range

    @classmethod
    def check_names(cls,
                    slide_names: List[str],
                    provided_slides_names: Optional[List[str]] = None) -> set:
        '''
        checks if the user-defined names (with or without '.svs') are valid
        raises error if not & tell which one is wrong
        returns indexes of the provided names
        '''
        if not provided_slides_names:
            return set()

        if not isinstance(provided_slides_names, list):
            provided_slides_names = [provided_slides_names]

        to_process = set()
        for name in provided_slides_names:
            if not re.search('.svs', name):
                name += '.svs'
            try:
                to_process.add(slide_names.index(name))
            except ValueError:
                LOGGER.error(f'please check provided slide name: {name}')
                raise UserInputError(
                    incorrect_data=name,
                    message=f'please check provided slide name: {name}'
                )
        return to_process

    def controller(self,
                   slide_names: List[str],
                   provided_slides_names: List[str],
                   provided_slides_i: List[int]) -> List[int]:
        '''
        combines sets of indexes derived from the user-devined names and
        indexes, combines them into one set
        converts to a list (slight performance improvement..?)
        '''
        indexes = InputChecker.check_indexes(slide_names, provided_slides_i)
        indexes.update(InputChecker.check_names(
            slide_names, provided_slides_names))
        return list(indexes)


class FileData:
    '''
    combines all data together
    i.e. all paths, slide names, slide indexes
    if path with svs and QuPath project paths are specified, QuPath project has priority
    '''

    def __init__(self,
                 norm_path: Union[str, Path],
                 slides_indexes: Optional[List[int]] = None,
                 slide_names: Optional[List[str]] = None,
                 qpproj_path: Union[str, Path, None] = None,
                 svs_path: Union[str, Path, None] = None,
                 temp_path: Union[str, Path, None] = None,
                 rewrite: Optional[bool] = None
                 ) -> None:

        self.path_info = self.system_paths(norm_path,
                                           svs_path,
                                           qpproj_path,
                                           temp_path,
                                           rewrite_flag=rewrite)

        self.slide_info = self.slides_to_process(self.path_info,
                                                 slide_names,
                                                 slides_indexes)

    def __repr__(self) -> str:
        return f'paths: {self.path_info}\n\
            slides: {self.slide_info}'

    def system_paths(self,
                     norm_slide_path: Union[str, Path],
                     svs_path: Optional[Union[str, Path]] = None,
                     qpproj_path: Optional[Union[str, Path]] = None,
                     temp_path: Optional[Union[str, Path]] = None,
                     rewrite_flag=False) -> SystemPaths:
        '''
        returns instance of UserSlideInput which holds
        controlled system paths
        if both, svs_path and qpproj_path, are provided, then qpproj_path has priority
        created paths (temporary path)
        temporary path is created either at the given path or as temp folder in norm_slide_path)
        '''
        if not svs_path and not qpproj_path:
            LOGGER.error(
                f'either path with SVS slides or QuPath project path must be provided')
            raise UserInputError(
                incorrect_data='',
                message=f'either path with SVS slides or QuPath project path must be provided'
            )
        path_holder = SystemPaths(
            norm_slide_path=path_checker.str_to_path(norm_slide_path)
        )
        if qpproj_path:
            path_holder.qpproj_path = path_checker.str_to_path(qpproj_path)
        else:
            path_holder.svs_path = path_checker.str_to_path(svs_path)

        # TODO maybe should switch to tempfile
        # tempfile.TemporaryDirectory(suffix=None, prefix=slide_stem, dir=temp_path)
        if temp_path:
            temp_path = path_checker.str_to_path(temp_path)
        else:
            temp_path = Path(path_holder.norm_slide_path,
                             DEFAULTS['temporary_folder_name'],)
        path_creator.create_path(temp_path, rewrite=rewrite_flag)
        path_holder.temp_path = temp_path

        return path_holder

    @staticmethod
    def qupath_image_path(index: int,
                          paquo_project: QuPathProject) -> Path:
        '''
        produces valid path to the svs slide given index in the paquo project image entry
        '''
        # TODO probably should be replaced- too slow
        try:
            str_path = re.search('.*file:(.+(\.svs|\.tif|\.scn|\.vms|\.vmu|\.ndpi|\.mrxs|\.svslide|\.bif))',
                                 str(paquo_project.images[index]._image_server.getPath()))[1]
            return Path(unquote(str_path))
        except:
            raise UserInputError(message='can\'t process Qupath over paquo')

    def get_slide_names(self,
                        path_info: SystemPaths) -> Tuple[list[str], Optional[QuPathProject]]:
        '''
        returns all names of the slides in the QuPath project
        or at the given path
        '''
        if path_info.qpproj_path:  # user-provided qupath project file has priority
            paquo_project = QuPathSlides(path_info.qpproj_path).pq
            all_slide_names = [
                slide.image_name for slide in paquo_project.images]
        else:
            paquo_project = None
            all_slide_names = [slide.name for slide in
                               path_info.svs_path.iterdir()
                               if slide.suffix == '.svs' and not slide.name.startswith('.')]

        return all_slide_names, paquo_project

    def slides_to_process(self,
                          path_info: SystemPaths,
                          slide_names: Optional[List[str]],
                          slide_indexes: Optional[List[int]]) -> UserSlideInput:
        '''
        creates instance of UserSlideInput which holds
        user-defined indexes of slides (only if qpproj path is defined)
        user-defined names of slides (if svs path or qpproj path are defined)
        processed indexes
        instance of SystemPaths must be previously created
        '''
        slide_info = UserSlideInput(names=slide_names,
                                    indexes=slide_indexes)

        # get all slide names at in the folder/in the QuPath project
        all_slide_names, paquo_project = self.get_slide_names(path_info)

        # get the indexes of the slides to process
        slide_info.to_process_i = InputChecker(all_slide_names,
                                               slide_info.names,
                                               slide_info.indexes).indexes
        # get all paths of the slides to process
        if slide_info.to_process_i:  # if the user provided slide indexes or names
            if path_info.qpproj_path:
                slide_paths = [self.qupath_image_path(i, paquo_project)
                               for i in slide_info.to_process_i]
            else:
                slide_paths = [Path(path_info.svs_path, all_slide_names[i])
                               for i in slide_info.to_process_i]
        else:  # normalise all of no names or idexes are defined
            if path_info.svs_path:  # if the path to the svs files is provided
                slide_paths = [Path(path_info.svs_path, slide)
                               for slide in all_slide_names]
            else:
                # if path to the qpproj is provided
                # full paths are used in this case as the location might differ
                slide_paths = [self.qupath_image_path(i, paquo_project)
                               for i in range(len(all_slide_names))]
        slide_info.to_process_paths = slide_paths

        return slide_info
