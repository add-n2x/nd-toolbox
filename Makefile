.DEFAULT_GOAL := help

help::
	@echo
	@echo --[ Navidrome Toolbox ]--
	@echo
	

# Targets

spell:: 
	poetry run codespell

version:: VERSION := $(shell poetry version)
version:: VERSION := $(lastword $(subst |, ,$(VERSION)))
version::
	@echo Navidrome Toolbox ${VERSION}