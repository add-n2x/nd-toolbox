"""
Beets Duplicatez Plugin.

Extension of the official Beets Duplicates Plugin.

In addition to listing duplicate tracks, the plugin will also output a JSON file with the duplicate information.
This can be useful for further analysis or integration with other systems.
"""

import json

import beets
from beets.library import Item

from beetsplug.duplicates import DuplicatesPlugin


class DuplicatezPlugin(DuplicatesPlugin):
    """List duplicate tracks or albums, additional JSON file output."""

    _dupz: dict[Item]
    _file: str
    _count_tracks: int
    _count_dups: int

    def __init__(self):
        """Initialize plugin."""
        super().__init__()
        self._command.name = "duplicatez"
        self._command.help = __doc__
        self._command.aliases = ["dupz"]
        self._dupz = {}
        self._count_tracks = 0
        self._count_dups = 0
        self._file = "./output/beets-duplicates.json"

        # Purposely reuse 'duplicates' config
        self.config = beets.config["duplicates"]

    def commands(self) -> list:
        """Wrap the parent method and call JSON rendering."""
        super().commands()
        inner_func = self._command.func

        def wrapper_func(lib, opts, args):
            inner_func(lib, opts, args)
            self._render_json()

        self._command.func = wrapper_func
        return [self._command]

    def _process_item(self, item: Item, copy=False, move=False, delete=False, tag=False, fmt=""):
        """Wraps the parent method and creates an additional duplicates dict."""
        super()._process_item(item, copy, move, delete, tag, fmt)
        key = item.get("mb_trackid")
        key_format = "$mb_trackid:$mb_albumid"
        key = format(item, key_format)
        self._dupz.setdefault(key, [])
        dup = str(format(item, "$path"))
        self._dupz.get(key).append(dup)
        self._count_dups += 1

    def _render_json(self):
        """Renders the JSON file."""
        self._count_tracks = len(self._dupz.keys())
        with open(self._file, "w", encoding="utf-8") as file:
            json.dump(self._dupz, file, indent=4, ensure_ascii=False)
        print("---")
        print(f"Found {self._count_tracks} tracks with {self._count_dups} duplicates")
        print(f"Stored to '{self._file}'")
