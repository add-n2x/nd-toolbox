# Navidrome Toolbox

Remove duplicates from your [Navidrome](https://www.navidrome.org/) music library, while keeping play counts 
and ratings. 

And other little helpers for Navidrome Music Server.

<mark>**WIP**: This repository is work in progress. Features and documentation are not yet completed!</mark>

## Prerequisites

- Navidrome Music Server 0.53.0 or later
- Docker

## Start Docker container

Your music library is expected in the Docker container under `/music`. To mount your local music
library into that Docker directory set edit `.env` and set the location for `MUSIC_LIBRARY_BASE`.


```bash
	docker run --rm -it  \
		-v $(ND_DIR):/app/config/navidrome  \
		-v $(MUSIC_DIR):/app/music  \
		-v $(DATA_DIR):/app/data  \
		-e TZ=${TIMEZONE} \
		--entrypoint bash nd-toolbox
```

## Usage

For all command first log into the container with:

```bash
	docker exec -it nd-toolbox bash
```

### Import music library

```bash
make beet.import
```

### Get duplicates

Get a list of duplicates according to the default behaviour, matching MusicBrainz Track ID (`mb_trackid`)
and Album ID (`mb_albumid`).

```bash
make beet.duplicates
```

### Merge and update annotations

Merge annotations such as play count and rating within duplicates and store the result in the Navidrome database.

```bash
make nd.merge-annotations
```

### Evaluate deletable duplicates

Evaluate which duplicates have the best criteria for keeping and can be kept while deleting others.

```bash
make nd.eval-deletable
```

## Acknowledgments

This library is based on the important groundwork provided by the
[iTunes Navidrome Migration](https://github.com/Stampede/itunes-navidrome-migration) scripts.
This is what finally made my move to Navidrome possible. Thank you, @Stampede!

Kudos to the Navidrome developers for building a music server that is here to stay.

