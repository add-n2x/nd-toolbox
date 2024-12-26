"""
This module provides functionality to process duplicate media files.
"""

import json
import os
import sys
import unicodedata

from dotenv import find_dotenv, load_dotenv

from ndtools.model import MediaFile
from ndtools.db import NavidromeDb
from ndtools.utils import DotDict, PrintUtils as PU


class DuplicateProcessor:
    """
    This class processes duplicate media files.

    Attributes:
        db (NavidromeDb): The database connection to interact with the Navidrome database.
        dups_input (dict): A dictionary containing the raw duplicate media files references from Beets.
        media_files (dict): A dictionary containing the enhanced duplicate media files with data from Navidrome.
        stats (DotDict): A dictionary containing statistics about the processing of duplicate media files.
        output_folder (str): The path to the output folder where processed files will be saved.
    """

    DUPLICATES_INPUT_FILE = "beets-duplicates.json"

    db: NavidromeDb
    dups_input: dict
    dups_media_files: dict
    stats: DotDict
    errors: list
    output_folder: str

    def __init__(self, db: NavidromeDb, output_folder: str):
        """
        Initialize the DuplicateProcessor with a database and an input file containing duplicate media files.

        The input JSON file with media references is generated by the Beets `duplicatez` plugin.

        Args:
            db (NavidromeDb): The Navidrome data access object.
            output_folder (str): Path to the output folder where processed files are saved.
        """
        self.output_folder = output_folder
        self.db = db

        # Path to JSON file generated by the Beets `duplicatez` plugin.
        input_file_path = output_folder + "/" + DuplicateProcessor.DUPLICATES_INPUT_FILE
        # Read the input JSON file containing duplicate media files references from Beets.
        with open(input_file_path, "r", encoding="utf-8") as file:
            self.dups_input = json.load(file)
        if not self.dups_input:
            PU.red(f"No duplicates found in input file '{input_file_path}'")
            sys.exit(1)

        # Init media file duplicates dictionary for holding processing output.
        self.dups_media_files = {}

        # Init logging objects.
        self.errors = []
        self.stats = DotDict({"duplicate_records": 0, "duplicate_files": 0, "media_files": 0, "file_annotations": 0})

    def replace_base_path(self, source_base: str, target_base: str):
        """
        Replace the music library base location with the actual location.

        This is required since the base paths of files may differ between the Beets and Navidrome library.

        Args:
            source_base (str): Paths in the JSON file are relative to this path.
            target_base (str): The actual location in the Navidrome music library.
        """
        if not source_base or not target_base:
            PU.orange("Skipping base path update")
            return
        if source_base == target_base:
            PU.orange("Skipping base path update as target equals source")
            return

        for paths in self.dups_input.values():
            for i, item in enumerate(paths):
                paths[i] = item.replace(source_base, target_base, 1)
        PU.green(f"Updated all base paths from '{source_base}' to '{target_base}'")

    def query_media_data(self):
        """
        Query the Navidrome database for each duplicate file and get all relevant data.
        """
        for key in self.dups_input.keys():
            PU.print("")
            PU.print(f"[*] Processing duplicate {key}")
            files = self.dups_input.get(key)
            self.stats.duplicate_records += 1

            # Initialize the list for this key if it doesn't exist.
            if not self.dups_media_files.get(key):
                self.dups_media_files[key] = []

            for file in files:
                self.stats.duplicate_files += 1
                # Normalize Unicode characters in the file path. Otherwise characters like `á` (`\u0061\u0301`)
                # and `á` (`\u00e1`) are not threaded as the same.
                file = unicodedata.normalize("NFC", file)

                PU.print(f"    Query {file}", l=0)
                media: MediaFile = db.get_media(file)
                self.dups_media_files[key].append(media)
                self._log_info(file, media)
        self._print_stats()
        self._export_errors()

    def _log_info(self, file_path: str, media: MediaFile):
        """
        Log information about the media file.
        """
        if media:
            PU.green(f"└─ {media}", l=1)
            self.stats.media_files += 1
            if media.annotation:
                PU.green(f"└───── {media.annotation}", l=2)
                self.stats.file_annotations += 1
            if media.artist:
                PU.green(f"└───── {media.artist}", l=2)
                if media.artist.annotation:
                    PU.green(f"└───── {media.artist.annotation}", l=3)
            else:
                self.errors.append({"error": "artist not found", "path": file_path, "media": media})
                PU.red("└───── Artist not found in database!", l=2)
            if media.album:
                PU.green(f"└───── {media.album}", l=2)
                if media.album.annotation:
                    PU.green(f"└───── {media.album.annotation}", l=3)
            else:
                # This is not seen as an error because not all media files have an album
                PU.orange("└───── Album not found in database!", l=2)
        else:
            self.errors.append({"error": "media file not found", "path": file_path})
            PU.red("└───── Media file not found in database!", l=1)

    def _print_stats(self):
        PU.print("")
        PU.print("-----------------------------------------------------")
        PU.green(" STATISTICS")
        PU.print("-----------------------------------------------------")
        PU.print("")
        PU.green(" Duplicates:")
        PU.green(f"     Records: {self.stats.duplicate_records}")
        PU.green(f"     Files: {self.stats.duplicate_files}")
        PU.print("")
        PU.green(" Media files:")
        PU.green(f"     Found: {self.stats.media_files}")
        PU.green(f"     Annotations: {self.stats.file_annotations}")
        PU.print("")
        PU.green(f" Artists: {len(self.db.artists)}")
        PU.green(f" Albums: {len(self.db.albums)}")
        PU.print("")

    def _export_errors(self):
        PU.print("-----------------------------------------------------")
        PU.green(" ERRORS")
        PU.print("-----------------------------------------------------")
        if len(self.errors) > 0:
            error_file = self.output_folder + "/errors.json"
            PU.red(f"Exporting {len(self.errors)} errors to {error_file} ...")
            with open(error_file, "w") as f:
                json.dump(self.errors, f, indent=4)
            PU.red("Done!")
        else:
            PU.green(" No errors found.")
        PU.print("-----------------------------------------------------")

    def merge_annotation_data(self, a: MediaFile, b: MediaFile):
        """
        Merge annotation data of two MediaFile objects.
        """
        aa = a.annotation
        ba = b.annotation
        PU.print(f"Merging annotations for {aa} and {ba} ...")

        if aa and ba:
            # Combine play counts
            aa.play_count += int(ba.play_count)
            ba.play_count = aa.play_count
            PU.print(f"Combined play count: {aa.play_count}", 1)
            if aa.play_date > ba.play_date:
                ba.play_date = aa.play_date
            else:
                aa.play_date = ba.play_date
            PU.print(f"Updated play date: {aa.play_date}", 1)

            # Keep the better rating
            if aa.rating and ba.rating:
                if aa.rating > ba.rating:
                    ba.rating = aa.rating
                else:
                    aa.rating = ba.rating
            elif aa.rating and not ba.rating:
                ba.rating = aa.rating
            elif not aa.rating and ba.rating:
                aa.rating = ba.rating
            PU.print(f"Merged rating: {aa.rating}", 1)

            # If one is starred, both are starred
            if aa.starred and not ba.starred:
                ba.starred = True
                ba.starred_at = aa.starred_at
            elif not aa.starred and ba.starred:
                aa.starred = True
                aa.starred_at = ba.starred_at
            PU.print(f"Is starred: {aa.starred}", 1)


if __name__ == "__main__":
    load_dotenv(find_dotenv())

    config_dir = None
    report_dir = None
    music_dir = None
    source_base = None
    target_base = None

    if os.getenv("DIR_CONFIG"):
        config_dir = os.getenv("DIR_CONFIG")
    if os.getenv("DIR_OUTPUT"):
        report_dir = os.getenv("DIR_OUTPUT")
    if os.getenv("DIR_MUSIC"):
        music_dir = os.getenv("DIR_MUSIC")
    if os.getenv("BEETS_BASE_PATH"):
        source_base = os.getenv("BEETS_BASE_PATH")
    if os.getenv("NAVIDROME_BASE_PATH"):
        target_base = os.getenv("NAVIDROME_BASE_PATH")

    db = NavidromeDb(f"{config_dir}/navidrome/navidrome.db")
    processor = DuplicateProcessor(db, report_dir)
    processor.replace_base_path(source_base, target_base)
    processor.query_media_data()
