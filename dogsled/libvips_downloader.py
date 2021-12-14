
'''
when libvips is not installed on Windows (e.g. using conda)
Mostly, for Github's actions
'''
import shutil
import hashlib
import urllib.request
import zipfile
import logging
from pathlib import Path
from typing import Optional

from dogsled.defaults import DEFAULTS
from dogsled.errors import LibVipsError

LOGGER = logging.getLogger(__name__)


class GetLibvips:
    '''
    class for creating the folders, downloading, unzipping..
    '''

    def __init__(self, parent: str = '.'):
        self.libvips_home = self.libvips_folder(parent)
        self.libvips_zip = Path(self.libvips_home,
                                'vips-dev-w64-web-x.xx.x-static.zip')

    @staticmethod
    def md5_gen(file) -> str:
        '''calculates md5 of a file'''
        md5_h = hashlib.md5()
        with open(file, 'rb') as f:
            while True:
                chunk = f.read(1000 * 1000)
                if not chunk:
                    break
                md5_h.update(chunk)
        return md5_h.hexdigest()

    def libvips_folder(self, parent) -> Path:
        '''creates folder where libvips will live'''
        path = Path(parent, 'lib')
        try:
            path.mkdir(exist_ok=False)
        except FileExistsError:
            LOGGER.warning(
                'libvips already downloaded')
        return path

    def download_dlls(self) -> None:
        '''downloads libvips .zip, unpacks, checks md5'''
        LOGGER.info(f'downloading libvips')
        url = DEFAULTS['libvips_url']

        with urllib.request.urlopen(url) as response, open(self.libvips_zip, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
        LOGGER.info(GetLibvips.md5_gen(self.libvips_zip))

        if GetLibvips.md5_gen(self.libvips_zip) != DEFAULTS['libvips_md5']:
            LOGGER.error(
                'libvips md5 does not match md5 of the downloaded file')
            LOGGER.error('exiting')
            self.libvips_zip.unlink()
            raise LibVipsError(
                message=f'was not able to verify libvips defined in DEFAULTS')

    def unzip_vips(self) -> None:
        '''simple unzipper to the libvips folder (lib)'''
        with zipfile.ZipFile(self.libvips_zip, 'r') as vips_packed:
            vips_packed.extractall(self.libvips_home)
        self.libvips_zip.unlink()

    def pathfinder(self) -> Path:
        '''checks for libvips folders in lib
        returns the one with the latest version if several are present
        (e.g. if re-defined in DEFAULTS and downloaded older versions)'''
        vips_folders = [
            str(folder) for folder in self.libvips_home.iterdir() if 'vips' in folder.name]
        vips_folders.sort()
        return Path(vips_folders[-1])

    def get_path(self) -> Path:
        '''
        wrapper function
        which downloads dlls & returns their folder for registring in the PATH
        '''
        try:
            vips_path = self.pathfinder()
        except IndexError:
            self.download_dlls()
            self.unzip_vips()
            vips_path = self.pathfinder()
        LOGGER.info(vips_path)
        return Path(vips_path, 'bin')
