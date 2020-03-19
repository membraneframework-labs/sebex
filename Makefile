.PHONY: install clean

install: sebex/language/elixir/elixir_analyzer
	pip install --user .

setup.py: Pipfile
	pipenv-setup sync -p

sebex/language/elixir/elixir_analyzer:
	cd sebex_elixir_analyzer \
		&& MIX_ENV=prod mix do deps.get, escript.build \
		&& mv sebex_elixir_analyzer ../sebex/language/elixir/elixir_analyzer

clean:
	rm -rf sebex/language/elixir/elixir_analyzer
