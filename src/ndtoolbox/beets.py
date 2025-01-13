"""Classes for interaction with Beets."""

import subprocess

from easydict import EasyDict

from ndtoolbox.utils import PrintUtil as PU
from ndtoolbox.utils import StringUtil as SU


class BeetsClient:
    """Client wrapping commands for Beets."""

    @staticmethod
    def get_album_info(album_path) -> EasyDict:
        """Get album information based on given folder.

        Args:
            album_path (str): The path to the album folder to check.

        Returns:
            EasyDict: Album information containing `album` name, `total` tracks and `missing` tracks.
        """
        album_info = EasyDict({"album": None, "total": None, "missing": None})
        cmd = f"beet ls -a -f '$album:::$albumtotal:::$missing' path:\"{album_path}\""
        PU.info(f"BEET CMD: {cmd}")

        try:
            result = subprocess.check_output(cmd, shell=True, text=True)
            PU.info(SU.pink(f"BEET RESULT: {result}"))

            if result:
                lines = result.splitlines()
                if len(lines) > 1:
                    msg = f"Got too many lines while getting album info for '{album_path}': {result}"
                    PU.error(msg)
                for line in lines:
                    result = line.split(":::")
                    if len(result) != 3:
                        msg = f"Unexpected result format while getting album info for '{album_path}': {result}"
                        PU.error(msg)
                        return None

                    album_info.album = result[0]
                    album_info.total = int(result[1])
                    album_info.missing = int(result[2])
                    return album_info
            else:
                PU.warning("Got no result from missing files check!")
        except ValueError as ve:
            PU.error("Error occurred while checking for missing files:" + str(ve))
        except Exception as e:
            PU.error("Unknown error occurred while checking for missing files:" + str(e))
        return None
