#
# Navidrome Toolbox CLI
#

.DEFAULT_GOAL := help

# Load env vars from .env file
include .env

# Build vars
VERSION := $(shell grep -m 1 version pyproject.toml | tr -s ' ' | tr -d '"' | tr -d "'" | cut -d' ' -f3)
BUILD_DATE=$(shell date +%F)

# Container vars
BEETSDIR = ./config/beets
BEETSDIR_MUSIC_SOURCE = ./music
export


help::
	@echo
	@echo --[ $(shell poetry version) ]--
	@echo
	@echo "- init             : init app"
	@echo "- shell            : start app shell"
	@echo "- beet.import      : import music to beets library"
	@echo "- beet.duplicatez  : list duplicates with beets and export JSON"
	@echo "- beet.reset       : delete beets music library"
	@echo "- nd.list          : "
	@echo "- version          : app version"
	@echo
	@echo "- dev.spell        : run spell check"
	@echo "- dev.ruff         : format code"
	@echo "- dev.test         : run tests"
	@echo
	@echo "- docker.build	  : build the docker image"
	@echo "- docker.run       : run the docker container"
	@echo


### App targets ###

init::
	$(shell cp -n config/beets/sample-config.yaml config/beets/config.yaml)
	poetry install
shell::
	poetry shell
beet.import::
	beet import -A $(BEETSDIR_MUSIC_SOURCE)
beet.duplicatez::
	beet duplicatez
beet.reset::
	rm config/beets/library.db
	rm config/beets/state.pickle
nd.list::
	poetry run python src/ndtools/list.py
version::
	@echo ${VERSION}

### Development targets ###

dev.spell::
	poetry run codespell
dev.ruff::
	poetry run ruff check ./**
dev.test::
	poetry run pytest -s

### Docker Targets ###

docker.build::
	docker build \
		-t nd-toolbox \
		--build-arg BUILD_DATE=$(BUILD_DATE) \
		--build-arg VERSION=$(VERSION) \
		.
docker.run::
	docker run --rm -it  \
		-v $(DIR_CONFIG):/app/config  \
		-v $(DIR_MUSIC):/app/music  \
		-v $(DIR_OUTPUT):/app/output  \
		-e TZ=${TIMEZONE} \
		--entrypoint bash nd-toolbox
