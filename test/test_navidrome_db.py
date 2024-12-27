import pytest

from datetime import datetime
from ndtools.db import NavidromeDb, Annotation
from ndtools.utils import DotDict

# Example data to use for testing
TEST_DB_PATH = "config/navidrome/navidrome.db"
TEST_USER_ID = "b65d5135-ca67-4534-8014-d0f7c2d8e65a"

test_media_file = DotDict(
    {
        "path": "/music/library/Venetian Snares/rossz csillag allat szuletett/oengyilkos vasarnap.mp3",
        "id": "151e12ac667484745301625483d71399",
        "title": "Öngyilkos vasárnap",
        "year": 2005,
        "track_number": 3,
        "duration": 206.2100067138672,
        "bitrate": 160,
    }
)

test_anno = DotDict(
    {
        "id": "4ac94a1b-c33a-f613-34dc-75965fa54c55",
        "item_id": "151e12ac667484745301625483d71399",
        "play_count": 1,
        "play_date": "2013-04-18 00:33:37",
        "rating": 0,
        "starred": False,
        "starred_at": None,
    }
)


@pytest.fixture(scope="session")
def db():
    db = NavidromeDb(db_path=TEST_DB_PATH)
    yield db


def test_init_user(db):
    # Verify that the user ID is correctly initialized
    assert db.user_id == TEST_USER_ID


def test_generate_annotation_id():
    # Verify that generated IDs are strings and have the expected format
    annotation_id = NavidromeDb.generate_annotation_id()
    assert isinstance(annotation_id, str)
    assert len(annotation_id) == 36


def test_get_media(db):
    db = NavidromeDb(TEST_DB_PATH)
    media_file = db.get_media(test_media_file.path)

    print(f"Media file: {media_file}")
    print(f"File annotation: {media_file.annotation}")
    print(f"Artist annotation: {media_file.artist.annotation}")
    print(f"Album annotation: {media_file.album.annotation}")

    assert media_file is not None
    assert media_file.id == test_media_file.id
    assert media_file.path == test_media_file.path
    assert media_file.title == test_media_file.title
    assert media_file.year == test_media_file.year
    assert media_file.track_number == test_media_file.track_number
    assert media_file.duration == test_media_file.duration
    assert media_file.bitrate == test_media_file.bitrate

    anno: Annotation = media_file.annotation
    assert anno.id == test_anno.id
    assert anno.item_id == test_anno.item_id
    assert anno.play_count == test_anno.play_count
    assert anno.play_date == test_anno.play_date
    assert anno.rating == test_anno.rating
    assert anno.starred == test_anno.starred
    assert anno.starred_at is test_anno.starred_at


def test_get_invalid_annotation(db):
    # Attempt to retrieve an annotation that does not exist
    invalid_anno = db.get_annotation(1000, Annotation.Type.album)
    assert invalid_anno is None


def test_store_annotation(db):
    # Delete any existing annotations with item_id 999
    db.delete_annotation("999", Annotation.Type.album)

    # Create a new annotation object, without specifying an ID (let the DAO generate it)
    new_anno = Annotation(
        id=None,
        item_id="999",
        item_type=Annotation.Type.album,
        play_count=5,
        play_date=datetime.now(),
        rating=4,
        starred=True,
        starred_at=datetime.now(),
    )
    # Store the annotation in the database
    anno_id = db.store_annotation(new_anno)
    assert anno_id is not None
    # Retrieve the stored annotation to verify it was saved correctly
    stored_anno = db.get_annotation("999", Annotation.Type.album)

    assert stored_anno is not None
    assert stored_anno.item_id == new_anno.item_id
    assert stored_anno.item_type == new_anno.item_type
    assert stored_anno.play_count == new_anno.play_count
    assert stored_anno.rating == new_anno.rating
    assert stored_anno.starred == new_anno.starred
    assert stored_anno.starred_at is not None
