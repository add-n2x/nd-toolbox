"""
Model classes representing the Navidrome database.
"""

import os
from datetime import datetime
from enum import Enum
from typing import Optional

from ndtoolbox.beets import BeetsClient
from ndtoolbox.utils import DateUtil as DU
from ndtoolbox.utils import FileUtil, ToolboxConfig
from ndtoolbox.utils import PrintUtil as PU


class Annotation:
    """
    Annotation class to represent an annotation database table.

    Attributes:
        item_id (str): The identifier of the item being annotated. Depending on the `item_type` it holds either the ID
            of an artist, track or album.
        item_type (str): The type of the item being annotated. Either a artist, track or an album.
        play_count (int): The number of times the item has been played.
        play_date (datetime): The date and time when the item was last played.
        rating (int): The user's rating for the item.
        starred (bool): Whether the item is marked as starred by the user.
        starred_at (datetime): The date and time when the item was starred.
    """

    class Type(Enum):
        """Annotation Types."""

        media_file = "id"
        artist = "artist_id"
        album = "album_id"

    item_id: str
    item_type: Type
    play_count: int
    play_date: datetime
    rating: int
    starred: bool
    starred_at: datetime

    def __init__(
        self,
        item_id: str,
        item_type: Type,
        play_count: int,
        play_date: datetime,
        rating: int,
        starred: bool,
        starred_at: datetime,
    ):
        """Init instance."""
        self.item_id = item_id
        self.item_type = item_type
        self.play_count = int(play_count) if play_count else 0
        self.play_date = DU.parse_date(play_date) if play_date else None
        self.rating = int(rating) if rating else 0
        self.starred = bool(starred) if starred else False
        self.starred_at = DU.parse_date(starred_at) if starred_at else None

    def __repr__(self) -> str:
        """Instance representation."""
        return f"Annotation(item_id={self.item_id}, play_count={self.play_count}, play_date={self.play_date}, \
            rating={self.rating}, starred={self.starred}, starred_at={self.starred_at})"


class Artist:
    """Artist model representing an artist in the database."""

    id: str
    name: str
    album_count: int
    annotation: Optional[Annotation]

    def __init__(self, id: str, name: str, album_count: int):
        """Init instance."""
        self.id = id
        self.name = name
        self.album_count = album_count

    def __repr__(self) -> str:
        """Instance representation."""
        return f"Artist(id={self.id}, name={self.name}, album_count={self.album_count})"


class Album:
    """Album model representing an album in the database."""

    id: str
    name: str
    artist_id: str
    song_count: int
    mbz_album_id: str
    annotation: Optional[Annotation]
    has_keepable: bool

    def __init__(self, id: str, name: str, artist_id: str, song_count: int, mbz_album_id: str):
        """Init instance."""
        self.id = id
        self.name = name
        self.artist_id = artist_id
        self.mbz_album_id = mbz_album_id
        self.song_count = song_count
        self.has_keepable = False

    def __repr__(self) -> str:
        """Instance representation."""
        return f"Album(id={self.id}, name={self.name}, artist_id={self.artist_id}, song_count={self.song_count}, mbz_album_id={self.mbz_album_id})"


class MediaFile:
    """Media File model representing a media file in the database.

    Attributes:
       id (str): The unique identifier of the media file.
       path (str): The file path of the media file.
       beets_path (str): The file path of the media file in Beets.
       title (str): The title of the media file.
       year (int): The release year of the media file.
       track_number (int): The track number of the media file.
       duration (int): The duration of the media file in seconds.
       bitrate (int): The bitrate of the media file in kbps.
       annotation (Annotation): The annotation of the media file.
       artist_id (str): The foreign key referencing the artist of the media file.
       artist_name (str): The name of the artist of the media file (optional).
       artist (Artist): The artist of the media file.
       album_id (str): The foreign key referencing the album of the media file.
       album_name (str): The name of the album of the media file.
       album (Album): The album of the media file (optional).
       mbz_recording_id (str): The MusicBrainz recording ID of the media file.
       is_deletable (bool): Indicates whether some of its media files is keepable.
       delete_reason (Optional[str]): The reason why the media file is scored as deletable.
    """

    id: str
    path: str
    beets_path: str
    folder: object
    title: str
    year: int
    track_number: int
    duration: int  # in seconds
    bitrate: int  # in kbps
    annotation: Optional[Annotation]
    artist_id: Optional[str]  # foreign key
    arist_name: str
    artist: Artist
    album_id: Optional[str]  # foreign key
    album_name: str
    album: Album
    mbz_recording_id: str
    is_deletable: bool
    delete_reason: Optional[str]

    def __init__(
        self,
        id: str,
        path: str,
        title: str,
        year: int,
        track_number: int,
        duration: int,
        bitrate: int,
        artist_id: str,
        artist_name: str,
        album_id: str,
        album_name: str,
        mbz_recording_id: str,
    ):
        """Init instance."""
        self.id = id
        self.path = path
        self.beets_path = None
        self.folder = None
        self.title = title
        self.year = year
        self.track_number = track_number
        self.duration = duration
        self.bitrate = int(bitrate)
        self.artist_id = artist_id
        self.artist_name = artist_name
        self.artist = None
        self.album_id = album_id
        self.album_name = album_name
        self.album = None
        self.mbz_recording_id = mbz_recording_id
        self.annotation = None
        self.is_deletable = False
        self.delete_reason = None

    def __repr__(self) -> str:
        """Instance representation."""
        return f"MediaFile(id={self.id}, path={self.path}, title={self.title}, year={self.year}, \
            track_number={self.track_number}, duration={self.duration}, bitrate={self.bitrate}, \
            artist_id={self.artist_id}, artist_name={self.artist_name} album_id={self.album_id}, \
            album_name={self.album_name}, mbz_recording_id={self.mbz_recording_id})"


