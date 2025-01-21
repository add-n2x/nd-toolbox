"""Test module for the DuplicateProcessor class."""

import copy
import datetime

import jsonpickle
import pytest

from ndtoolbox.app import DuplicateProcessor
from ndtoolbox.config import config
from ndtoolbox.model import Album, Annotation, Artist, MediaFile

config.set_file("test/config/config.yaml")

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
        beets_path="/music/path/library/to/file1.mp3",
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
        beets_path="/music/path/library/to/file2 2.mp3",
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
        beets_path="/music/path/library/to/file3.mp3",
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
        beets_path="/music/path/library/to/file4.mp3",
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
    processor = DuplicateProcessor()
    yield processor


def test_encode_decode_json_pickle(processor: DuplicateProcessor):
    """Test encoding and decoding of JSON using jsonpickle."""
    file_path = "test/data/test-data.json"
    data = {"duplicates": FILES, "stats": "bbb", "errors": []}
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
        beets_path="/music/path/library/to/file1.mp3",
    )
    a.annotation = Annotation(
        item_id="1",
        item_type=Annotation.Type.media_file,
        play_count=5,
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
        beets_path="/music/path/library/to/file1.mp3",
    )
    b.annotation = Annotation(
        item_id="2",
        item_type=Annotation.Type.media_file,
        play_count=10,
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
        beets_path="/music/path/library/to/file3.mp3",
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

    assert a.annotation.play_count == 5
    assert b.annotation.play_count == 10
    assert c.annotation.play_count == 0
    assert a.annotation.rating == 5
    assert b.annotation.rating == 3
    assert c.annotation.rating == 0
    assert a.annotation.starred is True
    assert b.annotation.starred is False
    assert c.annotation.starred is False
    assert a.annotation.starred_at == datetime.datetime(2022, 1, 1, 0, 0)
    assert b.annotation.starred_at is None
    assert c.annotation.starred_at == datetime.datetime(2025, 5, 7, 0, 0)
    assert a.annotation.play_date == datetime.datetime(2023, 1, 1, 0, 0)
    assert b.annotation.play_date == datetime.datetime(2023, 2, 2, 0, 0)
    assert c.annotation.play_date is None

    # Merge annotations
    dups = [a, b, c]
    (play_count, play_date, rating, starred, starred_at) = processor._get_merged_annotation(dups)

    assert play_count == 10
    assert play_date == datetime.datetime(2023, 2, 2, 0, 0)
    assert rating == 5
    assert starred is True
    assert starred_at == datetime.datetime(2025, 5, 7, 0, 0)

    # Calling the merge several times should keep the same annotation data
    (play_count, play_date, rating, starred, starred_at) = processor._get_merged_annotation(dups)
    (play_count, play_date, rating, starred, starred_at) = processor._get_merged_annotation(dups)

    assert play_count == 10
    assert play_date == datetime.datetime(2023, 2, 2, 0, 0)
    assert rating == 5
    assert starred is True
    assert starred_at == datetime.datetime(2025, 5, 7, 0, 0)

    processor._merge_annotation_list(dups)

    assert a.annotation.play_count == 10
    assert b.annotation.play_count == 10
    assert c.annotation.play_count == 10
    assert a.annotation.rating == 5
    assert b.annotation.rating == 5
    assert c.annotation.rating == 5
    assert a.annotation.starred is True
    assert b.annotation.starred is True
    assert c.annotation.starred is True
    assert a.annotation.starred_at == datetime.datetime(2025, 5, 7, 0, 0)
    assert b.annotation.starred_at == datetime.datetime(2025, 5, 7, 0, 0)
    assert c.annotation.starred_at == datetime.datetime(2025, 5, 7, 0, 0)


def test_merge_annotation_list(processor: DuplicateProcessor):
    """Test the merge_annotation_list method."""
    # Create a list of four Media files with annotations
    files = copy.copy(FILES)

    # Set up the processor with the test files
    processor._merge_annotation_list(files)

    for f in files:
        print("Play count: " + str(f.annotation.play_count))
        assert f.annotation.play_count == 44
        assert f.annotation.rating == 4
        assert f.annotation.starred is True


def test_get_keepable_media(processor: DuplicateProcessor):
    """
    Test get keepable media logic.

    1. Media file is in an album, which already contains another media file which is keepable.
    1. Media files have equal filenames, but one has a numeric suffix, e.g., "song.mp3" and "song1.mp3".
        The one with the numeric suffix is considered less important and will be removed.
    1. Media file title and filename are compared with fuzzy search. Higher ratio is a keeper.
    1. Media file has one of the preferred file extensions
    1. Media file has a MusicBrainz recording ID.
    1. Media file has an artist record available in the Navidrome database.
    1. Media file has an album record available in the Navidrome database.
    1. Media file contains a album track number.
    1. Media file has a better bit rate than any of the other duplicate media files.
    1. Media file holds a release year.
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
            beets_path="/music/path/library/to/file1.mp3",
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
            beets_path="/music/path/library/to/file1.mp3",
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
            beets_path="/music/path/library/to/file3.mp3",
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
            beets_path="/music/path/library/to/file4.mp3",
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
            beets_path="/music/path/library/to/file4.mp3",
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
            beets_path="/music/path/library/to/file4.mp3",
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
            beets_path="/music/path/library/to/file4.mp3",
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
            beets_path="/music/path/library/to/file4.mp3",
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
            beets_path="/music/path/library/to/file4.mp3",
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
            beets_path="/music/path/library/to/file4.mp3",
        ),
    ]

    dups3 = [
        MediaFile(
            # That's a keeper:
            id="no_artist_media",
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
            mbz_recording_id=None,
            beets_path="/music/path/library/to/file4.mp3",
        ),
        MediaFile(
            id="artist_keeper_id",
            path="/path/to/The Song (remastered).mp3",
            title="The Song (remastered)",
            year=None,
            track_number=1,
            duration=3600,
            bitrate=1024,
            artist_id=0,
            artist_name=None,
            album_id=0,
            album_name=None,
            mbz_recording_id=None,
            beets_path="/music/path/library/to/file4.mp3",
        ),
    ]

    artist = Artist(id="artist-1", name="Artist 1", album_count=33)
    dups[-2].artist = artist
    dups3[-1].artist = artist

    album = Album(id="album-1", name="Album 1", artist_id="artist-1", song_count=13, mbz_album_id="mbz-album")
    # for dup in dups[4:-1]:
    dups[-1].album = album
    dups2[0].album = album

    # First, eval the 2nd list, to get the album marked with "has_keepable"
    keeper = processor._get_keepable_media(dups2)
    assert keeper.id == dups2[0].id
    assert keeper.album is not None
    assert keeper.folder is not None
    assert keeper.folder.has_keepable is True
    assert keeper.title == "The Song"
    assert keeper.bitrate == 1024

    # Now, eval the first list
    keeper = processor._get_keepable_media(dups)
    assert keeper.id == dups[7].id
    assert keeper.album is not None
    assert keeper.folder is not None
    assert keeper.folder.has_keepable is True
    assert keeper.title == "File 8"
    assert keeper.bitrate == 320

    # Eval the thirt list
    keeper = processor._get_keepable_media(dups3)
    assert keeper.id == "artist_keeper_id"
    assert keeper.artist is not None
