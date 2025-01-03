# Navidrome Toolbox

Remove duplicates from your [Navidrome](https://www.navidrome.org/) music library, while keeping play counts 
and ratings. 

And other little helpers for Navidrome Music Server.

> [!IMPORTANT]
> This repository is work in progress. Features and documentation are not yet completed.

## Prerequisites

- Navidrome Music Server 0.53.0 or later
- Docker

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

For all command first log into the container with:

```bash
docker exec -it nd-toolbox bash
```

### Remove files with unsupported extensions

Remove files with unsupported extensions from your music library. This is useful to clean up your library before 
importing it into Beets. Set the envinronment variable `UNSUPPORTED_EXTENSIONS` to a list of extensions you want to 
remove. Defaults to `m4p mp4 mp2`.

```bash
make sh.remove-unsupported
```

By default it performs a dry-run, without actually moving files. Pass an `DRY_RUN=false` argument to actually move 
files. Moved files are moved to a `removed-media` directory inside your `DATA_DIR`.

```bash
make sh.remove-unsupported DRY_RUN=true
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

### Merge and update annotations

Merge annotations such as play count and rating within duplicates and store the result in the Navidrome database.

The command backups the navidrome database before merging annotations. To be safe always create an additional 
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
1. Media file has one of the preferred file extensions
1. Media file has a MusicBrainz recording ID.
1. Media file has an artist record available in the Navidrome database.
1. Media file contains a album track number.
1. Media file has a better bit rate than any of the other duplicate media files.
1. Media file holds a release year.

## Acknowledgments

This library is based on the important groundwork provided by the
[iTunes Navidrome Migration](https://github.com/Stampede/itunes-navidrome-migration) scripts.
This is what finally made my move to Navidrome possible.

Also, kudos to the Navidrome developers for building a music server that is here to stay.

