"""
Model classes representing the Navidrome database.
"""

import datetime
from enum import Enum
from typing import Optional


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
        self.play_count = play_count
        self.play_date = play_date
        self.rating = rating
        self.starred = starred
        self.starred_at = starred_at

    def __repr__(self) -> str:
        """Instance representation."""
        return f"Annotation(item_id={self.item_id}, play_count={self.play_count}, play_date={self.play_date}, rating={self.rating}, starred={self.starred}, starred_at={self.starred_at})"


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
    annotation: Optional[Annotation]
    has_keepable: bool

    def __init__(self, id: str, name: str, artist_id: str, song_count: int):
        """Init instance."""
        self.id = id
        self.name = name
        self.artist_id = artist_id
        self.song_count = song_count
        self.has_keepable = False

    def __repr__(self) -> str:
        """Instance representation."""
        return f"Album(id={self.id}, name={self.name}, artist_id={self.artist_id}, song_count={self.song_count})"


class MediaFile:
    """Media File model representing a media file in the database.

    Attributes:
       id (str): The unique identifier of the media file.
       path (str): The file path of the media file.
       title (str): The title of the media file.
       year (int): The release year of the media file.
       track_number (int): The track number of the media file.
       duration (int): The duration of the media file in seconds.
       bitrate (int): The bitrate of the media file in kbps.
       annotation (Annotation): The annotation of the media file.
       artist_id (str): The foreign key referencing the artist of the media file.
       artist (Artist): The artist of the media file.
       album_id (str): The foreign key referencing the album of the media file.
       album (Album): The album of the media file.
       mbz_recording_id (str): The MusicBrainz recording ID of the media file.
       has_keepable (bool): Indicates whether some of its media files is keepable.
    """

    id: str
    path: str
    title: str
    year: int
    track_number: int
    duration: int  # in seconds
    bitrate: int  # in kbps
    annotation: Optional[Annotation]
    artist_id: Optional[str]  # foreign key
    artist: Artist
    album_id: Optional[str]  # foreign key
    album: Album
    mbz_recording_id: str
    has_keepable: bool

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
        album_id: str,
        mbz_recording_id: str,
    ):
        """Init instance."""
        self.id = id
        self.path = path
        self.title = title
        self.year = year
        self.track_number = track_number
        self.duration = duration
        self.bitrate = int(bitrate)
        self.artist_id = artist_id
        self.album_id = album_id
        self.mbz_recording_id = mbz_recording_id
        self.annotation = None
        self.has_keepable = False

    def __repr__(self):
        """Instance representation."""
        return f"MediaFile(id={self.id}, path={self.path}, title={self.title}, year={self.year}, track_number={self.track_number}, duration={self.duration}, bitrate={self.bitrate}, artist_id={self.artist_id}, album_id={self.album_id}, mbz_recording_id={self.mbz_recording_id})"
