# Sebex

The ultimate assistant in [Membrane Framework] releasing & development.

## Installation

Sebex is a Python application and is officially supported on Linux and macOS systems. At least **Python 3.8** is required. There is also Elixir analysis code, which is written in Elixir itself and distributed as an _escript_. For this to work, a reasonably fresh **Erlang** installation is also needed.

Currently, building and installation directly from source code is the recommended way, and the whole procedure is scripted using a makefile:

```bash
git clone https://github.com/membraneframework/sebex.git
cd sebex
make install
```

Under the hood this will build Elixir analyzer script and place it in expected place, then it will install `sebex` package issuing `pip install --user .` command.

To update your existing installation, invoke `make install` again.

## Usage

Make sure the repositories of your GitHub Organization are public. To allow Sebex to edit your repositories generate a GitHub [Personal Access Token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) and set it as your `TOKEN` environment variable or pass it with the `--github_access_token` option.

### General workflow

Add an organization by running:
```
sebex bootstrap -o sebex-test-organization
```
#todo talk about `sebex graph` and .sebex/profiles for excluding broken repos 

Clone the organization's repositories to the local workspace:
```
sebex sync
```
Specify the package you'd like to update:
```
sebex release plan
Project: sebex_test_x
Version: 0.8.0
```

### Elixir

Sebex will update Elixir package dependencies and versions automatically and release them on your GitHub. To publish those updated packages to [Hex](https://hex.pm/) you need to be logged in as an authorized Hex package maintainer on your machine. You can check your status by running:
```
mix hex.user whoami
```

You also need to set the `HEX_API_KEY` environment variable to your Hex user key. To generate the key run:
```
mix hex.user key generate
```

You will be alerted when trying to update a package and it's dependents without publishing it to Hex as the dependent packages won't be able to resolve their dependencies to the required but unpublished version by running `mix deps.get`.

If you proceed anyway then the entire package dependency tree will later need to be published manually in order of the dependency relations.
## Development

We use [Poetry] to manage dependencies, virtual environments and builds. Run `poetry install` to install all dependencies. To build wheels run `make build`.

Python tests are run using pytest, run `pytest` inside `poetry shell` to execute them. To run Elixir analyzer test, run `mix test` within its directory.

## Support and questions

If you have any problems with Sebex or Membrane Framework feel free to contact us on the [mailing list](https://groups.google.com/forum/#!forum/membrane-framework), [Discord](https://discord.gg/nwnfVSY) or via [e-mail](mailto:info+sebex@membraneframework.org).

## Copyright and License

Copyright 2020, [Software Mansion](https://swmansion.com/?utm_source=git&utm_medium=readme&utm_campaign=membrane)

[![Software Mansion](https://logo.swmansion.com/logo?color=white&variant=desktop&width=200&tag=membrane-github)](
https://swmansion.com/?utm_source=git&utm_medium=readme&utm_campaign=membrane)

Licensed under the [Apache License, Version 2.0](LICENSE.txt)

[Membrane Framework]: https://www.membraneframework.org/
[Poetry]: https://python-poetry.org
