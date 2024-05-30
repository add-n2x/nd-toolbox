.DEFAULT_GOAL := help
	
# Config

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

version::
	@echo $(shell poetry version)

# Dev targets

spell:: 
	poetry run codespell
