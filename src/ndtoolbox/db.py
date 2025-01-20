"""
Navidrome database classes.
"""

import sqlite3
from typing import TYPE_CHECKING, Generator

from ndtoolbox.model import Album, Annotation, Artist, Folder, MediaFile
from ndtoolbox.utils import DateUtil as DU
from ndtoolbox.utils import FileUtil
from ndtoolbox.utils import PrintUtil as PU

if TYPE_CHECKING:
    from ndtoolbox.app import DataCache


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

    db_path: str
    cache: "DataCache"
    user_id: str
    conn: NavidromeDbConnection

    def __init__(self, db_path: str, cache: "DataCache"):
        """
        Initialize the database connection and set the user ID.

        Args:
            db_path (str): Path to the database file.
            cache (DataCache): Cache for data already queried.
        """
        NavidromeDbConnection.db_path = db_path
        self.cache = cache
        self.user_id = self.init_user()

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

    def get_media(self, file_path: str, conn: NavidromeDbConnection) -> MediaFile:
        """
        Retrieves the media file associated with the given file path and all related objects.

        This method also fetches artist and album and any annotations available.
        If artist and album objects are available in the cache, then those are used.

        Args:
            file_path (str): The path to the media file.
            conn (NavidromeDbConnection): The database connection to use.

        Returns:
            MediaFile: The media file object.
        """
        media = self.get_media_file(file_path, conn)
        if media:
            # Get file annotation
            media.annotation = self.get_media_annotation(media, Annotation.Type.media_file, conn)
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
            media.artist = self.cache.artists.get(media.artist_id)
            media.artist = self.get_artist(media, media.artist_id, conn) if not media.artist else media.artist
            if media.artist:
                self.cache.artists[media.artist_id] = media.artist
            # Get album data
            media.album = self.cache.albums.get(media.album_id)
            media.album = self.get_album(media, media.album_id, conn) if not media.album else media.album
            if media.album:
                self.cache.albums[media.album_id] = media.album
            # Store album folder in directories dictionary
            dir = FileUtil.get_folder(media.path)
            media.folder = self.cache.directories.get(dir)
            media.folder = Folder(media) if not media.folder else media.folder
            self.cache.directories[dir] = media.folder

        return media

    def get_media_batch(self, file_paths: dict, conn: NavidromeDbConnection) -> Generator[MediaFile]:
        """Get a batch of media files by a list of file paths.

        Args:
            file_paths: A dictionary with Navidrome to Beets path mappings
            conn: A NavidromeDbConnection object.

        Returns:
            (Generator[MediaFile]): A generator of MediaFile objects.
        """
        query = """
            SELECT  id, path, title, year, track_number, duration, bit_rate,
                    artist_id, artist, album_id, album, mbz_recording_id
            FROM media_file
            WHERE path IN ({})
        """.format(",".join("?" for _ in file_paths))
        cursor = conn.cursor()
        params = () + tuple(file_paths.keys()) + () * (len(file_paths.keys()) + 1)
        results = cursor.execute(query, params).fetchall()
        for result in results:
            media = MediaFile(*result)
            media.beets_path = file_paths[media.path]
            # Get artist data
            media.artist = self.cache.artists.get(media.artist_id)
            media.artist = self.get_artist(media, media.artist_id, conn) if not media.artist else media.artist
            if media.artist:
                self.cache.artists[media.artist_id] = media.artist

            # Get album data
            media.album = self.cache.albums.get(media.album_id)
            media.album = self.get_album(media, media.album_id, conn) if not media.album else media.album
            if media.album:
                self.cache.albums[media.album_id] = media.album

            # Store album folder in directories dictionary
            dir = FileUtil.get_folder(media.path)
            media.folder = self.cache.directories.get(dir)
            media.folder = Folder(media) if not media.folder else media.folder
            self.cache.directories[dir] = media.folder

            yield media

    def get_media_file(self, file_path: str, conn: NavidromeDbConnection) -> MediaFile:
        """
        Retrieve a media file from the database based on its path.

        Args:
            file_path (str): The path of the media file to retrieve.
            conn (NavidromeDbConnection): The database connection to use.

        Returns:
            Optional[MediaFile]: The retrieved media file, or None if not found.
        """
        query = """
            SELECT id, title, year, track_number, duration, bit_rate, artist_id, artist, album_id, album, mbz_recording_id
            FROM media_file
            WHERE path LIKE ?
        """

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

    def get_artist(self, media_file: MediaFile, artist_id: str, conn: NavidromeDbConnection) -> Artist:
        """
        Retrieve an artist from the database based on their ID.

        Args:
           media_file (MediaFile): The media file associated with the artist.
           artist_id (str): The ID of the artist to retrieve.
           conn (NavidromeDbConnection): The database connection to use.

        Returns:
            Artist: The retrieved artist object. If the artist is not found, returns None.
        """
        result = None
        query = """
            SELECT name, album_count
            FROM artist
            WHERE id LIKE ?
        """

        cursor = conn.cursor()
        cursor.execute(query, (artist_id,))
        result = cursor.fetchone()
        if not result:
            return None

        artist = Artist(id, result[0], result[1])
        artist.annotation = self.get_media_annotation(media_file, Annotation.Type.artist, conn)
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

    def get_album(self, media_file: MediaFile, album_id: str, conn: NavidromeDbConnection) -> Album:
        """
        Retrieve an album associated with the media file.

        Args:
            media_file (MediaFile): The media file associated with the album.
            album_id (str): The ID of the album.
            conn (NavidromeDbConnection): The database connection.
        """
        result = None
        query = """
            SELECT name, artist_id, song_count, mbz_album_id
            FROM album
            WHERE id LIKE ?
        """
        cursor = conn.cursor()
        cursor.execute(query, (album_id,))
        result = cursor.fetchone()
        if not result:
            return None

        album = Album(album_id, result[0], result[1], result[2], result[3])
        album.annotation = self.get_media_annotation(media_file, Annotation.Type.album, conn)
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

    def get_media_annotation(
        self, media_file: MediaFile, type: Annotation.Type, conn: NavidromeDbConnection
    ) -> Annotation:
        """
        Get media annotation for a given media file and type.

        Args:
            media_file (MediaFile): The media file object holding the relevant item id.
            type (Annotation.Type): The type of the annotation, used for querying the item type.
            conn (NavidromeDbConnection): The database connection to use.

        Returns:
            Annotation: The annotation object from the database, if existing. Otherwise it returns
               the existsing annotation assigned to the media file.
        """
        item_id: str = media_file.__getattribute__(type.value)
        annotation = self.get_annotation(item_id, type, conn)
        if not annotation:
            return media_file.annotation

    def get_annotation(self, item_id: str, type: Annotation.Type, conn: NavidromeDbConnection) -> Annotation:
        """
        Get annotation for a given item and type.

        Args:
            item_id (str): The id of the item to get annotations for.
            type (Annotation.Type): The type of the annotation, used for querying the item type.
            conn (NavidromeDbConnection): The database connection to use.

        Returns:
           Annotation: The annotation object for the given media file and type, if existing.
        """
        query = """
            SELECT play_count, play_date, rating, starred, starred_at
            FROM annotation
            WHERE user_id LIKE ? and item_id LIKE ? and item_type LIKE ?
        """
        cursor = conn.cursor()
        cursor.execute(query, (self.user_id, str(item_id), str(type.name)))
        result = cursor.fetchone()

        if not result:
            return None
        return Annotation(
            item_id,
            type,
            int(result[0]),
            result[1],
            result[2],
            result[3],
            result[4],
        )

    def store_annotation(self, annotation: Annotation, conn: NavidromeDbConnection):
        """
        Adds an annotation to the database. If the annotation already exists, it will be updated.

        Args:
            annotation (Annotation): The annotation object to be added or updated.
            conn (NavidromeDbConnection): The database connection to use.
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
        cur = conn.cursor()
        cur.execute(
            query,
            args,
        )

    def delete_annotation(self, item_id: int, item_type: Annotation.Type, conn: NavidromeDbConnection):
        """
        Delete an annotation identified by item_id, item_type and user_id.

        Args:
            item_id (int): The ID of the item associated with the annotation.
            item_type (Annotation.Type): The type of the item associated with the annotation.
            conn (NavidromeDbConnection): The database connection to use.
        """
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM annotation WHERE item_id=? AND item_type=? AND user_id=?",
            (item_id, item_type.name, self.user_id),
        )
