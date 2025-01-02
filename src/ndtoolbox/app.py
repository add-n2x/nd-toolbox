"""
This module provides functionality to process duplicate media files.
"""

import datetime
import json
import sys
import unicodedata

import jsonpickle
import tomli

from ndtoolbox.db import NavidromeDb
from ndtoolbox.model import MediaFile
from ndtoolbox.utils import CLI, DotDict, ToolboxConfig
from ndtoolbox.utils import PrintUtils as PU


class DuplicateProcessor:
    """
    This class processes duplicate media files.

    Attributes:
        dups_input (dict): A dictionary containing the raw duplicate media files references from Beets.
        media_files (dict): A dictionary containing the enhanced duplicate media files with data from Navidrome.
        stats (DotDict): A dictionary containing statistics about the processing of duplicate media files.
        nd_folder (str): The path to the Navidrome database folder.
        data_folder (str): The path to the data folder where processed files will be saved.
    """

    db: NavidromeDb
    dups_input: dict
    dups_media_files: dict
    stats: DotDict
    errors: list
    nd_folder: str
    data_folder: str
    source_base: str
    target_base: str
    start: float
    stop: float

    def __init__(self, nd_folder: str, data_folder: str, source_base: str, target_base: str):
        """
        Initialize the DuplicateProcessor with a database and an input file containing duplicate media files.

        The input JSON file with media references is generated by the Beets `duplicatez` plugin.

        Args:
            config_folder (str): Path to the configuration folder containing the database file.
            data_folder (str): Path to the data folder where processed files are saved.
            source_base (str): Paths in the JSON file are relative to this path.
            target_base (str): The actual location in the Navidrome music library.
        """
        navidrome_db_path = nd_folder + "/navidrome.db"
        PU.bold("Initializing DuplicateProcessor")
        PU.ln()
        PU.info(f"Navidrome database path: {navidrome_db_path}")
        PU.info(f"Output folder: {data_folder}")
        PU.info(f"Source base: {source_base}")
        PU.info(f"Target base: {target_base}")
        self.db = NavidromeDb(navidrome_db_path)
        self.nd_folder = nd_folder
        self.data_folder = data_folder
        self.source_base = source_base
        self.target_base = target_base
        self.start = 0.0
        self.stop = 0.0

        # Path to JSON file generated by the Beets `duplicatez` plugin.
        beets_input_file = data_folder + "/beets/beets-duplicates.json"
        PU.info(f"Reading duplicates from Beets JSON file: {beets_input_file}")
        # Read the input JSON file containing duplicate media files references from Beets.
        with open(beets_input_file, "r", encoding="utf-8") as file:
            self.dups_input = json.load(file)
        if not self.dups_input:
            PU.error(f"No duplicates found in input file '{beets_input_file}'")
            sys.exit(1)

        # Init media file duplicates dictionary for holding processing data.
        self.dups_media_files = {}

        # Init logging objects.
        self.errors = []
        self.stats = DotDict(
            {
                "duplicate_records": 0,
                "duplicate_files": 0,
                "media_files": 0,
                "file_annotations": 0,
                "media_files_deletable": 0,
            }
        )

    def has_errors(self) -> bool:
        """Check if there are any errors in the processing."""
        return len(self.errors) > 0

    def merge_and_store_annotations(self):
        """
        Merge annotations per duplicate records and store them to the database.
        """
        self._start()
        self._load_navidrome_data()
        PU.bold("Merging and storing annotations for duplicate records")
        PU.ln()
        self._merge_annotation_list()
        self._save_all_annotations()
        self._stop()

    def eval_deletable_duplicates(self):
        """
        Detect deletable duplicate files based on the provided criteria.
        """
        self._start()
        self._load_navidrome_data()
        PU.bold("Evaluating deletable duplicates based on criteria")
        PU.ln()
        for key, dups in self.dups_media_files.items():
            PU.log(f"\nEvaluating {len(dups)} duplicates for: {key}")
            keepable = self._get_keepable_media(dups)
            PU.log(f"\nFound keepable: {keepable}", 0)

        file_path = self.data_folder + "/duplicates-with-keepers.json"
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(jsonpickle.encode(self.dups_media_files, indent=4))
        PU.success(f"Stored deletables and keepers to '{file_path}'")
        self._stop()

    def delete_duplicates(self):
        """
        Delete duplicate files from the Navidrome database and from the file system.
        """
        pass

    def _load_navidrome_data(self):
        """
        Load data from Navidrome database.
        """
        PU.bold("Loading duplicate records from Navidrome database")
        PU.ln()
        self._replace_base_path()
        self._query_media_data()

        # Check for errors before proceeding. If there are errors,
        # ask the user if they want to continue.
        if processor.has_errors():
            PU.error("Errors encountered during processing. Please review the error log.")
            PU.error("Do you want to continue anyway (not recommended)?")
            CLI.ask_continue()

    def _get_keepable_media(self, dups: list[MediaFile]) -> MediaFile:
        """
        Recursively determine which file is keepable based on the criteria.

        The logic to determine which file to keep is as follows, and in that order:

        1. Media file is in an album, which already contains another media file which is keepable.
        2. Media file has one of the preferred file extensions
        3. Media file has a MusicBrainz recording ID.
        4. Media file has an artist record available in the Navidrome database.
        5. Media file contains a album track number.
        6. Media file has a better bit rate than any of the other duplicate media files.
        7. Media file holds a release year.

        Args:
            dups (MediaFile): A list of duplicate media files to evaluate for a keepable.

        Returns:
            MediaFile: The media file to keep.
        """

        # Define the criteria for keepable media
        def is_keepable(this: MediaFile, that: MediaFile) -> MediaFile:
            PU.info(f"Compare {this.path} <=> {that.path}", 0)

            # If the files album already contains a keepable, we wanna keep all the items
            left = this.album and this.album.has_keepable
            right = that.album and that.album.has_keepable
            PU.log(f"Compare if albums contain a keepable: {left} || {right}", 1)
            if left != right:
                if left:
                    return this
                elif right:
                    return that
            # Skip, if they are the same

            # Having a preferred file extension is keepable
            left = this.path.split(".")[-1].lower() in ToolboxConfig.pref_extensions
            right = that.path.split(".")[-1].lower() in ToolboxConfig.pref_extensions
            PU.log(f"Compare if file extension is keepable: {left} || {right}", 1)
            if left != right:
                if left:
                    return this
                elif right:
                    return that
            # Skip, if they are the same

            # Having a MusicBrainz recording ID is keepable
            left = this.mbz_recording_id is not None
            right = that.mbz_recording_id is not None
            PU.log(f"Compare MusicBrainz recording ID: {left} || {right}", 1)
            if left != right:
                if left:
                    return this
                elif right:
                    return that
            # Skip, if they are the same

            # Having artist record in Navidrome is keepable
            left = this.artist is not None
            right = that.artist is not None
            PU.log(f"Artist record available: {left} || {right}", 1)
            if left != right:
                if left:
                    return this
                elif right:
                    return that
            # Skip, if they are the same

            # Having track numbers is keepable
            left = this.track_number > 0
            right = that.track_number > 0
            PU.log(f"Compare track numbers: {left} || {right}", 1)
            if left != right:
                if left:
                    return this
                elif right:
                    return that
            # Skip, if they are the same

            # Higher bitrate is keepable
            left = this.bitrate
            right = that.bitrate
            PU.log(f"Compare bitrate: {left} || {right}", 1)
            if left > right:
                return this
            elif left < right:
                return that
            # Skip, if they are the same

            # Year info is keepable
            left = this.year and this.year > 0
            right = that.year and this.year > 0
            PU.log(f"Compare year info: {left} || {right}", 1)
            if left != right:
                if left:
                    return this
                elif right:
                    return that
            # Skip, if they are the same

            # If no conditition matches, it doesn't matter which one we take
            PU.warning("No condition matched, keeping the other one (that)")
            self.errors.append({"warning": "No condition matched, keeping 'that'", "this": this, "that": that})
            return that

        # Keepable if there is only one duplicate
        if len(dups) == 1:
            # Mark related album as having a keepable duplicate
            if dups[0].album is not None:
                dups[0].album.has_keepable = True
            return dups[0]
        else:
            # Get the last item of the dups list:
            this = dups[-1]
            that = dups[-2]
            keepable = is_keepable(this, that)
            removed: MediaFile = None

            child_dups: list[MediaFile] = dups[:-2]
            if keepable == this:
                child_dups.append(this)
                removed = that
            else:
                child_dups.append(that)
                removed = this

            removed.deletable = True
            self.stats.media_files_deletable += 1
            PU.log(f"\nDeletable: {removed}", 1)
            return self._get_keepable_media(child_dups)

    def _replace_base_path(self):
        """
        Replace the music library base location with the actual location.

        This is required since the base paths of files may differ between the Beets and Navidrome library.
        """
        if not self.source_base or not self.target_base:
            PU.warning("Skipping base path update, since no paths are set")
            return
        if self.source_base == self.target_base:
            PU.warning("Skipping base path update as target equals source")
            return

        for paths in self.dups_input.values():
            for i, item in enumerate(paths):
                paths[i] = item.replace(self.source_base, self.target_base, 1)
        PU.info(f"Updated all base paths from '{self.source_base}' to '{self.target_base}'.")

    def _query_media_data(self):
        """
        Query the Navidrome database for each duplicate file and get all relevant data.
        """
        PU.info("Loading data from Navidrome database ", end="")
        for key in self.dups_input.keys():
            PU.info(f"[*] Processing duplicate {key}")
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

                PU.log(f"    Query {file}")
                media: MediaFile = self.db.get_media(file)
                self.dups_media_files[key].append(media)
                self._log_info(file, media)
        PU.success("> Done.")

    def _merge_annotation_list(self):
        """
        Merge data of all media file annotations referred to as duplicates.
        """
        dups: list[MediaFile]
        for key, dups in self.dups_media_files.items():
            title = dups[0].title
            if dups[0].artist:
                title = f"{dups[0].artist.name} - {title}"

            PU.info(f"Merging {len(dups)} duplicates of '{title}' ", 0, False, end="")
            PU.log(f"Merging {key} : {title} with {len(dups)} duplicates...")
            if len(dups) < 2:
                PU.warning("> No duplicates to be merged. Skipping.", 1)
                continue
            for dup in dups[1 : len(dups)]:
                self._merge_annotation_data(dups[0], dup)
            PU.success("> Merged successfully.")

    def _merge_annotation_data(self, a: MediaFile, b: MediaFile):
        """
        Merge annotation data of two MediaFile objects.
        """
        aa = a.annotation
        ba = b.annotation
        PU.log(f"Merging annotations for {aa} and {ba} ...")

        if aa and ba:
            # Combine play counts
            aa.play_count += int(ba.play_count)
            ba.play_count = aa.play_count
            PU.log(f"Combined play count: {aa.play_count}", 1)
            if aa.play_date and ba.play_date:
                if aa.play_date > ba.play_date:
                    ba.play_date = aa.play_date
                else:
                    aa.play_date = ba.play_date
            PU.log(f"Updated play date: {aa.play_date}", 1)

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
            PU.log(f"Merged rating: {aa.rating}", 1)

            # If one is starred, both are starred
            if aa.starred and not ba.starred:
                ba.starred = True
                ba.starred_at = aa.starred_at
            elif not aa.starred and ba.starred:
                aa.starred = True
                aa.starred_at = ba.starred_at
            PU.log(f"Is starred: {aa.starred}", 1)

    def _save_all_annotations(self):
        """
        Save all annotations of all media file duplicates to the database.
        """
        for _, dups in self.dups_media_files.items():
            for media in dups:
                self.db.store_annotation(media.annotation)

    def _log_info(self, file_path: str, media: MediaFile):
        """
        Log information about the media file.
        """
        if media:
            PU.info(f"└─ {media.path}", 1)
            self.stats.media_files += 1
            if media.annotation:
                PU.log(f"└───── {media.annotation}", 2)
                self.stats.file_annotations += 1
            if media.artist:
                PU.log(f"└───── {media.artist}", 2)
                if media.artist.annotation:
                    PU.log(f"└───── {media.artist.annotation}", 3)
            else:
                aid = media.album_id if media.album_id else ""
                PU.warning(f"└───── Artist '{media.artist_name}' not found in database!", 2)
            if media.album:
                PU.log(f"└───── {media.album}", 2)
                if media.album.annotation:
                    PU.log(f"└───── {media.album.annotation}", 3)
            else:
                # This is not seen as an error because not all media files have an album
                aid = media.album_id if media.album_id else ""
                PU.warning(f"└───── Album '{media.album_name}' not found in database!", 2)
        else:
            self.errors.append({"error": "media file not found", "path": file_path})
            PU.error(f"└───── Media file for '{file_path}' not found in database!", 1)

    def print_stats(self):
        """Print statistics about the processing."""
        if len(self.errors) > 0:
            self.export_errors()
        else:
            PU.bold("\nSTATS")
            PU.ln()
            PU.info("Duplicates:", 0)
            PU.info(f"Records: {self.stats.duplicate_records}", 1)
            PU.info(f"Files: {self.stats.duplicate_files}", 1)
            PU.info(f"Artists: {len(self.db.artists)}", 1)
            PU.info(f"Albums: {len(self.db.albums)}", 1)
            PU.info("")
            PU.info("Media files:", 0)
            PU.info(f"Found: {self.stats.media_files}", 1)
            PU.info(f"Annotations: {self.stats.file_annotations}", 1)
            PU.info(f"Deletables: {self.stats.media_files_deletable}", 1)
            PU.ln()
            PU.success("No errors found.")
            PU.success(f"Finished in {self._get_duration()} seconds")

    def export_errors(self):
        """Export errors to a JSON file."""
        PU.bold("\nERRORS")
        PU.ln()
        error_file = self.data_folder + "/errors.json"
        PU.error(f"Exporting {len(self.errors)} errors to {error_file} ... ", end="")
        with open(error_file, "w") as f:
            json.dump(self.errors, f, indent=4)
        PU.error("Done!")

    def _start(self):
        """Start the operation."""
        self.start = datetime.datetime.now().timestamp()

    def _stop(self):
        """Stop the operation."""
        self.stop = datetime.datetime.now().timestamp()

    def _get_duration(self) -> float:
        """Get the duration of the operation in seconds."""
        return round(self.stop - self.start, 2)


if __name__ == "__main__":
    config = ToolboxConfig()
    with open("pyproject.toml", mode="rb") as file:
        data = tomli.load(file)
        version = data["tool"]["poetry"]["version"]
        PU.ln()
        PU.bold(f"  NAVIDROME TOOLBOX v{version}")
        PU.ln()

    # Read the action argument from the command line
    action = sys.argv[1] if len(sys.argv) > 1 else None
    action = action.split("action=")[1]

    processor = DuplicateProcessor(config.nd_dir, config.data_dir, config.source_base, config.target_base)

    if action == "merge-annotations":
        processor.merge_and_store_annotations()
        processor.print_stats()
        # processor.export_errors()
    elif action == "eval-deletable":
        processor.eval_deletable_duplicates()
        processor.print_stats()
        # processor.export_errors()
    elif action == "delete-duplicates":
        processor.delete_duplicates()
    else:
        PU.error(f"{action}: Invalid action specified")
