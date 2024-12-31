#
# Navidrome Toolbox CLI
#

export PYTHONPATH := src:$(PYTHONPATH)

# Load env vars from .env file
# include .env

# Build vars
VERSION := $(shell grep -m 1 version pyproject.toml | tr -s ' ' | tr -d '"' | tr -d "'" | cut -d' ' -f3)
BUILD_DATE=$(shell date +%F)

# Container vars
ND_DIR = ./config/navidrome
MUSIC_DIR = ./music
DATA_DIR = ./data
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
	beet import -A $(MUSIC_DIR)
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
dev.create-test-db::
	sqlite3 config/navidrome/navidrome.db '.schema' > tmp/schema.sql
	sqlite3 test/data/navidrome.db < tmp/schema.sql
	@echo Now connect to db and run 'INSERT INTO user VALUES('b67d5135-cf67-4544-8013-d0f7c2d8a65a','test','Test User','','xx+aaaa/bb/ccccc+dddd/eee==',1,'2024-12-12 12:12:12.12+00:00',NULL,'2024-12-12 12:12:12.12+00:00','2020-20-20T10:20:20.20');'

### Docker Targets ###

docker.build::
	docker build \
		-t nd-toolbox \
		--build-arg BUILD_DATE=$(BUILD_DATE) \
		--build-arg VERSION=$(VERSION) \
		.
docker.run::
	docker run --rm -it  \
		-v $(ND_DIR):/app/config/navidrome  \
		-v $(MUSIC_DIR):/app/music  \
		-v $(DATA_DIR):/app/data  \
		-e TZ=${TIMEZONE} \
		--entrypoint bash nd-toolbox
