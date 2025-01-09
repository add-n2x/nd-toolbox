"""
Utility classes and functions for the ndtoolbox package.
"""

import glob
import logging
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

import colorlog
import tomli
from dotenv import find_dotenv, load_dotenv
from fuzzywuzzy import fuzz


class FileUtil:
    """Utility class for string operations."""

    @staticmethod
    def equal_file_with_numeric_suffix(plain_file: str, suffix_file: str) -> bool:
        """Check if two file names are equal, except the second string having a numeric suffix."""
        _, plain_file = os.path.split(plain_file)
        plain_file: str = Path(plain_file).stem
        _, suffix_file = os.path.split(suffix_file)
        suffix_file = suffix_file.lower().removeprefix(plain_file.lower())
        suffix: str = Path(suffix_file).stem
        if suffix and suffix.strip().isdigit():
            return True

        return False

    @staticmethod
    def fuzzy_match_track(path: str, media) -> bool:
        """Check if path and media file artist and title are similar using fuzzy matching."""
        _, file = os.path.split(path)
        file = Path(file).stem.lower()
        title = str(media.title).lower()
        album = str(media.album_name).lower()
        artist = str(media.artist_name).lower()
        r1 = fuzz.ratio(file, title)
        r2 = fuzz.ratio(file, artist + " - " + title)
        r3 = fuzz.ratio(file, artist + " - " + album + " - " + title)
        # print(f"Got ratios for '{media.title}': {r1}, {r2}, {r3}")
        return max(r1, r2, r3)

    @staticmethod
    def fuzzy_match_album(path: str, media) -> bool:
        """Check if path and media file album are similar using fuzzy matching."""
        _, file = os.path.split(path)
        file = Path(file).stem.lower()
        album = str(media.album_name).lower()
        artist = str(media.artist_name).lower()
        r1 = fuzz.ratio(file, album)
        r2 = fuzz.ratio(file, artist + " - " + album)
        # print(f"Got ratios for '{media.title}': {r1}, {r2}, {r3}")
        return max(r1, r2)

    @staticmethod
    def get_folder(path: str) -> str:
        """Get folder from file path."""
        folders, _ = os.path.split(path)
        return folders

    @staticmethod
    def get_album_folder(path: str) -> str:
        """Get album folder from file path."""
        folder = FileUtil.get_folder(path)
        return folder.split(os.sep)[-1]

    @staticmethod
    def get_file(path: str) -> str:
        """Get album folder from file path."""
        _, file = os.path.split(path)
        return file


