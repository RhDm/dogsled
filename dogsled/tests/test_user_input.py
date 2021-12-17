from pathlib import Path
import pytest
import logging
import platform

from dogsled.user_input import InputChecker, FileData
from dogsled.errors import UserInputError
from dogsled.defaults import DEFAULTS


LOGGER = logging.getLogger(__name__)


def test_input_checker(test_slides_names, test_slides_i):
    ic = InputChecker(slide_names=test_slides_names,
                      provided_slides_names=test_slides_names,
                      provided_slides_i=test_slides_i)
    assert ic.indexes == test_slides_i


def test_input_checker_wrong_i(test_slides_names, test_slides_i):
    wrong_i = test_slides_i[:]
    wrong_i.append(len(test_slides_i) + 1)
    wrong_names = test_slides_names[:]
    wrong_names.append("some_random_slide_name.svs")
    with pytest.raises(UserInputError):
        _ = InputChecker(slide_names=test_slides_names,
                         provided_slides_names=test_slides_names,
                         provided_slides_i=wrong_i)
    with pytest.raises(UserInputError):
        _ = InputChecker(slide_names=test_slides_names,
                         provided_slides_names=wrong_names,
                         provided_slides_i=test_slides_i)


def test_file_data_qupath_svs(norm_path, test_slides_names, test_slides_i, qupath_project, test_slides):
    """When qupath project file and svs path are defined."""
    fd = FileData(norm_path=norm_path,
                  slides_indexes=test_slides_i,
                  slide_names=test_slides_names,
                  qpproj_path=qupath_project.path,
                  source_path=test_slides[0].parents[0],
                  rewrite=True)
    assert fd.path_info.norm_slide_path == norm_path
    assert fd.path_info.source_path == None
    assert fd.path_info.qpproj_path == qupath_project.path
    assert fd.path_info.temp_path == Path(
        norm_path, DEFAULTS.temporary_folder_name)

    assert fd.slide_info.to_process_i == test_slides_i
    if platform.system() != "Windows":
        assert fd.slide_info.to_process_paths == test_slides
    # inconsistent full path names on Windows- use only file names for now..
    else:
        paths_x = [path.name for path in fd.slide_info.to_process_paths]
        paths_y = [path.name for path in test_slides]
        assert paths_x == paths_y


def test_file_data_qupath(norm_path, test_slides_names, test_slides_i, qupath_project, test_slides):
    """When only qupath project file defined."""
    fd = FileData(norm_path=norm_path,
                  slides_indexes=test_slides_i,
                  slide_names=test_slides_names,
                  qpproj_path=qupath_project.path,
                  source_path=test_slides[0].parents[0],
                  rewrite=True)
    assert fd.path_info.norm_slide_path == norm_path
    assert fd.path_info.qpproj_path == qupath_project.path
    assert fd.path_info.temp_path == Path(
        norm_path, DEFAULTS.temporary_folder_name)

    assert fd.slide_info.indexes == test_slides_i
    assert fd.slide_info.to_process_i == test_slides_i
    if platform.system() != "Windows":
        assert fd.slide_info.to_process_paths == test_slides
    # inconsistent full path names on Windows- use only file names for now..
    else:
        paths_x = [path.name for path in fd.slide_info.to_process_paths]
        paths_y = [path.name for path in test_slides]
        assert paths_x == paths_y


def test_file_data_svs(norm_path, test_slides_names, test_slides_i, test_slides):
    """When only svs path is defined."""
    sorted_test_slides = test_slides[:].sort()
    fd = FileData(norm_path=norm_path,
                  slides_indexes=test_slides_i,
                  slide_names=test_slides_names,
                  source_path=test_slides[0].parents[0],
                  rewrite=True)
    assert fd.path_info.source_path == test_slides[0].parents[0]
    assert fd.path_info.norm_slide_path == norm_path
    assert fd.path_info.qpproj_path == None
    assert fd.path_info.temp_path == Path(
        norm_path, DEFAULTS.temporary_folder_name)

    assert fd.slide_info.to_process_i == test_slides_i
    assert fd.slide_info.to_process_paths.sort() == sorted_test_slides


def test_file_data_no_info(norm_path):
    """When used does not provide any information."""
    with pytest.raises(UserInputError):
        _ = FileData(norm_path=norm_path)


def test_file_data_no_svs_no_qupath(norm_path, test_slides_names, test_slides_i):
    """When svs path and qpproj path are not provided."""
    with pytest.raises(UserInputError):
        _ = FileData(norm_path=norm_path,
                     slides_indexes=test_slides_i,
                     slide_names=test_slides_names,
                     rewrite=True)


def test_file_data_wrong_index(norm_path, test_slides_names, test_slides_i, qupath_project):
    """Wrong indexes passed to FileData."""
    wrong_i = test_slides_i[:]
    wrong_i.append(len(test_slides_i) + 1)
    with pytest.raises(UserInputError):
        _ = FileData(norm_path=norm_path,
                     slides_indexes=wrong_i,
                     slide_names=test_slides_names,
                     qpproj_path=qupath_project.path)


def test_file_index_name(norm_path, test_slides_names, qupath_project, test_slides_i, test_slides):
    """When index 0 and name 1."""
    fd = FileData(norm_path=norm_path,
                  slides_indexes=[0],
                  slide_names=test_slides_names[1],
                  qpproj_path=qupath_project.path,
                  rewrite=True)
    assert fd.slide_info.to_process_i == test_slides_i
    if platform.system() != "Windows":
        assert fd.slide_info.to_process_paths == test_slides
    # inconsistent full path names on Windows- use only file names for now..
    else:
        paths_x = [path.name for path in fd.slide_info.to_process_paths]
        paths_y = [path.name for path in test_slides]
        assert paths_x == paths_y


def test_file_no_extension(norm_path, qupath_project, test_slides_i, test_slides):
    """When index 0 and name 1 without extension."""
    fd = FileData(norm_path=norm_path,
                  slides_indexes=[0],
                  slide_names=test_slides[1].stem,
                  qpproj_path=qupath_project.path,
                  rewrite=True)
    assert fd.slide_info.to_process_i == test_slides_i
    if platform.system() != "Windows":
        assert fd.slide_info.to_process_paths == test_slides
    # inconsistent full path names on Windows- use only file names for now..
    else:
        paths_x = [path.name for path in fd.slide_info.to_process_paths]
        paths_y = [path.name for path in test_slides]
        assert paths_x == paths_y
