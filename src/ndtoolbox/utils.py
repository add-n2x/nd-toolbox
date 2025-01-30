"""
Utility classes and functions for the ndtoolbox package.
"""

import glob
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

from fuzzywuzzy import fuzz

from ndtoolbox.config import config


class Stats:
    """Statistics class to keep track of various counts."""

    app: object
    duplicate_records: int
    duplicate_albums: int
    duplicate_artists: int
    duplicate_genres: int
    duplicate_files: int
    media_files: int
    file_annotations: int
    media_files_keepable: int
    media_files_deletable: int

    _start: float = 0.0
    _stop: float = 0.0

    def __init__(self, app):
        """Initialize statistics counters."""
        self.app = app
        self.duplicate_records = 0
        self.duplicate_albums = 0
        self.duplicate_artists = 0
        self.duplicate_genres = 0
        self.duplicate_files = 0
        self.media_files = 0
        self.file_annotations = 0
        self.media_files_keepable = 0
        self.media_files_deletable = 0

    def start(self):
        """Start the operation."""
        self._start = datetime.now().timestamp()
        self._stop = 0.0

    def stop(self):
        """Stop the operation."""
        self._stop = datetime.now().timestamp()

    def print_duration(self):
        """Print the duration of the operation."""
        """Get the duration of the operation in seconds."""
        duration = round(self._stop - self._start, 2)
        if duration > 60:
            duration = f"{round(duration / 60, 2)} minutes"
        else:
            duration = f"{duration} seconds"
        PrintUtil.success(f"Finished in {duration}")

    def print_stats(self):
        """Print statistics about the processing."""
        PrintUtil.bold("\nSTATS")
        PrintUtil.ln()
        PrintUtil.info("Duplicates:", 0)
        PrintUtil.info(f"Tuples: {self.duplicate_records}", 1)
        PrintUtil.info(f"Files: {self.duplicate_files}", 1)
        PrintUtil.info(f"Artists: {len(self.app.data.artists)}", 1)
        PrintUtil.info(f"Albums: {len(self.app.data.albums)}", 1)
        PrintUtil.info(f"Directories: {len(self.app.data.directories)}", 1)
        PrintUtil.ln()


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
    def is_library_path(base_path: str, path: str) -> bool:
        """Check if the given path is a library path."""
        return path.startswith(base_path)

    @staticmethod
    def get_album_folder(path: str) -> str:
        """Get album folder from file path."""
        folder = FileUtil.get_folder(path)
        return folder.split(os.sep)[-1]

    @staticmethod
    def is_album_folder(base_path: str, path: str) -> bool:
        """Check if the given path is an album folder."""
        relative_path = os.path.relpath(path, base_path)
        folders = relative_path.split(os.sep)
        return len(folders) == 2 and folders[1] != ""

    @staticmethod
    def get_artist_folder(path: str) -> str:
        """Get artist folder from file path."""
        folder = FileUtil.get_folder(path)
        return folder.split(os.sep)[-2]

    @staticmethod
    def is_artist_folder(base_path: str, path: str) -> bool:
        """Check if the given path is an artist folder."""
        relative_path = os.path.relpath(path, base_path)
        folders = relative_path.split(os.sep)
        return len(folders) == 1 and folders[0] != ""

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

    @staticmethod
    def strip_terminal_colors(text):
        """Match and strip ANSI escape sequences."""
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        return ansi_escape.sub("", text)


