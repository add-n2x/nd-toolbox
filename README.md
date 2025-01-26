![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/add-n2x/nd-toolbox/docker-hub.yml)
![Python](https://img.shields.io/badge/dynamic/toml?url=https%3A%2F%2Fraw.githubusercontent.com%2Fadd-n2x%2Fnd-toolbox%2Frefs%2Fheads%2Fmain%2Fpyproject.toml&query=tool.poetry.dependencies.python&label=Python)
![Beets](https://img.shields.io/badge/dynamic/toml?url=https%3A%2F%2Fraw.githubusercontent.com%2Fadd-n2x%2Fnd-toolbox%2Frefs%2Fheads%2Fmain%2Fpyproject.toml&query=tool.poetry.dependencies.beets&label=Beets)
![Ruff Style](https://img.shields.io/badge/style-ruff-41B5BE?style=flat)
![GitHub License](https://img.shields.io/github/license/add-n2x/nd-toolbox)

# Navidrome Toolbox

**Navidrome Toolbox** is a utility that enhances the functionality of [Navidrome Music Server](https://www.navidrome.org/) 
using [Beets](https://beets.io/) and custom logic. 

It aims to maintain a well-organized music library by:
- Organize your Navidrome filesystem library according to MusicBrainz folder convention.
- Removing duplicate tracks while preserving play counts and ratings.
- Avoiding the need for user interaction as much as possible.
- Offering additional helpful tools for managing your Navidrome library.

To set up _Navidrome Toolbox_, deploy it as a Docker container alongside your existing Navidrome 
installation.

> [!IMPORTANT]
> This repository is work in progress. Features and documentation are not yet completed.

## Prerequisites

- Docker
- Navidrome Music Server 0.53.0 or later

## Start Docker container

Use following command to start the Docker container:

```bash
docker run --rm -it \
    -v $(ND_DIR):/navidrome \
    -v $(MUSIC_DIR):/music \
    -v $(DATA_DIR):/data \
    -e TZ=${TIMEZONE} \
    -e ND_BASE_PATH=${ND_BASE_PATH} \
    --entrypoint bash nd-toolbox
```

You are now inside the Navidrome Toolbox container, prepared to utilize its commands.

If you installed Navidrome Toolbox using a Docker GUI on a NAS or similar device, enter 
the container shell with:

```bash
docker exec -it nd-toolbox bash
```

### Volumes

Bind-mount the following local directories into the container:

| Parameter  | Description                                                                     |
|------------|---------------------------------------------------------------------------------|
| `MUSIC_DIR` | Run the container in background. If not set, the container runs in foreground. |
| `DATA_DIR`  | A directory where temporary processing data and logs can be stored.            |
| `ND_DIR`    | The directory where your Navidrome database is located.                        |

### Environment Variables

Optionally set these environment variables:

| Parameter       | Description                                                                                   |
|-----------------|-----------------------------------------------------------------------------------------------|
| `TZ`            | Set your timezone. If not set it defaults to `Europe/Vienna`.                                 |
| `ND_BASE_PATH`  | Base path of the music library within your Navidrome container. Defaults to `/music/library`. |

## Usage

### Remove files with unsupported extensions

Remove files with unsupported extensions from your music library. This is useful to clean up your library before 
importing it into Beets. Set the environment variable `UNSUPPORTED_EXTENSIONS` to a list of extensions you want to 
remove. Defaults to `m4p mp4 mp2`.

```bash
make sh.remove-unsupported
```

By default it performs a dry-run, without actually moving files. Pass an `DRY_RUN=false` argument to actually move 
files. Moved files are moved to a `removed-media` directory inside your `DATA_DIR`.

```bash
make sh.remove-unsupported DRY_RUN=false
```

### Import music into internal library

Import music into your internal Beets library. This is required for further processing.

```bash
make beet.import
```

### Reset internal library

To reset your internal Beets library, removing all imported music:

```bash
make beet.reset
```

### Get duplicates

Get a list of duplicates according to the default behaviour, matching MusicBrainz Track ID (`mb_trackid`)
and Album ID (`mb_albumid`).

```bash
make beet.duplicates
```

### Load details for all duplicates from Navidrome database

```bash
make nd.load-duplicates
```

### Manually backup the Navidrome database

```bash
make nd.backup
```

### Merge and update annotations

Merge annotations such as play count and rating within duplicates and store the result in the Navidrome database.

The command backups the MNavidrome database before merging annotations. To be safe always create an additional 
backup of your database manually.

```bash
make nd.merge-annotations
```

### Evaluate deletable duplicates

Evaluate which duplicates have the best criteria for keeping and can be kept while deleting others.

```bash
make nd.eval-deletable
```

The criteria to decide on the media file to keep is as follows:

1. Media file is in an album, which already contains another media file which is keepable.
1. Media files have equal filenames, but one has a numeric suffix, e.g., "song.mp3" and "song1.mp3".
   The one with the numeric suffix is considered less important and will be removed.
1. Media file title and filename are compared with fuzzy search. Higher ratio is a keeper.
1. Media file has one of the preferred file extensions
1. Media file has a MusicBrainz recording ID.
1. Media file has an artist record available in the Navidrome database.
1. Media file has an album record available in the Navidrome database.
1. Media file contains a album track number.
1. Media file has a better bit rate than any of the other duplicate media files.
1. Media file holds a release year.

## Acknowledgments

This library is based on the important groundwork provided by the
[iTunes Navidrome Migration](https://github.com/Stampede/itunes-navidrome-migration) scripts.

Also, kudos to the Navidrome developers for building a music server that is here to stay.

