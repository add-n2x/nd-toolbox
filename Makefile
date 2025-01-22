#
# Navidrome Toolbox CLI
#

export PYTHONPATH := src:$(PYTHONPATH)

# Load env vars from .env file
include .env

# Build vars
VERSION := $(shell grep -m 1 version pyproject.toml | tr -s ' ' | tr -d '"' | tr -d "'" | cut -d' ' -f3)
BUILD_DATE=$(shell date +%F)


.DEFAULT_GOAL := help
help::
	@echo
	@echo --[ $(shell poetry version) ]--
	@echo
	@echo "- sh.remove-unsupported		: remove unsupported media files from the music folder"
	@echo "- beet.import    		: import music to beets library"
	@echo "- beet.duplicatez  		: list duplicates with beets and export JSON"
	@echo "- beet.reset       		: delete beets music library"
	@echo "- nd.backup			: backup the Navidrome database to 'data/backup'"
	@echo "- nd.load-duplicates		: load duplicates data from Navidrome"
	@echo "- nd.merge-annotations		: read annotations of all duplicates, merge and store them"
	@echo "- nd.eval-deletable		: evaluate deletable duplicates"
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

sh.remove-unsupported::
	poetry run python src/ndtoolbox/app.py action=remove-unsupported
beet.import::
	beet import -A $(MUSIC_DIR) -p
beet.duplicatez::
	export BEETSDIR=$(BEETSDIR) && beet -v duplicatez
beet.reset::
	rm -f $(DATA_DIR)/beets/library.db
	rm -f $(DATA_DIR)/beets/state.pickle
	rm -f $(DATA_DIR)/beets/beets-duplicates.json
nd.backup:: BACKUP_FILE = $(DATA_DIR)/backup/$(shell date +'%Y-%m-%d_%H-%M-%S')-navidrome.db
nd.backup::
	mkdir -p $(DATA_DIR)/backup
	cp $(ND_DIR)/navidrome.db $(BACKUP_FILE)
	@echo "Backed up Navidrome database to $(BACKUP_FILE)"
nd.load-duplicates::
	poetry run python src/ndtoolbox/app.py action=load-duplicates
nd.merge-annotations:: nd.backup
nd.merge-annotations::
	rm -f data/error.json
	poetry run python src/ndtoolbox/app.py action=merge-annotations
nd.eval-deletable::
	poetry run python src/ndtoolbox/app.py action=eval-deletable
version::
	@echo ${VERSION}

### Development targets ###

dev.init::
	$(shell cp -n config/beets/dev.config.yaml config/beets/config.yaml)
	poetry install
dev.shell::
	export BEETSDIR=$(BEETSDIR) && poetry shell
dev.spell::
	poetry run codespell
dev.ruff::
	poetry run ruff check .
dev.test::
	poetry run pytest -s
dev.create-test-db::
	rm test/data/navidrome.db
	sqlite3 navidrome/navidrome.db '.schema --nosys' > tmp/schema.sql
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
		-v ./navidrome:/navidrome  \
		-v ./music:/music  \
		-v ./data:/data  \
		-e TZ=${TIMEZONE} \
		--entrypoint sh nd-toolbox

