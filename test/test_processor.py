"""Test module for the DuplicateProcessor class."""

import pytest

from ndtoolbox.app import DuplicateProcessor
from ndtoolbox.model import Album, Annotation, MediaFile
from ndtoolbox.utils import ToolboxConfig

ND_DATABASE_PATH = "test/data/navidrome.db"
DATA_DIR = "test/data"
BEETS_BASE_PATH = "/app/music"
ND_BASE_PATH = "/music/library"


@pytest.fixture(scope="session")
def processor():
    """Fixture to create a DuplicateProcessor instance."""
    ToolboxConfig()
    processor = DuplicateProcessor(ND_DATABASE_PATH, DATA_DIR, BEETS_BASE_PATH, ND_BASE_PATH)
    yield processor


def test_merge_annotation_data(processor: DuplicateProcessor):
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
        artist_id=None,
        artist_name=None,
        album_id=None,
        album_name=None,
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
        artist_id=None,
        artist_name=None,
        album_id=None,
        album_name=None,
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


def test_merge_annotation_list(processor: DuplicateProcessor):
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
            artist_id=None,
            artist_name=None,
            album_id=None,
            album_name=None,
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
            artist_id=None,
            artist_name=None,
            album_id=None,
            album_name=None,
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
            artist_id=None,
            artist_name=None,
            album_id=None,
            album_name=None,
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
            artist_id=None,
            artist_name=None,
            album_id=None,
            album_name=None,
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


def test_get_keepable_media(processor: DuplicateProcessor):
    """
    Test get keepable media logic.

    1. Media file is in an album, which already contains another media file which is keepable.
    2. Media file has one of the preferred file extensions
    3. Media file has a MusicBrainz recording ID.
    4. Media file has an artist record available in the Navidrome database.
    5. Media file contains a album track number.
    6. Media file has a better bit rate than any of the other duplicate media files.
    7. Media file holds a release year.
    """
    dups = [
        MediaFile(
            id="11",
            path="/path/to/file1.mp3",
            title="File 1",
            year=None,
            track_number=None,
            duration=3600,
            bitrate=64,
            artist_id=0,
            artist_name=None,
            album_id=0,
            album_name=None,
            mbz_recording_id=None,
        ),
        MediaFile(
            id="12",
            path="/path/to/file2.mp3",
            title="File 2",
            year=1990,
            track_number=None,
            duration=3600,
            bitrate=64,
            artist_id=0,
            artist_name=None,
            album_id=0,
            album_name=None,
            mbz_recording_id=None,
        ),
        MediaFile(
            id="13",
            path="/path/to/file3.mp3",
            title="File 3",
            year=1990,
            track_number=None,
            duration=3600,
            bitrate=128,
            artist_id=0,
            artist_name=None,
            album_id=0,
            album_name=None,
            mbz_recording_id=None,
        ),
        MediaFile(
            id="14",
            path="/path/to/file4.mp3",
            title="File 4",
            year=1990,
            track_number=3,
            duration=3600,
            bitrate=360,
            artist_id=0,
            artist_name=None,
            album_id=0,
            album_name=None,
            mbz_recording_id=None,
        ),
        MediaFile(
            id="15",
            path="/path/to/file4.mp3",
            title="File 5",
            year=1990,
            track_number=3,
            duration=3600,
            bitrate=360,
            artist_id=0,
            artist_name=None,
            album_id=0,
            album_name=None,
            mbz_recording_id=None,
        ),
        MediaFile(
            id="16",
            path="/path/to/file4.mp3",
            title="File 6",
            year=1990,
            track_number=3,
            duration=3600,
            bitrate=320,
            artist_id=0,
            artist_name=None,
            album_id=0,
            album_name=None,
            mbz_recording_id="musicBrainzID",
        ),
        MediaFile(
            id="17",
            path="/path/to/file4.mp4",
            title="File 7",
            year=1990,
            track_number=3,
            duration=3600,
            bitrate=320,
            artist_id=0,
            artist_name=None,
            album_id=0,
            album_name=None,
            mbz_recording_id="musicBrainzID",
        ),
        # That's a keeper:
        MediaFile(
            id="18",
            path="/path/to/file4.mp3",
            title="File 8",
            year=1990,
            track_number=3,
            duration=3600,
            bitrate=320,
            artist_id=0,
            artist_name=None,
            album_id=0,
            album_name=None,
            mbz_recording_id="musicBrainzID",
        ),
    ]

    dups2 = [
        MediaFile(
            # That's a keeper:
            id="3000",
            path="/path/to/file4.mp3",
            title="The Song",
            year=1990,
            track_number=1,
            duration=3600,
            bitrate=1024,
            artist_id=0,
            artist_name=None,
            album_id=0,
            album_name=None,
            mbz_recording_id="musicBrainzID",
        ),
        MediaFile(
            id="2000",
            path="/path/to/file4.mp3",
            title="The Song (remastered)",
            year=1990,
            track_number=1,
            duration=3600,
            bitrate=1024,
            artist_id=0,
            artist_name=None,
            album_id=0,
            album_name=None,
            mbz_recording_id=None,
        ),
    ]

    album = Album(id="album-1", name="Album 1", artist_id="artist-1", song_count=13)
    # for dup in dups[4:-1]:
    dups[-1].album = album
    dups2[0].album = album

    # First, eval the 2nd list, to get the album marked with "has_keepable"
    keeper = processor._get_keepable_media(dups2)
    assert keeper.id == dups2[0].id
    assert keeper.album is not None
    assert keeper.album.has_keepable is True
    assert keeper.title == "The Song"
    assert keeper.bitrate == 1024

    # Now, eval the first list
    keeper = processor._get_keepable_media(dups)
    assert keeper.id == dups[7].id
    assert keeper.album is not None
    assert keeper.album.has_keepable is True
    assert keeper.title == "File 8"
    assert keeper.bitrate == 320
