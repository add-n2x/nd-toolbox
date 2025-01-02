"""
Utility classes and functions for the ndtoolbox package.
"""

import logging
import os
import sys
from datetime import datetime
from enum import Enum

import colorlog
from dotenv import find_dotenv, load_dotenv


class ToolboxConfig:
    """
    Configuration class for ND Toolbox.
    """

    timezone = None
    logger = None

    nd_dir = None
    data_dir = None
    music_dir = None
    source_base = None
    target_base = None

    def __init__(self):
        """Init config from environment variables."""
        load_dotenv(find_dotenv())

        ToolboxConfig.timezone = os.getenv("TZ", "UTC")
        ToolboxConfig.nd_dir = os.getenv("ND_DIR")
        ToolboxConfig.data_dir = os.getenv("DATA_DIR")
        ToolboxConfig.music_dir = os.getenv("MUSIC_DIR")
        ToolboxConfig.source_base = os.getenv("BEETS_BASE_PATH")
        ToolboxConfig.target_base = os.getenv("ND_BASE_PATH")

        # Setup logger
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        if log_level not in logging._nameToLevel:
            raise ValueError(f"Invalid LOG_LEVEL: {log_level}")
        log_file = ToolboxConfig.data_dir + "/nd-toolbox.log"
        ToolboxConfig.logger = colorlog.getLogger("ndtoolbox")
        colorlog.basicConfig(
            filename=log_file,
            filemode="w",
            encoding="utf-8",
            level=log_level,
            format="%(log_color)s %(msecs)d %(name)s %(levelname)s %(message)s",
        )
        print(f"Initialized logger with level: {log_level} and log file: {log_file}")


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


class TerminalColors(Enum):
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

    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    STRIKE = "\u0336"


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
        msg = TerminalColors.BOLD.value + msg + TerminalColors.RESET.value
        print(PrintUtils.indent(msg, lvl))
        if log:
            ToolboxConfig.logger.info(msg)

    @staticmethod
    def underline(msg, lvl=0, log=True):
        """Print unterlined text with indentation based on level."""
        msg = TerminalColors.UNDERLINE.value + msg + TerminalColors.RESET.value
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
        msg = TerminalColors.RED.value + msg + TerminalColors.RESET.value
        print(PrintUtils.indent(msg, lvl))
        ToolboxConfig.logger.error(msg)

    @staticmethod
    def success(msg, lvl=0):
        """Print green text with indentation based on level."""
        msg = TerminalColors.GREEN.value + msg + TerminalColors.RESET.value
        print(PrintUtils.indent(msg, lvl))
        ToolboxConfig.logger.info(msg)

    @staticmethod
    def warning(msg, lvl=0):
        """Print orange text with indentation based on level."""
        msg = TerminalColors.ORANGE.value + msg + TerminalColors.RESET.value
        print(PrintUtils.indent(msg, lvl))
        ToolboxConfig.logger.warning(msg)

    @staticmethod
    def log(msg, lvl=0):
        """Log info message with indentation based on level."""
        msg = PrintUtils.indent(msg, lvl)
        ToolboxConfig.logger.info(msg)


class DotDict(dict):
    """
    Wrap a dictionary with `DotDict()` to allow property access using the dot.notation.
    """

    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
