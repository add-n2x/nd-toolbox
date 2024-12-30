#
# Navidrome Toolbox CLI
#

export PYTHONPATH := src:$(PYTHONPATH)

# Load env vars from .env file
include .env

# Build vars
VERSION := $(shell grep -m 1 version pyproject.toml | tr -s ' ' | tr -d '"' | tr -d "'" | cut -d' ' -f3)
BUILD_DATE=$(shell date +%F)

# Container vars
BEETSDIR = ./config/beets
BEETSDIR_MUSIC_SOURCE = ./music
export

.DEFAULT_GOAL := help
help::
	@echo
	@echo --[ $(shell poetry version) ]--
	@echo
	@echo "- beet.import    		: import music to beets library"
	@echo "- beet.duplicatez  		: list duplicates with beets and export JSON"
	@echo "- beet.reset       		: delete beets music library"
	@echo "- nd.merge-annotations		: read annotations of all duplicates, merge and store them"
	@echo "- nd.eval-deletable	: evaluate deletable duplicates"
	@echo
	@echo "- dev.init			: init app"	
	@echo "- dev.shell			: start app shell"
	@echo "- dev.spell        		: run spell check"
	@echo "- dev.ruff         		: format code"
	@echo "- dev.test			: run tests"
	@echo
	@echo "- docker.build	 		: build the docker image"
	@echo "- docker.run			: run the docker container"
	@echo
	@echo "- version          		: app version"


### App targets ###

beet.import::
	beet import -A $(BEETSDIR_MUSIC_SOURCE)
beet.duplicatez::
	beet duplicatez
beet.reset::
	rm config/beets/library.db
	rm config/beets/state.pickle
nd.merge-annotations::
	poetry run python src/ndtoolbox/app.py action=merge-annotations
nd.eval-deletable::
	poetry run python src/ndtoolbox/app.py action=eval-deletable
version::
	@echo ${VERSION}

### Development targets ###

dev.init::
	$(shell cp -n config/beets/sample-config.yaml config/beets/config.yaml)
	poetry install
dev.shell::
	poetry shell
dev.spell::
	poetry run codespell
dev.ruff::
	poetry run ruff check .
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
