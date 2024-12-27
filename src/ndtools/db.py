"""
Navidrome database classes.
"""

import random
import sqlite3
import string

from ndtools.model import Album, Annotation, Artist, MediaFile
from ndtools.utils import PrintUtils as PU


class NavidromeDbConnection(object):
    """Navidrome database connection."""

    db_path = None
    conn: sqlite3.Connection
    debug: bool

    def __init__(self, debug=False):
        """Init instance."""
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

    def get_media(self, file_path: str) -> MediaFile:
        """
        Retrieves the media file associated with the given file path and all related objects.

        This method also fetches artist and album and any annotations available.
        If artist and album objects are available in the cache, then those are used.

        Args:
            file_path (str): The path to the media file.

        Returns:
            MediaFile: The media file object.
        """
        media = self.get_media_file(file_path)
        if media:
            # Get file annotation
            media.annotation = self.get_media_annotation(media, Annotation.Type.media_file)
            # Get artist data
            media.artist = self.artists.get(media.artist_id)
            media.artist = self.get_artist(media, media.artist_id) if not media.artist else media.artist
            if media.artist:
                self.artists[media.artist_id] = media.artist
            # Get album data
            media.album = self.albums.get(media.album_id)
            media.album = self.get_album(media, media.album_id) if not media.album else media.album
            if media.album:
                self.albums[media.album_id] = media.album
        return media

    def get_media_file(self, file_path: str) -> MediaFile:
        """
        Retrieve a media file from the database based on its path.

        Args:
            file_path (str): The path of the media file to retrieve.
        """
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

    def get_artist(self, media_file: MediaFile, artist_id: str) -> Artist:
        """
        Retrieve an artist from the database based on their ID.

        Args:
           media_file (MediaFile): The media file associated with the artist.
           artist_id (str): The ID of the artist to retrieve.

        Returns:
            Artist: The retrieved artist object. If the artist is not found, returns None.
        """
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
            artist.annotation = self.get_media_annotation(media_file, Annotation.Type.artist)
            return artist

    def get_album(self, media_file: MediaFile, album_id: str) -> Album:
        """
        Retrieve an album associated with the media file.
        """
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
            album.annotation = self.get_media_annotation(media_file, Annotation.Type.album)
            return album

    def get_media_annotation(self, media_file: MediaFile, type: Annotation.Type) -> Annotation:
        """
        Get media annotation for a given media file and type.

        Args:
            media_file (MediaFile): The media file object holding the relevant item id.
            type (Annotation.Type): The type of the annotation, used for querying the item type.

        Returns:
            Annotation: The annotation object for the given media file and type, if existing.
        """
        item_id: str = media_file.__getattribute__(type.value)
        return self.get_annotation(item_id, type)

    def get_annotation(self, item_id: str, type: Annotation.Type) -> Annotation:
        """
        Get annotation for a given item and type.

        Args:
            item_id (str): The id of the item to get annotations for.
            type (Annotation.Type): The type of the annotation, used for querying the item type.

        Returns:
           Annotation: The annotation object for the given media file and type, if existing.
        """
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

    def store_annotation(self, annotation: Annotation) -> str:
        """
        Adds an annotation to the database. If the annotation already exists, it will be updated.

        Args:
            annotation (Annotation): The annotation object to be added or updated.

        Returns:
           str: The ID of the stored annotation. If an existing annotation was updated, it will return the same ID.
        """
        query = None
        args = None
        pd = annotation.play_date.strftime("%Y-%m-%d %H:%M:%S") if annotation.play_date else None  # YYYY-MM-DD 24:mm:ss
        starred_at = annotation.starred_at.strftime("%Y-%m-%d %H:%M:%S") if annotation.starred_at else None

        if annotation.id:
            query = "UPDATE annotation SET play_count = ?, play_date = ?, rating = ?, starred = ?, starred_at = ? WHERE user_id = ? AND item_id = ? AND item_type = ?"
            args = (
                annotation.play_count,
                pd,
                annotation.rating,
                annotation.starred,
                starred_at,
                self.user_id,
                annotation.item_id,
                annotation.item_type.name,
            )
        else:
            annotation.id = self.generate_annotation_id()
            # Annotation columns: ann_id, user_id, item_id, item_type, play_count, play_date, rating, starred, starred_at
            query = """
                INSERT INTO annotation (ann_id, user_id, item_id, item_type, play_count, play_date, rating, starred, starred_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            args = (
                annotation.id,
                self.user_id,
                annotation.item_id,
                annotation.item_type.name,
                annotation.play_count,
                pd,
                annotation.rating,
                annotation.starred,
                starred_at,
            )

        with NavidromeDbConnection(debug=True) as conn:
            cur = conn.cursor()
            cur.execute(
                query,
                args,
            )
            conn.commit()
        return annotation.id

    def delete_annotation(self, item_id: int, item_type: Annotation.Type):
        """
        Delete an annotation identified by item_id, item_type and user_id.

        Args:
            item_id (int): The ID of the item associated with the annotation.
            item_type (Annotation.Type): The type of the item associated with the annotation.
        """
        with NavidromeDbConnection() as conn:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM annotation WHERE item_id=? AND item_type=? AND user_id=?",
                (item_id, item_type.name, self.user_id),
            )
            conn.commit()

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
