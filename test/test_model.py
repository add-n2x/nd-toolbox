"""Test models."""

from typing import Generator

import pytest
from easydict import EasyDict

from ndtoolbox.client import BeetsClient, beets_client
from ndtoolbox.config import config
from ndtoolbox.model import Folder, MediaFile

config.set_file("test/config/config.yaml")


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


@pytest.fixture(scope="session")
def query_result():
    """Fixture to provide Beets subprocess output."""
    result = [
        ":::0:::-3:::False",
        "Tschuldigung.:::11:::10:::False",
        "Herz für die Sache:::0:::-94:::True",
        "Keine Macht für Niemand:::16:::11:::True",
        "Tschuldigung.:::11:::8:::True",
    ]
    return result


def test_album_folder(infos, mocker):
    """Test album folder."""
    Folder.clear_cache()
    mocker.patch.object(BeetsClient, "get_album_info", autospec=True)
    BeetsClient.get_album_info.return_value = infos

    media = MediaFile(
        "1",
        "/music/artist/album/track.mp3",
        "title",
        2003,
        1,
        33,
        64,
        "1",
        "artist",
        "2",
        "album",
        "mbz3",
        beets_path="/music/artist/album/track.mp3",
    )
    folder = Folder.of_media(media)
    assert folder.beets_path == "/music/artist/album"
    assert folder.has_keepable is False
    assert folder.is_dirty is False
    assert folder.type == Folder.Type.ALBUM


def test_album_folder_dirty(infos2, mocker):
    """Test album folder."""
    Folder.clear_cache()
    mocker.patch.object(BeetsClient, "get_album_info", autospec=True)
    BeetsClient.get_album_info.return_value = infos2

    media = MediaFile(
        "1",
        "/music/library/artist/album23/track.mp3",
        "title",
        2003,
        1,
        33,
        64,
        "1",
        "artist",
        "2",
        "album",
        "mbz3",
        beets_path="/music/artist/album23/track.mp3",
    )
    folder = media.folder
    assert folder.beets_path == "/music/artist/album23"
    assert folder.has_keepable is False
    assert folder.is_dirty is True
    assert folder.type == Folder.Type.UNKNOWN


def test_album_folder_dirty_query(query_result, mocker):
    """Test mayday folder."""
    Folder.clear_cache()
    mocker.patch.object(beets_client, "query", autospec=True)
    beets_client.query.return_value = query_result

    media = MediaFile(
        "1",
        "/music/library/artist/album1144/track.mp3",
        "title",
        2003,
        1,
        33,
        64,
        "1",
        "artist",
        "2",
        "album",
        "mbz3",
        beets_path="/music/artist/album1144/track.mp3",
    )
    folder = media.folder
    assert folder.beets_path == "/music/artist/album1144"
    assert folder.has_keepable is False
    assert folder.is_dirty is True
    assert folder.type == Folder.Type.UNKNOWN
