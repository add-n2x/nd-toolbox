"""Test module for the DuplicateProcessor class."""

import pytest

from ndtoolbox.app import DuplicateProcessor
from ndtoolbox.model import Annotation, MediaFile

DIR_OUTPUT = "./output"
BEETS_BASE_PATH = "/app/music"
NAVIDROME_BASE_PATH = "/music/library"
CONFIG_DIR = "config"


@pytest.fixture(scope="session")
def processor():
    """Fixture to create a DuplicateProcessor instance."""
    processor = DuplicateProcessor(CONFIG_DIR, DIR_OUTPUT, BEETS_BASE_PATH, NAVIDROME_BASE_PATH)
    yield processor


def test_merge_annotation_data(processor):
    """Test merging annotation data from two MediaFile objects."""
    # Create two MediaFile objects with some annotation data
    a = MediaFile(
        id="1",
        path="/path/to/file1.mp3",
        title="File 1",
        year=1993,
        track_number=3,
        duration=3600,
        bitrate=320,
        artist_id=0,
        album_id=0,
        mbz_recording_id="recording-1",
    )
    a.annotation = Annotation(
        item_id="1",
        item_type=Annotation.Type.media_file,
        play_count=10,
        play_date="2023-01-01",
        rating=5,
        starred=True,
        starred_at="2022-01-01",
    )

    b = MediaFile(
        id="2",
        path="/path/to/file2.mp3",
        title="File 2",
        year=1993,
        track_number=3,
        duration=3600,
        bitrate=320,
        artist_id=0,
        album_id=0,
        mbz_recording_id="recording-2",
    )
    b.annotation = Annotation(
        item_id="2",
        item_type=Annotation.Type.media_file,
        play_count=5,
        play_date="2023-01-02",
        rating=4,
        starred=False,
        starred_at=None,
    )

    # Call the merge_annotation_data method
    processor._merge_annotation_data(a, b)
    assert a.annotation.play_count == 15
    assert a.annotation.play_date == "2023-01-02"
    assert a.annotation.rating == 5
    assert a.annotation.starred
    assert b.annotation.starred


def test_merge_annotation_list(processor):
    """Test the merge_annotation_list method."""
    # Create a list of four Media files with annotations
    files = [
        MediaFile(
            id="1",
            path="/path/to/file1.mp3",
            title="File 1",
            year=1993,
            track_number=3,
            duration=3600,
            bitrate=320,
            artist_id=0,
            album_id=0,
            mbz_recording_id="recording-1",
        ),
        MediaFile(
            id="2",
            path="/path/to/file2.mp3",
            title="File 2",
            year=1993,
            track_number=3,
            duration=3600,
            bitrate=320,
            artist_id=0,
            album_id=0,
            mbz_recording_id="recording-2",
        ),
        MediaFile(
            id="3",
            path="/path/to/file3.mp3",
            title="File 3",
            year=1993,
            track_number=3,
            duration=3600,
            bitrate=320,
            artist_id=0,
            album_id=0,
            mbz_recording_id="recording-3",
        ),
        MediaFile(
            id="4",
            path="/path/to/file4.mp3",
            title="File 4",
            year=1993,
            track_number=3,
            duration=3600,
            bitrate=320,
            artist_id=0,
            album_id=0,
            mbz_recording_id="recording-3",
        ),
    ]
    # Set annotations for each file
    for f in files:
        f.annotation = Annotation(
            item_id=f.id,
            item_type=Annotation.Type.media_file,
            play_count=f.id if int(f.id) > 1 else 0,  # File 1 has no play count, others have 2, 3 and 4 plays
            play_date="2023-01-01",
            rating=int(f.id),  # Ratings from 1 to 4
            starred=f.id == "2" or f.id == "4",  # Files 2 and 4 are starred
            starred_at="2022-01-01",
        )

    # Set up the processor with the test files
    processor.dups_media_files = {"key123": files}
    processor._merge_annotation_list()

    assert files[0].annotation.play_count == 9
    assert files[0].annotation.rating == 4
    assert files[0].annotation.starred
