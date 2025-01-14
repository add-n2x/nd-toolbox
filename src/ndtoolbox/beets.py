"""Classes for interaction with Beets."""

import subprocess
from typing import Generator

from easydict import EasyDict

from ndtoolbox.utils import PrintUtil as PU
from ndtoolbox.utils import StringUtil as SU


class BeetsClient:
    """Client wrapping commands for Beets."""

    @staticmethod
    def get_album_info(album_path) -> Generator[EasyDict]:
        """
        Get album information based on given folder.

        Args:
            album_path (str): The path to the album folder to check.

        Returns:
            (Generator[EasyDict]): list of album info dict containing `album` name, `total` tracks and `missing` tracks.
                Usually it only returns one record, but can return multiple records when the folder contains
                files from multiple albums. In that case, it will be treated as a manual compilation (mixtape).
        """
        album_info = EasyDict({"album": None, "total": None, "missing": None})
        cmd = f"beet ls -a -f '$album:::$albumtotal:::$missing:::$comp' path:\"{album_path}\""
        PU.debug(f"BEET CMD: {cmd}")

        try:
            result = subprocess.check_output(cmd, shell=True, text=True)
            PU.debug(SU.pink(f"BEET RESULT: {result}"))

            if result:
                lines = result.splitlines()
                for line in lines:
                    result = line.split(":::")
                    if len(result) != 4:
                        msg = f"Unexpected result format while getting album info for '{album_path}': {result}"
                        PU.error(msg)
                        return None

                    album_info.album = result[0]
                    album_info.total = int(result[1])
                    album_info.missing = int(result[2])
                    album_info.compilation = bool(result[3])
                    yield album_info
            else:
                PU.warning("Got no result from missing files check!")
        except ValueError as ve:
            PU.error("Error occurred while checking for missing files:" + str(ve))
        except Exception as e:
            PU.error("Unknown error occurred while checking for missing files:" + str(e))
        return None
