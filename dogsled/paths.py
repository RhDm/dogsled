''''
Path manager

Checks whether the user-provided folders exist
Creates a sub-folder system & checks if folders already exist
'''''
from pathlib import Path
import logging
from typing import Union, Optional
from dogsled.errors import UserInputError

LOGGER = logging.getLogger(__name__)


class PathChecker:
    '''
    simple class for reading the user-provided path as str or Path
    & checking if path is correctly defined
    '''

    def __init__(self) -> None:
        pass

    def str_to_path(self, path: Optional[Union[str, Path]]) -> Path:
        '''
        convert string to Path
        then check if path exists
        '''
        if isinstance(path, str):
            path = Path(path)
        if path is None or not path.exists():
            LOGGER.exception(f'path {path} does not exist')
            raise UserInputError(
                incorrect_data=str(path),
                message=f'path {path} does not exist'
            )
        return path


class PathCreator:
    '''
    creates path if it does not exist
    rewrites it if rewrite = True
    '''

    def __init__(self) -> None:
        pass

    @staticmethod
    def create_path(path: Path,
                    child_path: Optional[Union[Path, str]] = None,
                    rewrite=False) -> None:
        '''
        checks if parent path exists, creates child path in it
        '''
        if child_path:
            path = Path(path, child_path)
        try:
            path.mkdir(parents=False,
                       exist_ok=rewrite)
            if not path.exists():
                raise UserInputError(
                    incorrect_data=str(path),
                    message=f'path {path} can not be created'
                )
        except FileExistsError:
            raise UserInputError(
                incorrect_data=str(path),
                message=f'path {path} already exist; plese set \
                    rewrite to True or define another path'
            )
