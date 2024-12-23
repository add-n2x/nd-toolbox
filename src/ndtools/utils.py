"""
Utility classes and functions for the ndtools package.
"""

from enum import Enum
import sys


class CLI:
    def ask_continue():
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
    @staticmethod
    def red(text):
        print(TerminalColors.RED.value + text + TerminalColors.RESET.value)

    @staticmethod
    def green(text):
        print(TerminalColors.GREEN.value + text + TerminalColors.RESET.value)

    @staticmethod
    def orange(text):
        print(TerminalColors.ORANGE.value + text + TerminalColors.RESET.value)


class DotDict(dict):
    """
    Wrap a dictionary with `DotDict()` to allow property access using the dot.notation.
    """

    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
