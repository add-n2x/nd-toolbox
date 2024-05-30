# Navidrome Toolbox

Little helpers for [Navidrome](https://www.navidrome.org/).

## Prerequisites

- [Poetry](https://python-poetry.org/)

Then install the dependencies and create the default configuration using:

```bash
make init
```

## Usage

Enter the Poetry virtual environment with

```bash
make shell
```

**Important**: While you could call the `beet` command directly, ensure you always use the wrapped 
`make beet` version. This also sets the Beets working directory (`BEETSDIR`) to `config/beets/` and 
ensures using the prepared Beets configuration file.

Using this configuration, all operations are done in a non-destructive way, meaning no write 
operations are done on your music files and no files are copied. 

Nonetheless we cannot guarantee any malfunctions due to bugs and misconfiguration. Therefore always 
make copies of your files and libraries and do test runs wherever possible.

### Prepare music library

You can copy you existing Beets library files to `config/beets/library.db`, or create a new library
in said location with:

```bash
make beet.import
```

### Get duplicates

```bash
make beet.duplicates
```

This lists all duplicates according to default behaviour, matching MusicBrainz Track ID (`mb_trackid`)and Album ID (`mb_albumid`).

### Get list of worse duplicates

```py
python query_navidrome.py /path/to/navidrome.db /path/to/music/file.mp3
```