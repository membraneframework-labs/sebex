.PHONY: all install clean

all: setup.py

install: all
	pip install --user .

setup.py: Pipfile sebex/language/elixir/elixir_analyzer
	pipenv-setup sync -p

sebex/language/elixir/elixir_analyzer:
	cd sebex_elixir_analyzer \
		&& MIX_ENV=prod mix do deps.get, escript.build \
		&& mv sebex_elixir_analyzer ../sebex/language/elixir/elixir_analyzer

clean:
	rm -rf sebex/language/elixir/elixir_analyzer
