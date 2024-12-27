import pytest

from ndtools.db import NavidromeDb
from ndtools.list import DuplicateProcessor
from ndtools.model import Annotation, MediaFile

TEST_DB_PATH = "config/navidrome/navidrome.db"
DIR_OUTPUT = "./output"
BEETS_BASE_PATH = "/app/music"
NAVIDROME_BASE_PATH = "/music/library"


@pytest.fixture(scope="session")
def db():
    db = NavidromeDb(db_path=TEST_DB_PATH)
    yield db


@pytest.fixture(scope="session")
def processor():
    processor = DuplicateProcessor(db, DIR_OUTPUT, BEETS_BASE_PATH, NAVIDROME_BASE_PATH)
    yield processor


def test_merge_annotation_data(processor):
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
    )
    a.annotation = Annotation(
        id="1a",
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
    )
    b.annotation = Annotation(
        id="2",
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
        ),
    ]
    # Set annotations for each file
    for f in files:
        f.annotation = Annotation(
            id=f"a{f.id}",
            item_id=f.id,
            item_type=Annotation.Type.media_file,
            play_count=f.id if int(f.id) > 1 else 0,  # File 1 has no play count, others have 2, 3 and 4 plays
            play_date="2023-01-01",
            rating=int(f.id),  # Ratings from 1 to 4
            starred=f.id == "2" or f.id == "4",  # Files 2 and 4 are starred
            starred_at="2022-01-01",
        )

    processor._merge_annotation_list(files)

    assert files[0].annotation.play_count == 9
    assert files[0].annotation.rating == 4
    assert files[0].annotation.starred