class DateUtil:
    """Utility class for date operations."""

    @staticmethod
    def format_date(date: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format a date according to the specified format."""
        if not date:
            return ""
        return date.strftime(fmt)

    @staticmethod
    def parse_date(date_str: str, fmt: str = "%Y-%m-%d %H:%M:%S") -> datetime:
        """Parse a date string according to the specified format."""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            return datetime.fromisoformat(date_str)


class CLI:
    """Terminal dialog asking to continue or exit."""

    @staticmethod
    def ask_continue(key: str = "c", message: str = "Type (c) to continue, any key to quit: ", exit: bool = True):
        """
        Ask to continue or exit.

        Args:
            key (str): The key to press to continue. Defaults to "c".
            message (str): The message to display. Defaults to "Type (c) to continue, any key to quit: ".
            exit (bool): Whether to exit the program if the key is not pressed. Defaults to True.
        """
        _ = input(message).lower()
        if _ != key:
            if exit:
                print("Good bye.")
                sys.exit(0)
            return False
        return True


class StringUtil:
    """
    Colors for formatting terminal output.
    """

    RESET = "\033[0m"
    HEADER = "\033[95m"

    RED = "\033[91m"
    GREEN = "\033[92m"
    ORANGE = "\033[93m"
    BLUE = "\033[34m"
    PINK = "\033[35m"
    CYAN = "\033[36m"
    GRAY = "\033[90m"

    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    STRIKE = "\u0336"

    @staticmethod
    def header(text: str) -> str:
        """Format text as a header."""
        return f"{StringUtil.HEADER}{text}{StringUtil.RESET}"

    @staticmethod
    def bold(text: str) -> str:
        """Format text as bold."""
        return f"{StringUtil.BOLD}{text}{StringUtil.RESET}"

    @staticmethod
    def underline(text: str) -> str:
        """Format text with an underline."""
        return f"{StringUtil.UNDERLINE}{text}{StringUtil.RESET}"

    @staticmethod
    def strike(text: str) -> str:
        """Format text with a strikethrough."""
        return f"{StringUtil.STRIKE}{text}{StringUtil.RESET}"

    @staticmethod
    def red(text: str) -> str:
        """Format text as red."""
        return f"{StringUtil.RED}{text}{StringUtil.RESET}"

    @staticmethod
    def green(text: str) -> str:
        """Format text as green."""
        return f"{StringUtil.GREEN}{text}{StringUtil.RESET}"

    @staticmethod
    def orange(text: str) -> str:
        """Format text as orange."""
        return f"{StringUtil.ORANGE}{text}{StringUtil.RESET}"

    @staticmethod
    def blue(text: str) -> str:
        """Format text as blue."""
        return f"{StringUtil.BLUE}{text}{StringUtil.RESET}"

    @staticmethod
    def pink(text: str) -> str:
        """Format text as pink."""
        return f"{StringUtil.PINK}{text}{StringUtil.RESET}"

    @staticmethod
    def gray(text: str) -> str:
        """Format text as gray."""
        return f"{StringUtil.GRAY}{text}{StringUtil.RESET}"


class PrintUtils:
    """
    Utilities for printing and logging.
    """

    @staticmethod
    def indent(msg: str, lvl: int = 0) -> str:
        """Indent a message by a specified number of levels."""
        return " " * 6 * lvl + msg

    @staticmethod
    def ln(thick=False):
        """Print a ASCII line with optional length."""
        c = "─" if not thick else "━"
        print(c * 80)
        ToolboxConfig.logger.info(c * 80)

    @staticmethod
    def bold(msg, lvl=0, log=True):
        """Print bold text with indentation based on level."""
        msg = StringUtil.bold(msg)
        print(PrintUtils.indent(msg, lvl))
        if log:
            ToolboxConfig.logger.info(msg)

    @staticmethod
    def underline(msg, lvl=0, log=True):
        """Print unterlined text with indentation based on level."""
        msg = StringUtil.underline(msg)
        print(PrintUtils.indent(msg, lvl))
        if log:
            ToolboxConfig.logger.info(msg)

    @staticmethod
    def info(msg, lvl=0, log=True, end="\n"):
        """Print normal text with indentation based on level."""
        print(PrintUtils.indent(msg, lvl), end=end)
        if log:
            ToolboxConfig.logger.info(PrintUtils.indent(msg, lvl))

    @staticmethod
    def error(msg, lvl=0):
        """Print red text with indentation based on level."""
        msg = StringUtil.red(msg)
        print(PrintUtils.indent(msg, lvl))
        ToolboxConfig.logger.error(msg)

    @staticmethod
    def success(msg, lvl=0):
        """Print green text with indentation based on level."""
        msg = StringUtil.green(msg)
        print(PrintUtils.indent(msg, lvl))
        ToolboxConfig.logger.info(msg)

    @staticmethod
    def warning(msg, lvl=0):
        """Print orange text with indentation based on level."""
        msg = StringUtil.orange(msg)
        print(PrintUtils.indent(msg, lvl))
        ToolboxConfig.logger.warning(msg)

    @staticmethod
    def note(msg, lvl=0):
        """Print note text with indentation based on level."""
        msg = StringUtil.blue(msg)
        print(PrintUtils.indent(msg, lvl))
        ToolboxConfig.logger.info(msg)

    @staticmethod
    def log(msg, lvl=0):
        """Log info message with indentation based on level."""
        msg = PrintUtils.indent(msg, lvl)
        ToolboxConfig.logger.info(msg)


class FileTools:
    """
    Utility class for file operations.
    """

    @staticmethod
    def move_by_extension(source: str, target: str, extensions: list[str], dry: bool):
        """
        Move files with specific extensions from source to target directory.

        Args:
            source (str): Source directory.
            target (str): Target directory.
            extensions (list): List of file extensions to move.
            dry (bool): Dry-run mode.
        """
        if source.startswith("./"):
            source = source[2:]
        abs_target = os.path.join(os.path.abspath(target), "removed-media")
        msg = f"[dry-run: {dry}] Moving files file in '{source}' having '{str(extensions)}' extensions, to '{target}'."
        PrintUtils.info(msg)
        for ext in extensions:
            search = os.path.join(source, f"**/*.{ext}")
            PrintUtils.info(f"[dry-run: {dry}] Searching .{ext} files ({search})", 1)
            for file in glob.iglob(search, recursive=True):
                PrintUtils.info(f"[dry-run: {dry}] Found '{file}'")

                # Create folder hierarchy in target
                abs_target_dir = os.path.join(abs_target, os.path.dirname(file))
                PrintUtils.info(f"[dry-run: {dry}] Creating target directory: {abs_target_dir}", 2)
                if not dry:
                    os.makedirs(abs_target_dir, exist_ok=True)

                # Move files
                abs_file = os.path.abspath(file)
                PrintUtils.info(f"[dry-run: {dry}] Move {abs_file} to {abs_target_dir}", 2)
                if not dry:
                    shutil.move(abs_file, abs_target_dir)


class ToolboxConfig:
    """
    Configuration class for ND Toolbox.
    """

    FILE_BEETS_INPUT_JSON: str
    FILE_TOOLBOX_DATA_JSON: str
    ERROR_REPORT_JSON: str

    timezone: str = None
    dry_run: bool = None
    logger: logging.Logger = None
    pref_extensions: list = None
    remove_extensions: list = None
    navidrome_db_path: str = None
    nd_dir: str = None
    data_folder: str = None
    music_folder: str = None
    source_base: str = None
    target_base: str = None

    def __init__(self, dry_run: bool = True):
        """Init config from environment variables."""
        load_dotenv(find_dotenv())
        ToolboxConfig.timezone = os.getenv("TZ", "UTC")
        ToolboxConfig.dry_run = False if os.getenv("DRY_RUN").lower() == "false" else True
        ToolboxConfig.pref_extensions = os.getenv("PREFERRED_EXTENSIONS").split(" ")
        ToolboxConfig.remove_extensions = os.getenv("UNSUPPORTED_EXTENSIONS").split(" ")
        ToolboxConfig.nd_dir = os.getenv("ND_DIR")
        ToolboxConfig.navidrome_db_path = os.path.join(ToolboxConfig.nd_dir, "navidrome.db")
        ToolboxConfig.data_folder = os.getenv("DATA_DIR")
        ToolboxConfig.music_folder = os.getenv("MUSIC_DIR")
        ToolboxConfig.source_base = os.getenv("BEETS_BASE_PATH")
        ToolboxConfig.target_base = os.getenv("ND_BASE_PATH")

        # Init file paths.
        ToolboxConfig.FILE_BEETS_INPUT_JSON = os.path.join(ToolboxConfig.data_folder, "beets/beets-duplicates.json")
        ToolboxConfig.FILE_TOOLBOX_DATA_JSON = os.path.join(ToolboxConfig.data_folder, "nd-toolbox-data.json")
        ToolboxConfig.ERROR_REPORT_JSON = os.path.join(ToolboxConfig.data_folder, "nd-toolbox-error.json")

        # Setup logger
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        if log_level not in logging._nameToLevel:
            raise ValueError(f"Invalid LOG_LEVEL: {log_level}")
        log_file = os.path.join(ToolboxConfig.data_folder, "nd-toolbox.log")
        ToolboxConfig.logger = colorlog.getLogger("ndtoolbox")

        colorlog.basicConfig(
            filename=log_file,
            filemode="w",
            encoding="utf-8",
            level=log_level,
            format="%(log_color)s %(msecs)d %(name)s %(levelname)s %(message)s",
        )
        PrintUtils.info(f"Initialized logger with level: {log_level} and log file: {log_file}")

        # Print app version
        with open("pyproject.toml", mode="rb") as file:
            data = tomli.load(file)
            version = data["tool"]["poetry"]["version"]
            PrintUtils.ln()
            PrintUtils.bold(f"  NAVIDROME TOOLBOX v{version}")
            PrintUtils.ln()

        # Print config details
        PrintUtils.bold("Initializing configuration")
        PrintUtils.ln()
        PrintUtils.info(f"Dry-run: {ToolboxConfig.dry_run}")
        PrintUtils.info(f"Navidrome database path: {self.navidrome_db_path}")
        PrintUtils.info(f"Output folder: {ToolboxConfig.data_folder}")
        PrintUtils.info(f"Source base: {ToolboxConfig.source_base}")
        PrintUtils.info(f"Target base: {ToolboxConfig.target_base}")
