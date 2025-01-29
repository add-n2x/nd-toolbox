"""
This module provides functionality to process duplicate media files.
"""

import json
import os
import re
import sys
import unicodedata
from datetime import datetime
from io import StringIO

import jsonpickle
import tomli
from easydict import EasyDict
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

from ndtoolbox.config import config
from ndtoolbox.db import NavidromeDb, NavidromeDbConnection
from ndtoolbox.model import Annotation, Folder, MediaFile
from ndtoolbox.utils import CLI, FileTools, FileUtil, PrintUtil, Stats
from ndtoolbox.utils import PrintUtil as PU
from ndtoolbox.utils import StringUtil as SU


class DataCache:
    """Cache for objects to process duplicates and their relations."""

    artists: dict
    albums: dict
    media: dict
    directories: dict

    def __init__(self, data: dict = None):
        """Init cache."""
        if data is None:
            self.artists = {}
            self.albums = {}
            self.media = {}
            self.directories = Folder.CACHE
        else:
            self.artists = data["artists"]
            self.albums = data["albums"]
            self.media = data["media"]
            self.directories = data["directories"]


class DuplicateProcessor:
    """
    This class processes duplicate media files.

    Attributes:
        db (NavidromeDb): The Navidrome database DAO.
        stats (Stats): Contains statistics about the processing of duplicate media files.
        errors (list): A list to store any errors encountered during processing.
        data_folder (str): The path to the data folder where processed files will be saved.
        base_path_beets (str): The base path for source media files in Beets.
        base_path_navidrome (str): The base path for target media files in Navidrome.
        start (float): The timestamp when processing started.
        stop (float): The timestamp when processing stopped. This is set at the end of an action or an error occurs.
    """

    db: NavidromeDb
    data: DataCache
    stats: Stats
    errors: list

    def __init__(self):
        """
        Initialize the DuplicateProcessor with a database and an input file containing duplicate media files.

        The input JSON file with media references is generated by the Beets `duplicatez` plugin.

        Args:
            navidrome_db_path (str): Path to the Navidrome database file.
            data_folder (str): Path to the data folder where processed files are saved.
            base_path_beets (str): Paths in the JSON file are relative to this path.
            base_path_navidrome (str): The actual location in the Navidrome music library.
            dry_run (bool): If True, no actual file operations will be performed.
        """
        # self.config = config
        self.data = DataCache()
        self.errors = []
        navidrome_db = config["navidrome"]["database"].get(str)
        self.db = NavidromeDb(navidrome_db, self.data)
        self.stats = Stats(self)

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
            for _, dups in self.data.media.items():
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
        self._load_navidrome_data_file()
        self.stats.start()
        PU.bold("Evaluating deletable duplicates based on criteria")
        PU.ln()
        for _, dups in self.data.media.items():
            PU.debug(f"\n-> Evaluating {len(dups)} duplicates:")
            keepable = self._get_keepable_media(dups)
            PU.debug(f"<- Found keepable: {keepable.path}", 0)

        # Build the tree of deletable and keepable duplicates per album
        data = CommentedMap({})
        dup_folders = self._split_duplicates_by_album_folder(self.data.media)
        PU.info("List duplicates per album folder:")
        PU.ln()
        for _, dups in dup_folders.items():
            folder = FileUtil.get_folder(dups[0].path)
            PU.info(f"\n{folder} " + SU.bold(f"[Album: {dups[0].album_name}]"))
            data[folder] = CommentedMap({})
            for dup in dups:
                file = FileUtil.get_file(dup.path)
                if dup.is_deletable is True:
                    data[folder][file] = "DELETE"
                    reason = SU.strip_terminal_colors(dup.delete_reason)
                    data[folder].yaml_add_eol_comment(f"Reason: {reason}", file)
                    msg = SU.red(f"- DELETE > {file} ".ljust(42, " ")) + " - " + SU.pink(f"{dup.delete_reason}")
                else:
                    data[folder][file] = None
                    msg = SU.green(f"- KEEP   > {file}")
                PU.debug(msg, 1)

        # Store commands in yaml file for later execution
        yaml_file = os.path.join(config["data"].get(str), "commands.yaml")
        self._generate_command_yaml(yaml_file)

        # Print stats
        PU.ln()
        PU.info(f"Files to keep: {self.stats.media_files_keepable}")
        PU.info(SU.underline(f"Files to delete: {self.stats.media_files_deletable}".ljust(40, " ")))
        PU.info(SU.underline(f"Total media files: {self.stats.media_files}".ljust(40, " ")))
        if self._has_errors():
            PU.error(f"Found {len(self.errors)} errors")
        PU.success(
            f"Stored delete commands to '{yaml_file}'.\nReview the file and comment out any files you want to keep."
        )
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
        PU.info(f"Reading duplicates from Beets JSON file: {config["FILE_BEETS_INPUT_JSON"].get(str)}")
        # Read the input JSON file containing duplicate media files references from Beets.
        with open(config["FILE_BEETS_INPUT_JSON"].get(str), "r", encoding="utf-8") as file:
            beets_dups = json.load(file)
        if not beets_dups:
            PU.error(f"No duplicates found in input file '{config["FILE_BEETS_INPUT_JSON"].get(str)}'")
            PU.info("Please generate the duplicates info using Beets `duplicatez` plugin first.")
            sys.exit(1)

        # Check for existing data file.
        if os.path.isfile(config["FILE_TOOLBOX_DATA_JSON"].get(str)):
            PU.note(f"Data file '{config["FILE_TOOLBOX_DATA_JSON"].get(str)}' existing already.")
            PU.note("Do you want to continue anyway and overwrite existing data?")
            CLI.ask_continue()

        # Load data.
        mapped_paths = self._build_path_mapping(beets_dups)
        self._query_media_data(mapped_paths)

        # Persist data.
        data = {"stats": self.stats, "cache": self.data}
        with open(config["FILE_TOOLBOX_DATA_JSON"].get(str), "w", encoding="utf-8") as file:
            file.write(jsonpickle.encode(data, indent=4, keys=True))
        PU.success(f"Stored Navidrome data to '{config["FILE_TOOLBOX_DATA_JSON"].get(str)}'")
        self.stats.stop()
        self.stats.print_stats()
        if self._has_errors():
            PU.error(f"Please review {len(self.errors)} errors in {config["ERROR_REPORT_JSON"].get(str)}...")
            with open(config["ERROR_REPORT_JSON"].get(str), "w") as f:
                json.dump(self.errors, f, indent=4)
        else:
            PU.success("No errors found.")
        self.stats.print_duration()

    def _load_navidrome_data_file(self):
        """
        Load data from a previously saved JSON file.
        """
        # Check for existing errors file.
        if os.path.isfile(config["ERROR_REPORT_JSON"].get(str)):
            PU.error(f"Errors file '{config["ERROR_REPORT_JSON"].get(str)}' found.")
            PU.note("Have you checked the errors and decided to continue anyway?")
            CLI.ask_continue()

        PU.bold("Loading duplicate records from JSON file")
        PU.ln()
        # Load data from JSON file.
        with open(config["FILE_TOOLBOX_DATA_JSON"].get(str), "r", encoding="utf-8") as file:
            data = jsonpickle.decode(file.read())
            self.stats = data["stats"]
            self.data = data["cache"]
            PU.success(f"Loaded duplicate records from '{config["FILE_TOOLBOX_DATA_JSON"].get(str)}'")

    def _split_duplicates_by_album_folder(self, duplicates: dict[str, list[MediaFile]]) -> dict[str, list[MediaFile]]:
        """
        Split duplicates from different MusicBrainz albums, since they are not seen as duplicates.
        """
        PU.bold("Split duplicates by album")
        PU.ln()
        # Initialize dictionary to hold duplicates grouped by album ID or MusicBrainz album ID.
        album_dups: dict[str, list[MediaFile]] = EasyDict({})
        for _, dups in duplicates.items():
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
            # if dups[0].album is not None:
            # dups[0].album.has_keepable = True
            # TODO Mark album folder as having a keepable duplicate
            # dups[0].album_folder.set_keeper(dups[0])
            if dups[0].folder is not None:
                dups[0].folder.has_keepable = True
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

    def _build_path_mapping(self, beets_dups: dict[str, list[str]]) -> dict[str, dict]:
        """
        Creates a path mapping between Beets and Navidrome paths.

        Args:
            mapped_dups: The duplicates with path mapping.
        """
        mapped_dups: dict[list[dict]] = {}
        beets_base = config["beets"]["base-path"].get(str)
        nd_base = config["navidrome"]["base-path"].get(str)
        for key in beets_dups:
            mapped_dups[key] = {}
            for beets_path in beets_dups[key]:
                nd_path = beets_path.replace(beets_base, nd_base, 1)
                # Normalize Unicode characters in the file path. Otherwise characters like `á` (`\u0061\u0301`)
                # and `á` (`\u00e1`) are not threaded as the same.
                nd_path = unicodedata.normalize("NFC", nd_path)
                mapped_dups[key][nd_path] = beets_path

        PU.info(f"Base paths mapping done ('{beets_base}':'{nd_base}')")
        return mapped_dups

    def _query_media_data(self, dups_input: dict[str, dict]):
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
                self.data.media[key] = []
                batch = list(self.db.get_media_batch(files, conn))
                self.data.media[key] += batch
                self.stats.duplicate_files += len(files.keys())

                PU.progress_bar(progress, progress_total)
                progress += 1

                # Handle excluded files

                # --> Not found in Navidrome
                if len(files) != len(batch):
                    missing_media = [f for f in files.keys() if f not in [m.path for m in batch]]
                    for file in missing_media:
                        PU.warning(msg=f"\nExcluding media file not found in Navidrome: {file}")

                # --> Different release
                # TODO

            PU.progress_done(progress_total)

    def _merge_annotation_list(self, dups: list[MediaFile]):
        """
        Merge data of all media file annotations referred to as duplicates.

        Args:
           duplicates (list[MediaFile]): Dictionary of media files grouped by their key.

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

    def _save_all_annotations(self, duplicates: dict[str, list[MediaFile]]):
        """
        Save all annotations of all media file duplicates to the database.
        """
        with NavidromeDbConnection() as conn:
            for _, dups in duplicates.items():
                for media in dups:
                    self.db.store_annotation(media.annotation, conn)
            conn.commit()

    def _has_errors(self) -> bool:
        """Check if there are any errors in the processing."""
        return len(self.errors) > 0

    def _generate_command_yaml(self, file_name):
        """
        Generate a YAML command file.

        It purposely create invalid YAML keys for keys with `None` values, in order to provide
        a different syntax highlighting for those keys. This way users can more quickly see
        which files are not going to be deleted.
        """
        # Serialize the data to a YAML string
        yaml = YAML()
        yaml.indent(mapping=2, sequence=4, offset=2)
        stream = StringIO()
        yaml.dump(data, stream)
        yaml_str = stream.getvalue()

        # Remove the colon (and trailing space) for keys with `None` values
        modified_yaml = re.sub(
            r"^(\s{2}[^:\n]+):\s*$",  # Match lines like "  inner_key: " (2-space indentation)
            r"\1",  # Replace with "  inner_key"
            yaml_str,
            flags=re.MULTILINE,
        )

        # Save to a file
        with open(file_name, "w") as f:
            f.write(modified_yaml)

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
        PU.note(f"This folder: {SU.gray(this.folder)}, That folder: {SU.gray(that.folder)}")

        # Real album folder files are keepable over files in root, artist or dump folders
        left: Folder = this.folder
        right: Folder = that.folder
        if left.beets_path != right.beets_path:
            PU.log(f"Compare if file is in album folder: {left.type} || {right.type}", 1)
            if left.type != right.type:
                if left.type == Folder.Type.ALBUM:
                    msg = f"Other is an album folder: {SU.gray(this.folder.beets_path)}"
                    PU.log(msg, 2)
                    that.delete_reason = msg
                    return this
                elif right.type == Folder.Type.ALBUM:
                    msg = f"Other is an album folder: {SU.gray(that.folder.beets_path)}"
                    PU.log(msg, 2)
                    this.delete_reason = msg
                    return that
        # Skip if both are of the same path and type

        # Check for dirty folders
        left = this.folder.is_dirty
        right = that.folder.is_dirty
        PU.log(f"Compare dirty folders: {left} || {right}", 1)
        if left != right:
            if left:
                msg = f"This folder is dirty: {SU.gray(this.folder.beets_path)}"
                PU.log(msg, 2)
                this.delete_reason = msg
                return that
            elif right:
                msg = f"That folder is dirty: {SU.gray(that.folder.beets_path)}"
                PU.log(msg, 2)
                that.delete_reason = msg
                return this
        # Skip if both are incomplete

        # Check completeness of album folder
        left = this.folder
        right = that.folder
        if left.missing is not None and right.missing is not None:
            PU.log(f"Compare missing tracks: {left.missing}/{left.total} || {right.missing}/{right.total}", 1)
            if (left.missing != right.missing) and (left.missing > 0 or right.missing > 0):
                if (left.missing < right.missing) and not left.is_dirty:
                    msg = f"Other folder is more complete ({left.missing}/{left.total}): {SU.gray(this.path)}"
                    PU.log(msg, 2)
                    that.delete_reason = msg
                    return this
                elif (left.missing > right.missing) and not right.is_dirty:
                    msg = f"Other folder is more complete ({right.missing}/{right.total}): {SU.gray(that.path)}"
                    PU.log(msg, 2)
                    this.delete_reason = msg
                    return that
        # Skip if both are incomplete, none has missing tracks or have no information on missing tracks

        # If the album folder already contains a keepable, we wanna keep all the items, except for dirty folders
        left = this.folder and this.folder.has_keepable
        l_dirty = this.folder and this.folder.is_dirty
        right = that.folder and that.folder.has_keepable
        r_dirty = that.folder and that.folder.is_dirty
        PU.log(f"Compare if album folder contain a keepable: {left} +dirty: {l_dirty}  || {right} +dirty: {r_dirty}", 1)
        if left != right:
            if left and not l_dirty:
                that.delete_reason = f"Other album folder already contains a keepable | {SU.gray(this.path)}"
                return this
            elif right and not r_dirty:
                this.delete_reason = f"Other album folder already contains a keepable | {SU.gray(that.path)}"
                return that
        # Skip, if they are the same

        # If file paths are equal, except one contains a numeric suffix, keep the other
        left = FileUtil.equal_file_with_numeric_suffix(this.path, that.path)
        right = FileUtil.equal_file_with_numeric_suffix(that.path, this.path)
        PU.log(f"Compare paths with numeric suffix: {right} || {left}", 1)
        if left or right:
            if left:
                that.delete_reason = f"File has a numeric suffix (seems to be a copy) | {SU.gray(this.path)}"
                return this
            elif right:
                this.delete_reason = f"File has a numeric suffix (seems to be a copy) | {SU.gray(that.path)}"
                return that
        # Skip, if none is a suffixed path

        # Having a preferred file extension is keepable
        left = this.path.split(".")[-1].lower() in config["pref-extensions"].get(list)
        right = that.path.split(".")[-1].lower() in config["pref-extensions"].get(list)
        PU.log(f"Compare if file extension is keepable: {left} || {right}", 1)
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
        PU.log(f"Compare MusicBrainz recording ID: {left} || {right}", 1)
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
        PU.log(f"Artist record available: {left} || {right}", 1)
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
        PU.log(f"MusicBrainz Album ID available: {left} || {right}", 1)
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
        PU.log(f"Compare track numbers: {left} || {right}", 1)
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
        PU.log(f"Compare bitrate: {left} || {right}", 1)
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
        PU.log(f"Compare year info: {left} || {right}", 1)
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
        PU.log(f"Fuzzy match filename and track title: {left} || {right}", 1)
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
        PU.log(f"Fuzzy match album name: {left} || {right}", 1)
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


def print_info():
    """Prints the current configuration details."""
    # Print app version
    with open("pyproject.toml", mode="rb") as file:
        data = tomli.load(file)
        version = data["tool"]["poetry"]["version"]
        PrintUtil.ln()
        PrintUtil.bold(f"  Heartbeets v{version}")
        PrintUtil.ln()

    # Print config details
    PrintUtil.bold("\nInitializing configuration")
    PrintUtil.ln()
    PrintUtil.info(f"Dry-run: {config["dry-run"].get(bool)}")
    PrintUtil.info(f"Navidrome database path: {config["navidrome"]["database"].get(str)}")
    PrintUtil.info(f"Output folder: {config["data"].get(str)}")
    PrintUtil.info(f"Beets library root: {config["beets"]["base-path"].get(str)}")
    PrintUtil.info(f"Navidrome library root: {config["navidrome"]["base-path"].get(str)}")


if __name__ == "__main__":
    print_info()

    # Read the action argument from the command line
    action = ""
    for arg in sys.argv:
        if arg.startswith("action="):
            action = arg.split("=")[1]
            break
    else:
        PU.error("No action specified. Please use the format 'python app.py action=<action>'.")
        sys.exit(1)

    processor = DuplicateProcessor()

    if action == "remove-unsupported":
        music = config["music"].get(str)
        data = config["data"].get(str)
        remove_ext = config["remove-extensions"].get(list)
        dry_run = config["music"].get(str)
        FileTools.move_by_extension(music, data, remove_ext, dry_run)
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
