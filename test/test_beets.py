"""
Tests for the Beets integration.
"""

import io
import sys

from beets.ui import main

from ndtoolbox.beets import beets
from ndtoolbox.config import config

config.set_file("test/config/config.yaml")


def test_beets_ui():
    """Test Beets UI."""
    captured_output = io.StringIO()
    sys.stdout = captured_output
    main(["-c", "config/beets/config.yaml", "stats"])
    sys.stdout = sys.__stdout__
    results = captured_output.getvalue()
    captured_output.close()
    print("Beets stats:" + results)


def test_beets_client():
    """Test Beets client."""
    info = beets.get_album_info("/music/Calibre/Second Sun/")
    assert info is not None
    for i in info:
        print("Subprocess Query - Beets album info: " + i)

    # client = BeetsClient(1)
    # info = client.get_album_info("/music/Calibre/Second Sun/")
    # assert info is not None
    # for i in info:
    #     print("Stdio Capture - Beets album info: " + i)
