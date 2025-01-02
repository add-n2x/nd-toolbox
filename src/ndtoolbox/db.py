"""
Navidrome database classes.
"""

import sqlite3

from ndtoolbox.model import Album, Annotation, Artist, MediaFile
from ndtoolbox.utils import DateUtil as DU
from ndtoolbox.utils import PrintUtils as PU


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
                PU.info(f"Using Navidrome account '{users[0][1]}'.")
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
            # If no annotation exists, create one
            if not media.annotation:
                media.annotation = Annotation(
                    item_id=media.id,
                    item_type=Annotation.Type.media_file,
                    play_count=0,
                    play_date=None,
                    rating=0,
                    starred=False,
                    starred_at=None,
                )
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
            SELECT id, title, year, track_number, duration, bit_rate, artist_id, artist, album_id, album, mbz_recording_id
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
                result[0],
                file_path,
                result[1],
                result[2],
                result[3],
                result[4],
                result[5],
                result[6],
                result[7],
                result[8],
                result[9],
                result[10],
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
        result = None
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
        # If no annotation exists, create one
        if not artist.annotation:
            artist.annotation = Annotation(
                item_id=artist.id,
                item_type=Annotation.Type.artist,
                play_count=0,
                play_date=None,
                rating=0,
                starred=False,
                starred_at=None,
            )
        return artist

    def get_album(self, media_file: MediaFile, album_id: str) -> Album:
        """
        Retrieve an album associated with the media file.
        """
        result = None
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
        # If no annotation exists, create one
        if not album.annotation:
            album.annotation = Annotation(
                item_id=album.id,
                item_type=Annotation.Type.album,
                play_count=0,
                play_date=None,
                rating=0,
                starred=False,
                starred_at=None,
            )
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
            SELECT play_count, play_date, rating, starred, starred_at
            FROM annotation
            WHERE user_id LIKE ? and item_id LIKE ? and item_type LIKE ?
        """

        with NavidromeDbConnection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (self.user_id, str(item_id), str(type.name)))
            result = cursor.fetchone()

            if not result:
                return None
            return Annotation(
                item_id,
                type,
                result[0],
                DU.parse_date(result[1]),
                result[2],
                result[3],
                DU.parse_date(result[4]),
            )

    def store_annotation(self, annotation: Annotation):
        """
        Adds an annotation to the database. If the annotation already exists, it will be updated.

        Args:
            annotation (Annotation): The annotation object to be added or updated.
        """
        # Dates are in the format `YYYY-MM-DD 24:mm:ss`
        pd = DU.format_date(annotation.play_date)
        starred_at = DU.format_date(annotation.starred_at)

        query = """
            INSERT OR REPLACE INTO 
            annotation (user_id, item_id, item_type, play_count, play_date, rating, starred, starred_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        args = (
            self.user_id,
            annotation.item_id,
            annotation.item_type.name,
            annotation.play_count,
            pd,
            annotation.rating,
            annotation.starred,
            starred_at,
        )

        with NavidromeDbConnection() as conn:
            cur = conn.cursor()
            cur.execute(
                query,
                args,
            )
            conn.commit()

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
