"""Test utils module."""

from ndtoolbox.utils import StringUtil


def test_file_name_string_suffix():
    """Test the file name string suffix functionality."""
    assert StringUtil.equal_file_with_numeric_suffix("some_file.mp3", "some_file.mp3") is not True
    assert StringUtil.equal_file_with_numeric_suffix("some_file.mp3", "some_file1.mp3") is True
    assert StringUtil.equal_file_with_numeric_suffix("some_file.mp3", "some_file01.mp3") is True
    assert StringUtil.equal_file_with_numeric_suffix("some_file.mp3", "some_file 12.mp3") is True
    assert StringUtil.equal_file_with_numeric_suffix("some_file.mp3", "some_file 3.mp3") is True
