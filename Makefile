.PHONY: build install clean

build: sebex/language/elixir/elixir_analyzer
	poetry build

install: build
	pip install .

sebex/language/elixir/elixir_analyzer:
	cd sebex_elixir_analyzer \
		&& MIX_ENV=prod mix do deps.get, escript.build \
		&& mv sebex_elixir_analyzer ../sebex/language/elixir/elixir_analyzer

clean:
	rm -rf sebex/language/elixir/elixir_analyzer
