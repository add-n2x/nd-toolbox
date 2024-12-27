"""
Utility classes and functions for the ndtools package.
"""

import sys
from enum import Enum


class CLI:
    """Terminal dialog asking to continue or exit."""

    def ask_continue():
        """Ask to continue or exit."""
        _ = input("Type (c) to continue, any key to quit: ").lower()
        if _ != "c":
            print("Good bye.")
            sys.exit(0)


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
