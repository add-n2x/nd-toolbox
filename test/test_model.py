"""Test models."""

from typing import Generator

import pytest
from easydict import EasyDict

from ndtoolbox.beets import BeetsClient
from ndtoolbox.model import Folder, MediaFile
from ndtoolbox.utils import ToolboxConfig

ND_DATABASE_PATH = "test/data/navidrome.db"
ND_DATA_FILE = "data/nd-toolbox-data.json"
ND_DATA_FILE = "test/data/nd-toolbox-data.json"
DATA_DIR = "test/data"
BEETS_BASE_PATH = "/music"
ND_BASE_PATH = "/music/library"
config = ToolboxConfig(False)


@pytest.fixture(scope="session")
def infos() -> Generator[EasyDict]:
    """Fixture to provide folder information."""
    info = EasyDict({"album": None, "total": None, "missing": None, "compilation": False})
    yield [info]


@pytest.fixture(scope="session")
def infos2() -> Generator[EasyDict]:
    """Fixture to provide folder information."""
    info = EasyDict({"album": None, "total": None, "missing": None, "compilation": False})
    yield [info, info]


def test_album_folder(infos, mocker):
    """Test album folder."""
    mocker.patch.object(BeetsClient, "get_album_info", autospec=True)
    BeetsClient.get_album_info.return_value = infos

    media = MediaFile(
        "1", "/music/artist/album/track.mp3", "title", 2003, 1, 33, 64, "1", "artist", "2", "album", "mbz3"
    )
    media.beets_path = "/music/artist/album/track.mp3"
    folder = Folder(media)
    assert folder.beets_path == "/music/artist/album"
    assert folder.has_keepable is False
    assert folder.is_dirty is False
    assert folder.type == Folder.Type.ALBUM


def test_album_folder_dirty(infos2, mocker):
    """Test album folder."""
    mocker.patch.object(BeetsClient, "get_album_info", autospec=True)
    BeetsClient.get_album_info.return_value = infos2

    media = MediaFile(
        "1", "/music/artist/album/track.mp3", "title", 2003, 1, 33, 64, "1", "artist", "2", "album", "mbz3"
    )
    media.beets_path = "/music/artist/album/track.mp3"
    folder = Folder(media)
    assert folder.beets_path == "/music/artist/album"
    assert folder.has_keepable is False
    assert folder.is_dirty is True
    assert folder.type == Folder.Type.ALBUM
