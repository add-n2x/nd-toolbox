"""Test cases for the NavidromeDb class."""

from datetime import datetime

import pytest

from ndtoolbox.db import Annotation, NavidromeDb
from ndtoolbox.model import MediaFile
from ndtoolbox.utils import ToolboxConfig

# Example data to use for testing
TEST_DB_PATH = "test/data/navidrome.db"
TEST_USER_ID = "b67d5135-cf67-4544-8013-d0f7c2d8a65a"

test_media_file = MediaFile(
    id="111",
    path="/music/foobar/dummy1.mp3",
    title="Foo Bar",
    year=2005,
    track_number=3,
    duration=200,
    bitrate=160,
    artist_id=None,
    artist_name=None,
    album_id=None,
    album_name=None,
    mbz_recording_id=None,
)

test_anno = Annotation(
    item_type=Annotation.Type.media_file,
    item_id="111",
    play_count=1,
    play_date="2013-04-18 00:13:37",
    rating=0,
    starred=False,
    starred_at=None,
)


@pytest.fixture(scope="session")
def db():
    """Fixture to provide a database connection for tests."""
    ToolboxConfig()
    db = NavidromeDb(db_path=TEST_DB_PATH)
    yield db


def test_init_user(db):
    """Test the initialization of user ID."""
    # Verify that the user ID is correctly initialized
    assert db.user_id == TEST_USER_ID


def test_get_media(db, mocker):
    """Test the retrieval of a media file from the database."""
    # Mock the database query to return a specific media file and annotation
    mocker.patch.object(db, "get_media_file", autospec=True)
    db.get_media_file.return_value = test_media_file
    mocker.patch.object(db, "get_media_annotation")
    db.get_media_annotation.return_value = test_anno

    # Retrieve the media file from the database
    media_file = db.get_media(test_media_file.path)

    print(f"Media file: {media_file}")
    print(f"File annotation: {media_file.annotation}")

    # Verify that the media file is correctly retrieved and its attributes match the expected values
    assert media_file is not None
    assert media_file.id == test_media_file.id
    assert media_file.path == test_media_file.path
    assert media_file.title == test_media_file.title
    assert media_file.year == test_media_file.year
    assert media_file.track_number == test_media_file.track_number
    assert media_file.duration == test_media_file.duration
    assert media_file.bitrate == test_media_file.bitrate

    anno: Annotation = media_file.annotation
    assert anno.item_id == test_anno.item_id
    assert anno.play_count == test_anno.play_count
    assert anno.play_date == test_anno.play_date
    assert anno.rating == test_anno.rating
    assert anno.starred == test_anno.starred
    assert anno.starred_at is test_anno.starred_at


def test_get_invalid_annotation(db):
    """Test retrieving an invalid annotation."""
    # Attempt to retrieve an annotation that does not exist
    invalid_anno = db.get_annotation(1000, Annotation.Type.album)
    assert invalid_anno is None


def test_store_annotation(db: NavidromeDb):
    """Test storing an annotation."""
    # Delete any existing annotations with item_id 999
    db.delete_annotation("999", Annotation.Type.album)

    # Create a new annotation object
    new_anno = Annotation(
        item_id="999",
        item_type=Annotation.Type.album,
        play_count=5,
        play_date=datetime.now(),
        rating=4,
        starred=True,
        starred_at=datetime.now(),
    )
    # Store the annotation in the database
    db.store_annotation(new_anno)
    # Retrieve the stored annotation to verify it was saved correctly
    stored_anno = db.get_annotation("999", Annotation.Type.album)

    assert stored_anno is not None
    assert stored_anno.item_id == new_anno.item_id
    assert stored_anno.item_type == new_anno.item_type
    assert stored_anno.play_count == new_anno.play_count
    assert stored_anno.rating == new_anno.rating
    assert stored_anno.starred == new_anno.starred
    assert stored_anno.starred_at is not None
