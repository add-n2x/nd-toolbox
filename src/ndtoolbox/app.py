"""
This module provides functionality to process duplicate media files.
"""

import json
import os
import sys
import unicodedata
from datetime import datetime

import jsonpickle
import tomli
from easydict import EasyDict

from ndtoolbox.db import NavidromeDb
from ndtoolbox.model import MediaFile
from ndtoolbox.utils import CLI, FileTools, ToolboxConfig
from ndtoolbox.utils import PrintUtils as PU


class DuplicateProcessor:
    """
    This class processes duplicate media files.

    Attributes:
        db (NavidromeDb): The Navidrome database DAO.
        dups_media_files (dict): A dictionary containing the enhanced duplicate media files with data from Navidrome.
        stats (EasyDict): A dictionary containing statistics about the processing of duplicate media files.
        errors (list): A list to store any errors encountered during processing.
        data_folder (str): The path to the data folder where processed files will be saved.
        source_base (str): The base path for source media files in Beets.
        target_base (str): The base path for target media files in Navidrome.
        start (float): The timestamp when processing started.
        stop (float): The timestamp when processing stopped. This is set at the end of an action or an error occurs.
    """

    FILE_BEETS_INPUT_JSON: str
    FILE_TOOLBOX_DATA_JSON: str
    ERROR_REPORT_JSON: str

    db: NavidromeDb
    dups_media_files: dict
    stats: EasyDict
    errors: list

    data_folder: str
    source_base: str
    target_base: str
    start: float
    stop: float

    def __init__(self, navidrome_db_path: str, data_folder: str, source_base: str, target_base: str):
        """
        Initialize the DuplicateProcessor with a database and an input file containing duplicate media files.

        The input JSON file with media references is generated by the Beets `duplicatez` plugin.

        Args:
            navidrome_db_path (str): Path to the Navidrome database file.
            data_folder (str): Path to the data folder where processed files are saved.
            source_base (str): Paths in the JSON file are relative to this path.
            target_base (str): The actual location in the Navidrome music library.
            dry_run (bool): If True, no actual file operations will be performed.
        """
        self.db = NavidromeDb(navidrome_db_path)
        self.data_folder = data_folder
        self.source_base = source_base
        self.target_base = target_base
        self.start = 0.0
        self.stop = 0.0

        # Init file paths.
        self.FILE_BEETS_INPUT_JSON = os.path.join(data_folder, "beets/beets-duplicates.json")
        self.FILE_TOOLBOX_DATA_JSON = os.path.join(self.data_folder, "nd-toolbox-data.json")
        self.ERROR_REPORT_JSON = os.path.join(self.data_folder, "nd-toolbox-error.json")

        # Init media file duplicates dictionary for holding processing data.
        self.dups_media_files = {}

        # Init error and stats objects.
        self.errors = []
        self.stats = EasyDict(
            {
                "duplicate_records": 0,
                "duplicate_files": 0,
                "media_files": 0,
                "file_annotations": 0,
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
        self.load_navidrome_data_file()
        PU.bold("Merging and storing annotations for duplicate records")
        PU.ln()
        self._merge_annotation_list(self.dups_media_files)
        n: int = 0
        for _, dups in self.dups_media_files.items():
            for media in dups:
                self.db.store_annotation(media.annotation)
                n += 1
        PU.success(f"> Successfully updated annotations for {n} media files in the Navidrome database.")
        self._stop()
        PU.success(f"Finished in {self._get_duration()}")

    def eval_deletable_duplicates(self):
        """
        Detect deletable duplicate files based on the provided criteria.
        """
        self._start()
        self.load_navidrome_data_file()
        PU.bold("Evaluating deletable duplicates based on criteria")
        PU.ln()
        for key, dups in self.dups_media_files.items():
            PU.log(f"\nEvaluating {len(dups)} duplicates for: {key}")
            keepable = self._get_keepable_media(dups)
            PU.log(f"\nFound keepable: {keepable}", 0)

        file_path = os.path.join(self.data_folder, "duplicates-with-keepers.json")
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(jsonpickle.encode(self.dups_media_files, indent=4))
        PU.success(f"Stored deletables and keepers to '{file_path}'")
        self._stop()

    def delete_duplicates(self):
        """
        Delete duplicate files from the Navidrome database and from the file system.
        """
        pass

    def load_navidrome_database(self):
        """
        Load data from Navidrome database.
        """
        self._start()
        PU.bold("Loading duplicate records from Navidrome database")
        PU.ln()

        # Read raw duplicates info generated by the Beets `duplicatez` plugin.
        PU.info(f"Reading duplicates from Beets JSON file: {self.FILE_BEETS_INPUT_JSON}")
        # Read the input JSON file containing duplicate media files references from Beets.
        with open(self.FILE_BEETS_INPUT_JSON, "r", encoding="utf-8") as file:
            dups_input = json.load(file)
        if not dups_input:
            PU.error(f"No duplicates found in input file '{self.FILE_BEETS_INPUT_JSON}'")
            PU.info("Please generate the duplicates info using Beets `duplicatez` plugin first.")
            sys.exit(1)

        # Check for existing data file.
        if os.path.isfile(self.FILE_TOOLBOX_DATA_JSON):
            PU.note(f"Data file '{self.FILE_TOOLBOX_DATA_JSON}' existing already.")
            PU.note("Do you want to continue anyway and overwrite existing data?")
            CLI.ask_continue()

        # Load data.
        self._replace_base_path(dups_input)
        self._query_media_data(dups_input)

        # Persist data.
        data = {"dups_media_files": self.dups_media_files, "stats": self.stats}
        with open(self.FILE_TOOLBOX_DATA_JSON, "w", encoding="utf-8") as file:
            file.write(jsonpickle.encode(data, indent=4, keys=True))
        PU.success(f"Stored Navidrome data to '{self.FILE_TOOLBOX_DATA_JSON}'")
        self._stop()
        self._print_stats()

    def load_navidrome_data_file(self):
        """
        Load data from a previously saved JSON file.
        """
        # Check for existing errors file.
        if os.path.isfile(self.ERROR_REPORT_JSON):
            PU.error(f"Errors file '{self.ERROR_REPORT_JSON}' found.")
            PU.note("Have you checked the errors and decided to continue anyway?")
            CLI.ask_continue()

        PU.bold("Loading duplicate records from JSON file")
        PU.ln()
        # Load data from JSON file.
        with open(self.FILE_TOOLBOX_DATA_JSON, "r", encoding="utf-8") as file:
            data = jsonpickle.decode(file.read())
            self.dups_media_files = data["dups_media_files"]
            self.stats = data["stats"]
            PU.success(f"Loaded duplicate records from '{self.FILE_TOOLBOX_DATA_JSON}'")

    def _get_keepable_media(self, dups: list[MediaFile]) -> MediaFile:
        """
        Recursively determine which file is keepable based on the criteria.

        The logic to determine which file to keep is as follows, and in that order:

        1. Media file is in an album, which already contains another media file which is keepable.
        2. Media file has one of the preferred file extensions
        3. Media file has a MusicBrainz recording ID.
        4. Media file has an artist record available in the Navidrome database.
        5. Media file has an album record available in the Navidrome database.
        6. Media file contains a album track number.
        7. Media file has a better bit rate than any of the other duplicate media files.
        8. Media file holds a release year.

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

            # Having album record in Navidrome is keepable
            left = this.album is not None
            right = that.album is not None
            PU.log(f"Album record available: {left} || {right}", 1)
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

    def _replace_base_path(self, dups_input: dict[str, list[MediaFile]]):
        """
        Replace the music library base location with the actual location.

        This is required since the base paths of files may differ between the Beets and Navidrome library.

        Args:
            dups_input (dict[str, list[str]]): A dictionary where the keys are duplicate identifiers and the values
                are lists of file paths.
        """
        if not self.source_base or not self.target_base:
            PU.warning("Skipping base path update, since no paths are set")
            return
        if self.source_base == self.target_base:
            PU.warning("Skipping base path update as target equals source")
            return

        for paths in dups_input.values():
            for i, item in enumerate(paths):
                paths[i] = item.replace(self.source_base, self.target_base, 1)
        PU.info(f"Updated all base paths from '{self.source_base}' to '{self.target_base}'.")

    def _query_media_data(self, dups_input: dict[str, list[str]]):
        """
        Query the Navidrome database for each duplicate file and get all relevant data.

        Args:
            dups_input (dict[str, list[str]]): A dictionary where the keys are duplicate identifiers and the values
                are lists of file paths.
        """
        PU.info("Loading data from Navidrome database ", end="")
        for key in dups_input.keys():
            PU.info(f"[*] Processing duplicate {key}")
            files = dups_input.get(key)
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
                if media:
                    self.dups_media_files[key].append(media)
                self._log_info(file, media)
        PU.success("> Done.")

    def _merge_annotation_list(self, dups_media_files: dict[str, list[MediaFile]]):
        """
        Merge data of all media file annotations referred to as duplicates.

        Args:
           dups_media_files (dict[str, list[MediaFile]]): Dictionary of media files grouped by their key.
        """
        dups: list[MediaFile]
        for key, dups in dups_media_files.items():
            # Skip, if there are no duplicates left
            if not dups or len(dups) <= 1:
                PU.warning("> No duplicate media files found for key '{key}'. Skipping.")
                continue

            # Build title for logging purposes.
            title = dups[0].title
            if dups[0].artist:
                title = f"{dups[0].artist.name} - {title}"

            PU.info(f"Merging {len(dups)} duplicates of '{title}' ", 0, False, end="")
            PU.log(f"Merging {key} : {title} with {len(dups)} duplicates...")
            if len(dups) < 2:
                PU.warning("> No duplicates to be merged. Skipping.", 1)
                continue

            # Get merged annotation data from duplicates.
            (play_count, play_date, rating, starred, starred_at) = self._get_merged_annotation(dups)
            for dup in dups:
                dup.annotation.play_count = play_count
                dup.annotation.play_date = play_date
                dup.annotation.rating = rating
                dup.annotation.starred = starred
                dup.annotation.starred_at = starred_at
            msg = f"> Merged annotations (play_count={play_count}, play_date={play_date}, rating={rating}, starred={starred}, starred_at={starred_at})"
            PU.success(msg)

    def _get_merged_annotation(self, dups: list[MediaFile]) -> tuple[int, datetime, int, bool, datetime]:
        """
        Get merged annotation data from a list of MediaFile objects.

        Args:
            dups (list[MediaFile]): List of duplicate media files.

        Returns:
            tuple[int, datetime, int, bool, datetime]: The merged annotation data.
        """
        play_count: int = 0
        play_date: datetime = None
        rating: int = 0
        starred: bool = False
        starred_at: datetime = None

        for dup in dups:
            a = dup.annotation
            if a.play_count > play_count:
                play_count = a.play_count
            if a.play_date:
                if not play_date:
                    play_date = a.play_date
                elif a.play_date.timestamp() > play_date.timestamp():
                    play_date = a.play_date
            if a.rating > rating:
                rating = a.rating
            if a.starred:
                starred = True
            if a.starred_at:
                if not starred_at:
                    starred_at = a.starred_at
                elif a.starred_at.timestamp() > starred_at.timestamp():
                    starred_at = a.starred_at

        return (play_count, play_date, rating, starred, starred_at)

    def _save_all_annotations(self, dups_media_files: dict[str, list[MediaFile]]):
        """
        Save all annotations of all media file duplicates to the database.
        """
        for _, dups in dups_media_files.items():
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
                PU.warning(f"└───── Album '{media.album_name}' not found in database!", 2)
        else:
            self.errors.append({"error": "media file not found.", "path": file_path})
            PU.error(f"└───── Media file for '{file_path}' not found in database! Exclude from processing.", 1)

    def _print_stats(self):
        """Print statistics about the processing."""
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
        PU.ln()
        if self.has_errors():
            PU.error(f"Please review {len(self.errors)} errors in {self.ERROR_REPORT_JSON} ... ")
            with open(self.ERROR_REPORT_JSON, "w") as f:
                json.dump(self.errors, f, indent=4)
        else:
            PU.success("No errors found.")
        PU.success(f"Finished in {self._get_duration()}")

    def _start(self):
        """Start the operation."""
        self.start = datetime.now().timestamp()

    def _stop(self):
        """Stop the operation."""
        self.stop = datetime.now().timestamp()

    def _get_duration(self) -> float:
        """Get the duration of the operation in seconds."""
        duration = round(self.stop - self.start, 2)
        if duration > 60:
            return f"{round(duration / 60, 2)} minutes"
        else:
            return f"{duration} seconds"


if __name__ == "__main__":
    config = ToolboxConfig()
    with open("pyproject.toml", mode="rb") as file:
        data = tomli.load(file)
        version = data["tool"]["poetry"]["version"]
        PU.ln()
        PU.bold(f"  NAVIDROME TOOLBOX v{version}")
        PU.ln()

    # Read the action argument from the command line
    action = sys.argv[1]
    action = action.split("action=")[1]
    processor = DuplicateProcessor(config.navidrome_db_path, config.data_dir, config.source_base, config.target_base)

    if action == "remove-unsupported":
        FileTools.move_by_extension(config.music_dir, config.data_dir, config.remove_extensions, ToolboxConfig.dry_run)
    elif action == "load-duplicates":
        processor.load_navidrome_database()
    elif action == "merge-annotations":
        processor.merge_and_store_annotations()
    elif action == "eval-deletable":
        processor.eval_deletable_duplicates()
    elif action == "delete-duplicates":
        processor.delete_duplicates()
    else:
        PU.error(f"{action}: Invalid action specified")
