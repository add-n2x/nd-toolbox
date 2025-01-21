"""Classes for interaction with Beets."""

# import os
import subprocess

# from pathlib import Path
from typing import Generator

# import confuse
# from beets.dbcore.query import AndQuery, FieldQuery, OrQuery, SubstringQuery
# from beets.library import Library
from easydict import EasyDict

# from beets.ui import print_
# from beets.util import syspath, displayable_path, normpath
# from ndtoolbox import config
from ndtoolbox.utils import PrintUtil as PU
from ndtoolbox.utils import StringUtil as SU


class BeetsClient:
    """Client wrapping commands for Beets."""

    # lib: Library = None

    # def __init__(self):
    #     """Initialize the Beets client."""
    #     confuse.Path(cwd="config/beets")
    #     libpath = config["beets"]["library"].get(str)
    #     BeetsClient.lib = Library(libpath)
    #     paths_found = []

    # def _query_lib(self, beet_query, message, silent=False):
    #     """beet_query can be string or query object. Returns a list of paths."""
    #     # libpath = os.path.expanduser(Path(SHELLENV["BEETSDIR"]) / "jtbeets_gin.db")
    #     libpath = Config.beets_db_path
    #     lib = Library(libpath)
    #     paths_found = []

    #     for item in lib.items(beet_query):
    #         paths_found += [item.get("path")]
    #     return paths_found

    # def _query1(self):
    #     isrc = ""
    #     beet_result = self._query_lib(SubstringQuery("isrc", isrc), "", silent=True)
    #     return beet_result

    # def _query1(self):
    #     artist = "oasis"
    #     title = "wonderwall"
    #     beet_result = self._query_lib(
    #         AndQuery([SubstringQuery("artist", artist), SubstringQuery("title", title)]),
    #     )
    #     return beet_result

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
        album_info = EasyDict({"album": None, "total": None, "missing": None, "compilation": False})
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
