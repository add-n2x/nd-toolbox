"""
Utility classes and functions for the ndtools package.
"""

from datetime import datetime
import sys
from enum import Enum


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
        return datetime.strptime(date_str, fmt)


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
    def print(text, lvl=0):
        """Print normal text with indentation based on level."""
        print(" " * 6 * lvl + text)

    @staticmethod
    def println(text, lvl=0):
        """Print with new line an normal text with indentation based on level."""
        print("\n" + " " * 6 * lvl + text)

    @staticmethod
    def bold(text, lvl=0):
        """Print bold text with indentation based on level."""
        print(TerminalColors.BOLD.value + text + TerminalColors.RESET.value, lvl)

    @staticmethod
    def red(text, lvl=0):
        """Print red text with indentation based on level."""
        PrintUtils.print(TerminalColors.RED.value + text + TerminalColors.RESET.value, lvl)

    @staticmethod
    def green(text, lvl=0):
        """Print green text with indentation based on level."""
        PrintUtils.print(TerminalColors.GREEN.value + text + TerminalColors.RESET.value, lvl)

    @staticmethod
    def orange(text, lvl=0):
        """Print orange text with indentation based on level."""
        PrintUtils.print(TerminalColors.ORANGE.value + text + TerminalColors.RESET.value, lvl)


class DotDict(dict):
    """
    Wrap a dictionary with `DotDict()` to allow property access using the dot.notation.
    """

    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
