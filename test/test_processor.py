"""Test module for the DuplicateProcessor class."""

import copy
import datetime

import jsonpickle
import pytest

from ndtoolbox.app import DuplicateProcessor
from ndtoolbox.model import Album, Annotation, MediaFile
from ndtoolbox.utils import ToolboxConfig

ND_DATABASE_PATH = "test/data/navidrome.db"
ND_DATA_FILE = "data/nd-toolbox-data.json"
ND_DATA_FILE = "test/data/nd-toolbox-data.json"
DATA_DIR = "test/data"
BEETS_BASE_PATH = "/app/music"
ND_BASE_PATH = "/music/library"

FILES = [
    MediaFile(
        id="11",
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
        id="22",
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
        id="33",
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
        id="44",
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
for f in FILES:
    f.annotation = Annotation(
        item_id=f.id,
        item_type=Annotation.Type.media_file,
        play_count=f.id if int(f.id) > 20 else 0,  # File 1 has no play count, others have 22, 33 and 44 plays
        play_date="2023-01-01",
        rating=int(int(f.id) / 10),  # Ratings from 1 to 4
        starred=f.id == "22" or f.id == "44",  # Files 2 and 4 are starred
        starred_at="2022-01-01",
    )


@pytest.fixture(scope="session")
def processor():
    """Fixture to create a DuplicateProcessor instance."""
    ToolboxConfig(False)
    processor = DuplicateProcessor(ND_DATABASE_PATH, DATA_DIR, BEETS_BASE_PATH, ND_BASE_PATH)
    yield processor


def test_encode_decode_json_pickle(processor: DuplicateProcessor):
    """Test encoding and decoding of JSON using jsonpickle."""
    file_path = "test/data/test-data.json"
    data = {"dups_media_files": FILES, "stats": "bbb", "errors": []}
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(jsonpickle.encode(data, indent=4, keys=True))


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
        play_date="2023-02-02",
        rating=3,
        starred=False,
        starred_at=None,
    )

    c = MediaFile(
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
        mbz_recording_id="recording-2",
    )
    c.annotation = Annotation(
        item_id="3",
        item_type=Annotation.Type.media_file,
        play_count=None,
        play_date=None,
        rating=None,
        starred=None,
        starred_at="2025-05-07",
    )

    dups = [a, b, c]
    (play_count, play_date, rating, starred, starred_at) = processor._get_merged_annotation(dups)

    assert play_count == 10
    assert play_date == datetime.datetime(2023, 2, 2, 0, 0)
    assert rating == 5
    assert starred is True
    assert starred_at == datetime.datetime(2025, 5, 7, 0, 0)


def test_merge_annotation_list(processor: DuplicateProcessor):
    """Test the merge_annotation_list method."""
    # Create a list of four Media files with annotations
    files = copy.copy(FILES)

    # Set up the processor with the test files
    processor._merge_annotation_list({"key123": files})

    for f in files:
        print("Play count: " + str(f.annotation.play_count))
        assert f.annotation.play_count == 44
        assert f.annotation.rating == 4
        assert f.annotation.starred is True


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
