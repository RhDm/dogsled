from pathlib import Path
import logging

from dogsled.libvips_downloader import GetLibvips

LOGGER = logging.getLogger(__name__)


def test_vips_download():
    """Goes through the downloading rutine & checks whether the vips.exe exists."""
    vips_getter = GetLibvips("dogsled/tests/data")
    vips_path = vips_getter.get_path()
    assert Path(vips_path, "vips.exe").exists()
    LOGGER.info(vips_path)
