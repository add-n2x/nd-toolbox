# Music Toolbox Makefile

# Config

.DEFAULT_GOAL := help
BEETSDIR = ./config/beets
BEETSDIR_MUSIC_SOURCE = ./music
export

BEETS_BASE_PATH := $(shell pwd)/music
NAVIDROME_BASE_PATH := /music/library
NAVIDROME_LIB := ./config/navidrome/navidrome.db
NAVIDROME_INPUT_DUPLICATES := ./output/beets-duplicates.json

# App targets

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

init::
init::
	$(shell cp -n config/beets/sample-config.yaml config/beets/config.yaml)
	$(shell mkdir -p music)
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
	python src/ndtools/list.py $(NAVIDROME_LIB) $(NAVIDROME_INPUT_DUPLICATES) $(BEETS_BASE_PATH) $(NAVIDROME_BASE_PATH)

version::
	@echo $(shell poetry version)

# Dev targets

spell::
	poetry run codespell

ruff::
	poetry run ruff check ./**