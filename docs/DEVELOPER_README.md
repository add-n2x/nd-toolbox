# Navidrome Toolbox - Developer README

This document provides guidance for developers who want to contribute to or understand the Navidrome Toolbox project.

## Prerequisites

- Navidrome Music Server 0.53.0 or later
- [Poetry](https://python-poetry.org/)

Create an `.env` file based on the sample:

```bash
cp -n .env.dev .env
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

