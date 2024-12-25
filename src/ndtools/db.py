"""
Navidrome database classes.
"""

import datetime
import random
import sqlite3
import string
from utils import PrintUtils as PU

from model import Album, Annotation, Artist, MediaFile


class NavidromeDbConnection(object):
    """Navidrome database connection."""

    db_path = None
    conn: sqlite3.Connection
    debug: bool

    def __init__(self, debug=False):
        self.debug = debug

    def __enter__(self):
        """
        Open a new database connection and get a cursor.

        Returns:
            Connection: Connection to the database.
        """
        self.conn = sqlite3.connect(self.db_path)
        # print("Connected to database at:", self.db_path)
        if self.debug:
            self.conn.set_trace_callback(print)
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Close the database connection.

        Args:
            exc_type (type): Type of exception that occurred.
            exc_val (value): Value of the exception that occurred.
            exc_tb (traceback): Traceback object of the exception that occurred.
        """
        self.conn.close()


class NavidromeDb:
    """
    Navidrome database class.

    Provides methods to interact with the Navidrome database.

    Access to artists and albums is cached.
    """

    db_path: str = None
    user_id: str
    artists: dict
    albums: dict

    def __init__(self, db_path: str):
        """
        Initialize the database connection and set the user ID.

        Args:
            db_path (str): Path to the database file.
        """
        NavidromeDbConnection.db_path = db_path
        self.user_id = self.init_user()

        self.artists = {}
        self.albums = {}

    def init_user(self) -> str:
        """
        Initialize the user ID for the database operations.

        Returns:
           str: The ID of the retrieved Navidrome user.
        """
        with NavidromeDbConnection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, user_name FROM user")
            users = cur.fetchall()
            if len(users) == 1:
                PU.green(f"Using Navidrome account '{users[0][1]}'.")
            else:
                raise Exception(
                    """
                    There needs to be exactly one user account set up with Navidrome.
                    You either have 0, or more than 1 user account.
                    """
                )

            return users[0][0]

    # def update_playstats(d1, id, playcount, playdate, rating=0):
    #     d1.setdefault(id, {})
    #     d1[id].setdefault("play count", 0)
    #     d1[id].setdefault("play date", datetime.datetime.fromordinal(1))
    #     d1[id]["play count"] += playcount
    #     d1[id]["rating"] = rating

    #     if playdate > d1[id]["play date"]:
    #         d1[id].update({"play date": playdate})

    # def write_to_annotation(self, dictionary_with_stats, entry_type):
    #     annotation_entries = []
    #     for item_id in dictionary_with_stats:
    #         this_entry = dictionary_with_stats[item_id]

    #         play_count = this_entry["play count"]
    #         play_date = this_entry["play date"].strftime("%Y-%m-%d %H:%M:%S")  # YYYY-MM-DD 24:mm:ss
    #         rating = this_entry["rating"]

    #         annotation_entries.append(
    #             (
    #                 NavidromeDb.generate_annotation_id(),
    #                 self.user_id,
    #                 item_id,
    #                 entry_type,
    #                 play_count,
    #                 play_date,
    #                 rating,
    #                 0,
    #                 None,
    #             )
    #         )
    #     with NavidromeDbConnection() as conn:
    #         cur = conn.cursor()
    #         cur.executemany(
    #             "INSERT INTO annotation VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
    #             annotation_entries,
    #         )
    #         conn.commit()

    def get_media(self, file_path: str) -> MediaFile:
        """
        Retrieves the media file associated with the given file path.

        This method also fetches artist and album and any annotations available.
        If artist and album objects are available in the cache, then those are used.

        Args:
            file_path (str): The path to the media file.

        Returns:
            MediaFile: The media file object.
        """
        media = self._get_media_file(file_path)
        if media:
            # Get file annotation
            media.annotation = self._get_media_annotations(media, Annotation.Type.media_file)
            # Get artist data
            media.artist = self.artists.get(media.artist_id)
            media.artist = self._get_artist(media, media.artist_id) if not media.artist else media.artist
            if media.artist:
                self.artists[media.artist_id] = media.artist
            # Get album data
            media.album = self.albums.get(media.album_id)
            media.album = self._get_album(media, media.album_id) if not media.album else media.album
            if media.album:
                self.albums[media.album_id] = media.album
        return media

    def _get_media_file(self, file_path: str) -> MediaFile:
        query = """
            SELECT id, title, year, track_number, duration, bit_rate, artist_id, album_id
            FROM media_file
            WHERE path LIKE ?
        """
        with NavidromeDbConnection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (file_path,))
            result = cursor.fetchone()

            if not result:
                return None
            return MediaFile(
                result[0], file_path, result[1], result[2], result[3], result[4], result[5], result[6], result[7]
            )

    def _get_artist(self, media_file: MediaFile, artist_id: str) -> Artist:
        query = """
            SELECT name, album_count
            FROM artist
            WHERE id LIKE ?
        """
        with NavidromeDbConnection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (artist_id,))
            result = cursor.fetchone()

            if not result:
                return None
            artist = Artist(id, result[0], result[1])
            artist.annotation = self._get_media_annotations(media_file, Annotation.Type.artist)
            return artist

    def _get_album(self, media_file: MediaFile, album_id: str) -> Album:
        query = """
            SELECT name, artist_id, song_count
            FROM album
            WHERE id LIKE ?
        """
        with NavidromeDbConnection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (album_id,))
            result = cursor.fetchone()

            if not result:
                return None
            album = Album(album_id, result[0], result[1], result[2])
            album.annotation = self._get_media_annotations(media_file, Annotation.Type.album)
            return album

    def _get_media_annotations(self, media_file: MediaFile, type: Annotation.Type) -> Annotation:
        """
        Get media annotations for a given media file.

        Args:
            media_file (MediaFile): The media file object.
            type (Annotation.Type): The type of the annotation.

        Returns:
           Annotation: The annotation object for the given media file and type, if existing.
        """
        item_id = media_file.__getattribute__(type.value)
        query = """
            SELECT ann_id, play_count, play_date, rating, starred, starred_at 
            FROM annotation 
            WHERE user_id LIKE ? and item_id LIKE ? and item_type LIKE ?
        """

        with NavidromeDbConnection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (self.user_id, str(item_id), str(type.name)))
            result = cursor.fetchone()

            if not result:
                return None
            return Annotation(result[0], item_id, type, result[1], result[2], result[3], result[4], result[5])

    @staticmethod
    def generate_annotation_id() -> str:
        """
        Generates a random UUID-like string. This is used to create unique identifiers for annotations.

        Returns:
            str: UUID-like string.
        """
        character_pool = string.hexdigits[:16]

        id_elements = []
        for char_count in (8, 4, 4, 4, 12):
            id_elements.append("".join(random.choice(character_pool) for i in range(char_count)))
        return "-".join(id_elements)
