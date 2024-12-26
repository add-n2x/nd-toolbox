from unittest import TestCase
from ndtools.db import NavidromeDb
from ndtools.list import DuplicateProcessor
from ndtools.model import Annotation, MediaFile

TEST_DB_PATH = "config/navidrome/navidrome.db"
DIR_OUTPUT = "./output"


class TestProcessor(TestCase):
    def setUp(self):
        db = NavidromeDb(TEST_DB_PATH)
        self.processor = DuplicateProcessor(db, DIR_OUTPUT)

    def test_merge_annotation_data(self):
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
        self.processor.merge_annotation_data(a, b)
        # Check if the annotation data has been merged correctly
        self.assertEqual(a.annotation.play_count, 15)
        # Check if the play_date is updated to the latest date
        self.assertEqual(a.annotation.play_date, "2023-01-02")
        # Check if the rating is updated to the highest rating
        self.assertEqual(a.annotation.rating, 5)
        # Check if both files are starred if either one was starred
        self.assertTrue(a.annotation.starred)
        self.assertTrue(b.annotation.starred)
