"""
This module provides functionality to process duplicate media files.
"""

import json
import os
import sys
import unicodedata
from datetime import datetime

import jsonpickle
from easydict import EasyDict

from ndtoolbox.db import NavidromeDb, NavidromeDbConnection
from ndtoolbox.model import Annotation, MediaFile
from ndtoolbox.utils import CLI, FileTools, FileUtil, Stats, ToolboxConfig
from ndtoolbox.utils import PrintUtil as PU
from ndtoolbox.utils import StringUtil as SU


class DuplicateProcessor:
    """
    This class processes duplicate media files.

    Attributes:
        db (NavidromeDb): The Navidrome database DAO.
        dups_media_files (dict): A dictionary containing the enhanced duplicate media files with data from Navidrome.
        stats (Stats): Contains statistics about the processing of duplicate media files.
        errors (list): A list to store any errors encountered during processing.
        data_folder (str): The path to the data folder where processed files will be saved.
        source_base (str): The base path for source media files in Beets.
        target_base (str): The base path for target media files in Navidrome.
        start (float): The timestamp when processing started.
        stop (float): The timestamp when processing stopped. This is set at the end of an action or an error occurs.
    """

    config: ToolboxConfig
    db: NavidromeDb
    dups_media_files: dict
    stats: Stats
    errors: list

    def __init__(self, config: ToolboxConfig):
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
        self.config = config
        self.errors = []
        self.db = NavidromeDb(config.navidrome_db_path)
        self.stats = Stats(self.db)
        self.dups_media_files = {}

    def merge_and_store_annotations(self):
        """
        Merge annotations per duplicate records and store them to the database.
        """
        self._load_navidrome_data_file()
        self.stats.start()
        progress_total = self.stats.duplicate_files
        PU.bold("\nMerging and storing annotations for duplicate records")
        PU.ln()

        n: int = 0
        # progress_total = len(dups)

        with NavidromeDbConnection() as conn:
            for _, dups in self.dups_media_files.items():
                # Skip, if there are no duplicates left
                if len(dups) == 0:
                    PU.warning("No duplicate media files found for key '{key}'. Skipping unexpected scenario.")
                    continue
                elif len(dups) == 1:
                    PU.log(f"There is only one media file in the duplicates list: {dups[0].path}")
                    continue

                # Merge annotations and store them to the database.
                self._merge_annotation_list(dups)
                for media in dups:
                    self.db.store_annotation(media.annotation, conn)
                    n += 1
                PU.progress_bar(n, progress_total)
        PU.progress_done(progress_total)
        PU.success(f"> Successfully updated annotations for {n} media files in the Navidrome database.")
        self.stats.stop()
        self.stats.print_duration()

    def eval_deletable_duplicates(self):
        """
        Detect deletable duplicate files based on the provided criteria.
        """
        self.stats.start()
        self._load_navidrome_data_file()
        PU.bold("Evaluating deletable duplicates based on criteria")
        PU.ln()
        for _, dups in self.dups_media_files.items():
            PU.log(f"\n-> Evaluating {len(dups)} duplicates:")
            keepable = self._get_keepable_media(dups)
            PU.log(f"<- Found keepable: {keepable.path}", 0)

        file_path = os.path.join(self.config.data_folder, "duplicates-with-keepers.json")
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(jsonpickle.encode(self.dups_media_files, indent=4))

        # Print the list of deletable and keepable duplicates per album
        dup_folders = self._split_duplicates_by_album_folder(self.dups_media_files)
        PU.info("List duplicates per album folder:")
        PU.ln()
        for folder, dups in dup_folders.items():
            PU.info(f"\n{FileUtil.get_folder(dups[0].path)} " + SU.bold(f"[Album: {dups[0].album_name}]"))
            for dup in dups:
                file = FileUtil.get_file(dup.path)
                if dup.is_deletable is True:
                    msg = SU.red(f"- DELETE > {file} ".ljust(42, " ")) + " - " + SU.pink(f"{dup.delete_reason}")
                else:
                    msg = SU.green(f"- KEEP   > {file}")
                PU.info(msg, 1)

        PU.ln()
        PU.info(f"Files to keep: {self.stats.media_files_keepable}")
        PU.info(SU.underline(f"Files to delete: {self.stats.media_files_deletable}".ljust(40, " ")))
        PU.info(SU.underline(f"Total media files: {self.stats.media_files}".ljust(40, " ")))
        if self._has_errors():
            PU.error(f"Found {len(self.errors)} errors")
        PU.success(f"Stored deletables and keepers to '{file_path}'")
        self.stats.stop()
        self.stats.print_duration()

    def delete_duplicates(self):
        """
        Delete duplicate files from the Navidrome database and from the file system.
        """
        pass

    def load_navidrome_database(self):
        """
        Load data from Navidrome database based on duplicate records generated by Beets.

        The result is stored in a JSON file for fast, further processing.
        """
        self.stats.start()
        PU.bold("\nLoading duplicate records from Navidrome database")
        PU.ln()

        # Read raw duplicates info generated by the Beets `duplicatez` plugin.
        PU.info(f"Reading duplicates from Beets JSON file: {self.config.FILE_BEETS_INPUT_JSON}")
        # Read the input JSON file containing duplicate media files references from Beets.
        with open(self.config.FILE_BEETS_INPUT_JSON, "r", encoding="utf-8") as file:
            dups_input = json.load(file)
        if not dups_input:
            PU.error(f"No duplicates found in input file '{self.config.FILE_BEETS_INPUT_JSON}'")
            PU.info("Please generate the duplicates info using Beets `duplicatez` plugin first.")
            sys.exit(1)

        # Check for existing data file.
        if os.path.isfile(self.config.FILE_TOOLBOX_DATA_JSON):
            PU.note(f"Data file '{self.config.FILE_TOOLBOX_DATA_JSON}' existing already.")
            PU.note("Do you want to continue anyway and overwrite existing data?")
            CLI.ask_continue()

        # Load data.
        self._replace_base_path(dups_input)
        self._query_media_data(dups_input)

        # Persist data.
        data = {"dups_media_files": self.dups_media_files, "stats": self.stats}
        with open(self.config.FILE_TOOLBOX_DATA_JSON, "w", encoding="utf-8") as file:
            file.write(jsonpickle.encode(data, indent=4, keys=True))
        PU.success(f"Stored Navidrome data to '{self.config.FILE_TOOLBOX_DATA_JSON}'")
        self.stats.stop()
        self.stats.print_stats()
        if self._has_errors():
            PU.error(f"Please review {len(self.errors)} errors in {self.config.ERROR_REPORT_JSON} ... ")
            with open(self.config.ERROR_REPORT_JSON, "w") as f:
                json.dump(self.errors, f, indent=4)
        else:
            PU.success("No errors found.")
        self.stats.print_duration()

    def _load_navidrome_data_file(self):
        """
        Load data from a previously saved JSON file.
        """
        # Check for existing errors file.
        if os.path.isfile(self.config.ERROR_REPORT_JSON):
            PU.error(f"Errors file '{self.config.ERROR_REPORT_JSON}' found.")
            PU.note("Have you checked the errors and decided to continue anyway?")
            CLI.ask_continue()

        PU.bold("Loading duplicate records from JSON file")
        PU.ln()
        # Load data from JSON file.
        with open(self.config.FILE_TOOLBOX_DATA_JSON, "r", encoding="utf-8") as file:
            data = jsonpickle.decode(file.read())
            self.dups_media_files = data["dups_media_files"]
            self.stats = data["stats"]
            PU.success(f"Loaded duplicate records from '{self.config.FILE_TOOLBOX_DATA_JSON}'")

    def _split_duplicates_by_album_folder(
        self, dups_media_files: dict[str, list[MediaFile]]
    ) -> dict[str, list[MediaFile]]:
        """
        Split duplicates from different MusicBrainz albums, since they are not seen as duplicates.
        """
        PU.bold("Split duplicates by album")
        PU.ln()
        # Initialize dictionary to hold duplicates grouped by album ID or MusicBrainz album ID.
        album_dups: dict[str, list[MediaFile]] = EasyDict({})
        for _, dups in dups_media_files.items():
            dup: MediaFile
            for dup in dups:
                album_folder = FileUtil.get_folder(dup.path)
                if not album_dups.get(album_folder):
                    album_dups[album_folder] = []

                album_dups[album_folder].append(dup)

        PU.note(f"Organized duplicates in {len(album_dups)} albums")
        return album_dups

    def _get_keepable_media(self, dups: list[MediaFile]) -> MediaFile:
        """
        Recursively determine which file is keepable based on the criteria.

        Args:
            dups (MediaFile): A list of duplicate media files to evaluate for a keepable.

        Returns:
            MediaFile: The media file to keep.
        """
        # Keepable if there is only one duplicate
        if len(dups) == 1:
            # Mark related album as having a keepable duplicate
            if dups[0].album is not None:
                dups[0].album.has_keepable = True
                # TODO Mark album folder as having a keepable duplicate
                # dups[0].album_folder.set_keeper(dups[0])
            self.stats.media_files_keepable += 1
            PU.success(f"Chosen keepable: {dups[0].path}")
            return dups[0]
        else:
            # Get the last item of the dups list:
            this = dups[-1]
            that = dups[-2]
            keepable = self.is_keepable(this, that)
            removed: MediaFile = None

            child_dups: list[MediaFile] = dups[:-2]
            if keepable == this:
                child_dups.append(this)
                removed = that
            else:
                child_dups.append(that)
                removed = this

            removed.is_deletable = True
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
        if not self.config.source_base or not self.config.target_base:
            PU.warning("Skipping base path update, since no paths are set")
            return
        if self.config.source_base == self.config.target_base:
            PU.warning("Skipping base path update as target equals source")
            return

        for paths in dups_input.values():
            for i, item in enumerate(paths):
                paths[i] = item.replace(self.config.source_base, self.config.target_base, 1)
        PU.info(f"Updated all base paths from '{self.config.source_base}' to '{self.config.target_base}'.")

    def _query_media_data(self, dups_input: dict[str, list[str]]):
        """
        Query the Navidrome database for each duplicate file and get all relevant data.

        Args:
            dups_input (dict[str, list[str]]): A dictionary where the keys are duplicate identifiers and the values
                are lists of file paths.
        """
        PU.info("Loading data from Navidrome database")
        with NavidromeDbConnection() as conn:
            progress: int = 0
            for key in dups_input.keys():
                PU.log(f"[·] Processing duplicate {key}")
                progress_total = len(dups_input.keys())
                files = dups_input.get(key)
                self.stats.duplicate_records += 1
                self.dups_media_files[key] = []

                for file in files:
                    # Normalize Unicode characters in the file path. Otherwise characters like `á` (`\u0061\u0301`)
                    # and `á` (`\u00e1`) are not threaded as the same.
                    file = unicodedata.normalize("NFC", file)

                batch = list(self.db.get_media_batch(files, conn))
                self.dups_media_files[key] += batch
                self.stats.duplicate_files += len(files)

                PU.progress_bar(progress, progress_total)
                progress += 1

                if len(files) != len(batch):
                    missing_media = [f for f in files if f not in [m.path for m in batch]]
                    for file in missing_media:
                        PU.warning(msg=f"\nExcluding media file not found in Navidrome: {file}")

            PU.progress_done(progress_total)

    def _merge_annotation_list(self, dups: list[MediaFile]):
        """
        Merge data of all media file annotations referred to as duplicates.

        Args:
           dups_media_files (list[MediaFile]): Dictionary of media files grouped by their key.

        """
        # Build title for logging purposes
        title = dups[0].title
        if dups[0].artist:
            title = f"{dups[0].artist.name} - {title}"
        PU.log(f"Merging {len(dups)} duplicates of '{title}' ")

        # Load annotations for all dups
        with NavidromeDbConnection() as conn:
            for dup in dups:
                dup.annotation = self.db.get_media_annotation(dup, Annotation.Type.media_file, conn)
                if not dup.annotation:
                    PU.log(f"No annotation for media file found, creating new one: {dup.path}")
                    dup.annotation = Annotation(dup.id, Annotation.Type.media_file, 0, None, 0, False, None)

            # Get merged annotation data from duplicates.
            (play_count, play_date, rating, starred, starred_at) = self._get_merged_annotation(dups)
            for dup in dups:
                dup.annotation.play_count = play_count
                dup.annotation.play_date = play_date
                dup.annotation.rating = rating
                dup.annotation.starred = starred
                dup.annotation.starred_at = starred_at
            msg = f"> Merged annotations (play_count={play_count}, play_date={play_date}, rating={rating}, starred={starred}, starred_at={starred_at})"
            PU.log(msg)

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
            a: Annotation = dup.annotation

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
        with NavidromeDbConnection() as conn:
            for _, dups in dups_media_files.items():
                for media in dups:
                    self.db.store_annotation(media.annotation, conn)
            conn.commit()

    def _has_errors(self) -> bool:
        """Check if there are any errors in the processing."""
        return len(self.errors) > 0

    def is_keepable(self, this: MediaFile, that: MediaFile) -> MediaFile:
        """
        Compare two MediaFile objects and determine which one to keep.

        The logic to determine which file to keep is as follows, and in that order:

        1. Media file is in an album, which already contains another media file which is keepable.
        1. Media files have equal filenames, but one has a numeric suffix, e.g., "song.mp3" and "song1.mp3".
           The one with the numeric suffix is considered less important and will be removed.
        1. Media file title and filename are compared with fuzzy search. Higher ratio is a keeper.
        1. Media file has one of the preferred file extensions
        1. Media file has a MusicBrainz recording ID.
        1. Media file has an artist record available in the Navidrome database.
        1. Media file has an album record available in the Navidrome database.
        1. Media file contains a album track number.
        1. Media file has a better bit rate than any of the other duplicate media files.
        1. Media file holds a release year.

        """
        PU.note(f"Compare {SU.gray(this.path)} <=> {SU.gray(that.path)}", 0)

        # INFO: Check for same album but different folders
        left = FileUtil.get_folder(this.path)
        right = FileUtil.get_folder(that.path)
        PU.info(
            f"Same album folder: {FileUtil.get_album_folder(this.path)} || {FileUtil.get_album_folder(that.path)}",
            1,
        )
        if left != right:
            self.errors.append(
                {"error": "Album is spread across different folders", "file1": this.path, "file2": that.path}
            )
            PU.error(f"Album is in different folder: {SU.gray(this.path)} != {SU.gray(that.path)}", 1)
        # Move on since this is just debugging info

        # If the files album already contains a keepable, we wanna keep all the items
        left = this.album and this.album.has_keepable
        right = that.album and that.album.has_keepable
        PU.info(f"Compare if album contain a keepable: {left} || {right}", 1)
        if left != right:
            if left:
                that.delete_reason = f"Other album already contains a keepable | {SU.gray(this.path)}"
                return this
            elif right:
                this.delete_reason = f"Other album already contains a keepable | {SU.gray(that.path)}"
                return that
        # Skip, if they are the same

        # If file paths are equal, except one contains a numeric suffix, keep the other
        left = FileUtil.equal_file_with_numeric_suffix(this.path, that.path)
        right = FileUtil.equal_file_with_numeric_suffix(that.path, this.path)
        PU.info(f"Compare paths with numeric suffix: {right} || {left}", 1)
        if left or right:
            if left:
                that.delete_reason = f"File has a numeric suffix (seems to be a copy) | {SU.gray(this.path)}"
                return this
            elif right:
                this.delete_reason = f"File has a numeric suffix (seems to be a copy) | {SU.gray(that.path)}"
                return that
        # Skip, if none is a suffixed path

        # Having a preferred file extension is keepable
        left = this.path.split(".")[-1].lower() in ToolboxConfig.pref_extensions
        right = that.path.split(".")[-1].lower() in ToolboxConfig.pref_extensions
        PU.info(f"Compare if file extension is keepable: {left} || {right}", 1)
        if left != right:
            if left:
                that.delete_reason = f"Other file has a preferred extension | {SU.gray(this.path)}"
                return this
            elif right:
                this.delete_reason = f"Other file has a preferred extension | {SU.gray(that.path)}"
                return that
        # Skip, if they are the same

        # Having a MusicBrainz recording ID is keepable
        left = this.mbz_recording_id is not None
        right = that.mbz_recording_id is not None
        PU.info(f"Compare MusicBrainz recording ID: {left} || {right}", 1)
        if left != right:
            if left:
                that.delete_reason = f"Other file has a MusicBrainz recording ID | {SU.gray(this.path)}"
                return this
            elif right:
                this.delete_reason = f"Other file has a MusicBrainz recording ID | {SU.gray(that.path)}"
                return that
        # Skip, if they are the same

        # Having artist record in Navidrome is keepable
        left = this.artist is not None
        right = that.artist is not None
        PU.info(f"Artist record available: {left} || {right}", 1)
        if left != right:
            if left:
                that.delete_reason = f"Other file has an artist record in Navidrome | {SU.gray(this.path)}"
                return this
            elif right:
                this.delete_reason = f"Other file has an artist record in Navidrome | {SU.gray(that.path)}"
                return that
        # Skip, if they are the same

        # Having MusicBrainz album ID in Navidrome is keepable
        left = this.album.mbz_album_id if this.album else None
        right = that.album.mbz_album_id if that.album else None
        PU.info(f"MusicBrainz Album ID available: {left} || {right}", 1)
        if left != right:
            if left:
                that.delete_reason = f"Other file has a MusicBrainz album ID | {SU.gray(this.path)}"
                return this
            elif right:
                this.delete_reason = f"Other file has MusicBrainz album ID  | {SU.gray(that.path)}"
                return that
        # Skip, if they are the same

        # Having track numbers is keepable
        left = this.track_number > 0
        right = that.track_number > 0
        PU.info(f"Compare track numbers: {left} || {right}", 1)
        if left != right:
            if left:
                that.delete_reason = f"Other file has a track number | {SU.gray(this.path)}"
                return this
            elif right:
                this.delete_reason = f"Other file has a track number | {SU.gray(that.path)}"
                return that
        # Skip, if they are the same

        # Higher bitrate is keepable
        left = this.bitrate
        right = that.bitrate
        PU.info(f"Compare bitrate: {left} || {right}", 1)
        if left > right:
            that.delete_reason = f"Other file has a higher bitrate | {SU.gray(this.path)}"
            return this
        elif left < right:
            this.delete_reason = f"Other file has a higher bitrate | {SU.gray(that.path)}"
            return that
        # Skip, if they are the same

        # Year info is keepable
        left = this.year and this.year > 0
        right = that.year and that.year > 0
        PU.info(f"Compare year info: {left} || {right}", 1)
        if left != right:
            if left:
                that.delete_reason = f"Other file has a year info | {SU.gray(this.path)}"
                return this
            elif right:
                this.delete_reason = f"Other file has a year info | {SU.gray(that.path)}"
                return that
        # Skip, if they are the same

        # If the filename is closer to the track title, it is keepable
        left = FileUtil.fuzzy_match_track(this.path, this)
        right = FileUtil.fuzzy_match_track(that.path, that)
        PU.info(f"Fuzzy match filename and track title: {left} || {right}", 1)
        if left != right:
            if left > right:
                that.delete_reason = f"Other file is closer to the track title | {SU.gray(this.path)}"
                return this
            elif right:
                this.delete_reason = f"Other file is closer to the track title | {SU.gray(that.path)}"
                return that
        # Skip, if they are the same

        # If the album folder is closer to the album name, it is keepable
        left = FileUtil.fuzzy_match_album(FileUtil.get_album_folder(this.path), this)
        right = FileUtil.fuzzy_match_album(FileUtil.get_album_folder(that.path), that)
        PU.info(f"Fuzzy match album name: {left} || {right}", 1)
        if left != right:
            if left > right:
                that.delete_reason = f"Other album folder is closer to the album name  | {SU.gray(this.path)}"
                return this
            elif right:
                this.delete_reason = f"Other album folder is closer to the album name  | {SU.gray(that.path)}"
                return that
        # Skip, if they are the same

        # If no conditition matches, it doesn't matter which one we take
        PU.warning(f"No condition matched, keeping this one ({this.path}), instead of that one ({that.path})")
        this.delete_reason = f"No reason, since no condition matched | {SU.gray(that.path)}"
        return that


if __name__ == "__main__":
    config = ToolboxConfig()

    # Read the action argument from the command line
    action = ""
    for arg in sys.argv:
        if arg.startswith("action="):
            action = arg.split("=")[1]
            break
    else:
        PU.error("No action specified. Please use the format 'python app.py action=<action>'.")
        sys.exit(1)

    processor = DuplicateProcessor(config)

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
