# Navidrome Toolbox

Remove duplicates from your [Navidrome](https://www.navidrome.org/) music library, while keeping play stats. 

And other little helpers for Navidrome Music Server.

<mark>**WIP**: This repository is work in progress. Features and documentation are not yet completed!</mark>

## Prerequisites

- [Poetry](https://python-poetry.org/)

Create an `.env` file based on the sample:

```bash
cp -n sample.env .env
```

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

Your music library is expected in the Docker container under `/music`. To mount your local music
library into that Docker directory set edit `.env` and set the location for `MUSIC_LIBRARY_BASE`.

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

## Acknowledgments

This library is based on the important groundwork provided by the
[iTunes Navidrome Migration](https://github.com/Stampede/itunes-navidrome-migration) scripts.
This is what finally made my move to Navidrome possible. Thank you, @Stampede!

Kudos to the Navidrome developers for building a music server that is here to stay.

