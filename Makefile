# Music Toolbox Makefile

# Config

.DEFAULT_GOAL := help
BEETSDIR = ./config/beets
BEETSDIR_MUSIC_SOURCE = ./music
export

# App targets

help::
	@echo
	@echo --[ $(shell poetry version) ]--
	@echo
	@echo "- init             : init app"
	@echo "- shell            : start app shell"
	@echo "- beet.import      : import music to beets library"
	@echo "- beet.duplicates  : list duplicates with beets"
	@echo "- beet.reset       : delete beets music library"
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

beet.duplicates::
	beet duplicates  --full --strict

beet.reset::
	rm config/beets/library.db
	rm config/beets/state.pickle

version::
	@echo $(shell poetry version)

# Dev targets

spell:: 
	poetry run codespell
