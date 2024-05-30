.DEFAULT_GOAL := help
	
# Config

VERSION := $(shell poetry version)
VERSION := $(lastword $(subst |, ,$(VERSION)))
BEETSDIR = ./config/beets
BEETSDIR_MUSIC_SOURCE = ./music
export

# App targets

help::
	@echo
	@echo --[ Navidrome Toolbox $(VERSION) ]--
	@echo

spell:: 
	poetry run codespell

shell::
	poetry shell

beet.import::
	beet import -A $(BEETSDIR_MUSIC_SOURCE)

beet.duplicates::
	beet duplicates  --full --strict


version:: VERSION := $(shell poetry version)
version:: VERSION := $(lastword $(subst |, ,$(VERSION)))
version::
	@echo Navidrome Toolbox ${VERSION}