class Folder:
    """
    Folder model represents the directory holding a set of files in the filesystem.

    Depending on how many keepable or deletable duplicate, or non-duplicate files are present, this is used to
    identify if some file or folder is worth keeping or not.

    Attributes:
        folder (str): The path to the album folder.
        files (dict[str, MediaFile]): A dictionary with file path as key and optional MediaFile as value.

    """

    UNKNOWN_ARTIST = "Unknown Artist"
    UNKNOWN_ALBUM = "Unknown Album"

    class Type(Enum):
        """Folder type."""

        ROOT = "root"
        ARTIST = "artist"
        ALBUM = "album"

    CACHE: dict = {}
    path: str
    type: Type
    album: str
    files: dict[str, MediaFile]
    has_keepable: bool
    is_compilation: bool
    is_dirty: bool
    total: int
    missing: int

    def __init__(self, media: MediaFile):
        """Init instance."""
        self.beets_path = FileUtil.get_folder(media.beets_path)
        self.beets_album = None
        self.nd_album = media.album_name
        self.files = []
        self.has_keepable = False
        self.is_compilation = False
        self.is_dirty = False
        self.total = None
        self.missing = None

        # Set folder type
        self.type = Folder.Type.ALBUM
        if self.beets_path == ToolboxConfig.base_path_beets:
            self.type = Folder.Type.ROOT
        elif len(media.beets_path.replace(ToolboxConfig.base_path_beets, "").split(os.sep)) == 0:
            self.type = Folder.Type.ARTIST
        else:
            # FIXME This should be handled in a better way
            self.type = Folder.Type.ALBUM

        # For performance reasons, we don't load album info for all folders
        if (
            not self.is_dirty
            and not self.beets_album
            and not self.type == Folder.Type.ROOT
            and not self.type == Folder.Type.ARTIST
        ):
            self._load_album_info()

        # Check if folder is dirty
        artist = FileUtil.get_artist_folder(self.beets_path)
        album = FileUtil.get_album_folder(self.beets_path)
        if artist == Folder.UNKNOWN_ARTIST or album == Folder.UNKNOWN_ALBUM:
            self.is_dirty = True

    def _load_album_info(self) -> None:
        """Load album information from Beets."""
        if self.type == Folder.Type.ROOT:
            PU.warning("Root folder cannot not be processed")
            return None

        # Get album info from cache if available
        infos = Folder.CACHE.get(self.beets_path)
        if not infos:
            infos = list(BeetsClient.get_album_info(self.beets_path))
            Folder.CACHE[self.beets_path] = infos

        if not infos:
            # TODO Clarify how to handle this case
            PU.warning(f"Got no album info for {self.beets_path} > clarify handling")
            self.is_dirty = True
        if len(infos) > 1:
            # Folder contains files form multiples albums. So this is either a dump folder
            # or amanually made compilation/mixtape.
            self.is_dirty = True
            PU.warning(f"Found self-made compilation, mixtape or dump folder: '{self.beets_path}'")
        elif len(infos) == 1:
            self.beets_album = infos[0].album
            self.total = infos[0].total
            self.missing = infos[0].missing
            self.is_compilation = infos[0].compilation

    def map_media_to_file(self, media: MediaFile):
        """Map a media file to an existing file in the album folder."""
        self.files[FileUtil.get_file(media.path)] = media
