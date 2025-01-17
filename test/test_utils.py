"""Test utils module."""

from datetime import datetime

from ndtoolbox.utils import DateUtil, FileUtil


def test_file_name_string_suffix():
    """Test the file name string suffix functionality."""
    assert FileUtil.equal_file_with_numeric_suffix("some_file.mp3", "some_file.mp3") is not True
    assert FileUtil.equal_file_with_numeric_suffix("some_file.mp3", "some_file1.mp3") is True
    assert FileUtil.equal_file_with_numeric_suffix("some_file.mp3", "some_file01.mp3") is True
    assert FileUtil.equal_file_with_numeric_suffix("some_file.mp3", "some_file 12.mp3") is True
    assert FileUtil.equal_file_with_numeric_suffix("some_file.mp3", "some_file 3.mp3") is True


def test_is_artist_folder():
    """Test the is_artist_folder functionality."""
    base_path = "/path/to/base"
    artist_path = "/path/to/base/artist_name"
    assert FileUtil.is_artist_folder(base_path, artist_path) is True
    artist_path = "/path/to/base/artist_name/album_name"
    assert FileUtil.is_artist_folder(base_path, artist_path) is False
    artist_path = "/path/to/other_base/artist_name"
    assert FileUtil.is_artist_folder(base_path, artist_path) is False


def test_is_album_folder():
    """Test the is_album_folder functionality."""
    base_path = "/path/to/base"
    album_path = "/path/to/base/artist_name/album_name"
    assert FileUtil.is_album_folder(base_path, album_path) is True
    album_path = "/path/to/base/artist_name"
    assert FileUtil.is_album_folder(base_path, album_path) is False
    album_path = "/path/to/other_base/artist_name/album_name"
    assert FileUtil.is_album_folder(base_path, album_path) is False


def test_date_util():
    """Test the date utility functions."""
    now = datetime.now()
    s = DateUtil.format_date(now)
    assert isinstance(s, str)
    assert s == now.strftime("%Y-%m-%d %H:%M:%S")
    now2 = DateUtil.parse_date(s)
    assert now.date() == now2.date()
