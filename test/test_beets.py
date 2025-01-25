"""
Tests for the Beets integration.
"""

import io
import sys
from datetime import datetime

from beets.ui import main

from ndtoolbox.beets import BeetsClient
from ndtoolbox.config import config

IS_MICROSOFT_PYTHON = "AppData\\Local\\Microsoft\\WindowsApps" in sys.exec_prefix

config.set_file("test/config/config.yaml")


def test_beets_ui():
    """Test Beets UI."""
    if IS_MICROSOFT_PYTHON:
        return

    captured_output = io.StringIO()
    sys.stdout = captured_output
    main(["-c", "config/beets/config.yaml", "stats"])
    sys.stdout = sys.__stdout__
    results = captured_output.getvalue()
    captured_output.close()
    print("Beets stats:" + results)


def test_beets_client():
    """Test Beets client."""
    if IS_MICROSOFT_PYTHON:
        return

    start1 = datetime.now()
    info = BeetsClient(0).get_album_info("/music/Calibre/Second Sun/")
    assert info is not None
    for i in info:
        print("Subprocess Query - Beets album info: " + i)
    stop1 = datetime.now()

    start2 = datetime.now()
    client = BeetsClient(1)
    info = client.get_album_info("/music/Calibre/Second Sun/")
    assert info is not None
    for i in info:
        print("Stdio Capture - Beets album info: " + i)
    stop2 = datetime.now()

    print("Subprocess Query Time: " + str(stop1 - start1))
    print("Stdio Capture Time: " + str(stop2 - start2))