class PrintUtil:
    """
    Utilities for printing and logging.
    """

    in_progress: bool = True

    @staticmethod
    def indent(msg: str, lvl: int = 0) -> str:
        """Indent a message by a specified number of levels."""
        return " " * 6 * lvl + msg

    @staticmethod
    def ln(thick=False):
        """Print a ASCII line with optional length."""
        c = "─" if not thick else "━"
        PrintUtil.print(c * 80)
        config.logger.info(c * 80)

    @staticmethod
    def bold(msg, lvl=0, log=True):
        """Print bold text with indentation based on level."""
        msg = StringUtil.bold(msg)
        PrintUtil.print(PrintUtil.indent(msg, lvl))
        if log:
            config.logger.info(msg)

    @staticmethod
    def underline(msg, lvl=0, log=True):
        """Print unterlined text with indentation based on level."""
        msg = StringUtil.underline(msg)
        PrintUtil.print(PrintUtil.indent(msg, lvl))
        if log:
            config.logger.info(msg)

    @staticmethod
    def info(msg, lvl=0, log=True, end="\n"):
        """Print normal text with indentation based on level."""
        PrintUtil.print(PrintUtil.indent(msg, lvl), end=end)
        if log:
            config.logger.info(PrintUtil.indent(msg, lvl))

    @staticmethod
    def error(msg, lvl=0):
        """Print red text with indentation based on level."""
        msg = StringUtil.red(msg)
        PrintUtil.print(PrintUtil.indent(msg, lvl))
        config.logger.error(msg)

    @staticmethod
    def success(msg, lvl=0):
        """Print green text with indentation based on level."""
        msg = StringUtil.green(msg)
        PrintUtil.print(PrintUtil.indent(msg, lvl))
        config.logger.info(msg)

    @staticmethod
    def warning(msg, lvl=0):
        """Print orange text with indentation based on level."""
        msg = StringUtil.orange(msg)
        PrintUtil.print(PrintUtil.indent(msg, lvl))
        config.logger.warning(msg)

    @staticmethod
    def note(msg, lvl=0):
        """Print note text with indentation based on level."""
        msg = StringUtil.blue(msg)
        PrintUtil.print(PrintUtil.indent(msg, lvl))
        config.logger.info(msg)

    @staticmethod
    def print(msg, log=True, end="\n"):
        """Print text with progress bar line handling."""
        terminal_height = PrintUtil.get_terminal_height()
        PrintUtil.move_cursor_to_line(terminal_height - 1)
        PrintUtil.clear_line()
        print(msg, end)
        PrintUtil.move_cursor_to_line(terminal_height)
        sys.stdout.flush()
        config.logger.info(msg)

    @staticmethod
    def log(msg, lvl=0):
        """Log info message with indentation based on level."""
        msg = PrintUtil.indent(msg, lvl)
        config.logger.info(msg)

    @staticmethod
    def debug(msg, lvl=0):
        """Debug log message."""
        msg = PrintUtil.indent(msg, lvl)
        config.logger.debug(msg)

    @staticmethod
    def get_terminal_height():
        """
        Returns the terminal's height in lines.
        """
        return shutil.get_terminal_size().lines

    @staticmethod
    def move_cursor_to_line(line):
        """
        Moves the cursor to a specific line in the terminal.

        Args:
            line (int): Line number to move the cursor to. Starts at 0.
        """
        sys.stdout.write(f"\033[{line};0H")
        # sys.stdout.flush()

    @staticmethod
    def clear_line():
        """
        Clears the current line in the terminal to remove left over text.
        """
        sys.stdout.write("\033[K")


class ProgressBar:
    """Render a progress bar at the terminal."""

    length: int
    total: int
    progress: int

    def __init__(self, total: int, length: int = 80):
        """
        Init instance.

        Args:
            total (int): Total number of steps.
            length (int): Length of the progress bar. Defaults to 80 characters.
        """
        self.length = length
        self.total = total
        self.progress = 0

    def update(self, steps: int = 1):
        """
        Renders a progress bar at the last line of the terminal.

        Args:
           steps (int): Number of steps to advance the progress bar. Defaults to 1.
        """
        self.progress += steps
        terminal_height = PrintUtil.get_terminal_height()
        PrintUtil.move_cursor_to_line(terminal_height)
        PrintUtil.clear_line()
        percent = 100 * (self.progress / self.total)
        bar_length = int(self.length * self.progress / self.total)
        bar = "█" * bar_length + "·" * (self.length - bar_length)
        sys.stdout.write(StringUtil.green(f"|{bar}| {percent:.2f}%"))
        sys.stdout.flush()

    def done(self):
        """
        Clears the progress bar and restores normal terminal behavior after completion.
        """
        self.progress = self.total
        self.update(0)
        terminal_height = PrintUtil.get_terminal_height()
        PrintUtil.move_cursor_to_line(terminal_height)  # Move to the last line
        sys.stdout.write("\n\n")  # Move to the next line for normal printing
        sys.stdout.flush()


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
        PrintUtil.info(msg)
        for ext in extensions:
            search = os.path.join(source, f"**/*.{ext}")
            PrintUtil.info(f"[dry-run: {dry}] Searching .{ext} files ({search})", 1)
            for file in glob.iglob(search, recursive=True):
                PrintUtil.info(f"[dry-run: {dry}] Found '{file}'")

                # Create folder hierarchy in target
                abs_target_dir = os.path.join(abs_target, os.path.dirname(file))
                PrintUtil.info(f"[dry-run: {dry}] Creating target directory: {abs_target_dir}", 2)
                if not dry:
                    os.makedirs(abs_target_dir, exist_ok=True)

                # Move files
                abs_file = os.path.abspath(file)
                PrintUtil.info(f"[dry-run: {dry}] Move {abs_file} to {abs_target_dir}", 2)
                if not dry:
                    shutil.move(abs_file, abs_target_dir)
