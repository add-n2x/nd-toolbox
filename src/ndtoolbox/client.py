"""Classes for interaction with Beets."""

import io
import subprocess
import sys
from typing import Generator

from beets.ui import main
from easydict import EasyDict

from ndtoolbox.utils import PrintUtil as PU
from ndtoolbox.utils import StringUtil as SU


class BeetsClient:
    """Client wrapping commands for Beets."""

    query_type: int

    def __init__(self, query_type: int):
        """Initialize BeetsClient."""
        self.query_type = query_type

    def query(self, cmd: list) -> list:
        """Query Beets."""
        results = None
        # Use subprocess query
        if self.query_type == 0:
            cmd = ["beet"] + cmd
            cmd = " ".join(cmd)
            PU.debug(f"Beets query command: {cmd}")
            results = subprocess.check_output(cmd, shell=True, text=True)
            results = results.splitlines()
        # Query by capturing stout
        else:
            base_cmd = ["-c", "config/beets/config.yaml"]
            cmd = base_cmd + cmd
            PU.debug(f"Beets query args: {cmd}")
            captured_output = io.StringIO()
            sys.stdout = captured_output
            main(cmd)
            sys.stdout = sys.__stdout__
            results = captured_output.getvalue()
            captured_output.close()
        return results

    def get_album_info(self, album_path) -> Generator[EasyDict]:
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
        cmd = ["ls", "-a", "-f", "'$album:::$albumtotal:::$missing:::$comp'", f'path:"{album_path}"']

        try:
            lines = self.query(cmd)
            PU.debug(SU.pink(f"Beets result: {lines}"))

            if lines:
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
            PU.error(f"Error occurred while checking for missing files (beets result: {result}), error:" + str(ve))
        except Exception as e:
            PU.error("Unknown error occurred while checking for missing files:" + str(e))
        return None


beets_client = BeetsClient(0)
