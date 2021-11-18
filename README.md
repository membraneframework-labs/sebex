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

### Preparation

It's advisable to use the `--profile` and `--workspace` options when running Sebex or to set env vars `SEBEX_PROFILE` and `SEBEX_WORKSPACE`

To add an organization run:

```bash
sebex bootstrap -o sebex-test-organization
```

This will create the `manifest.yaml` listing all public repositories in that organization. To exclude broken or unsupported repositories from further analysis add a new line containing `!project_name` to your `workspace_directory/profiles/your_profile.txt` file.

To perform further work Sebex must clone your organization's repositories to your local workspace:

```bash
sebex sync
```

You can view the dependency graph of your projects:

```bash
sebex graph --view
```

### Releasing packages

Prepare a release plan by listing the project names of the packages you want to release:

```bash
sebex release plan
Project: sebex_test_b
Project: sebex_test_e
Project:
```

All listed packages as well as their dependent packages will be bumped by one minor version (e.g. 0.2.1 -> 0.3.0).
Review if you're happy with the suggested release plan and save it.

Sebex will warn you if there are obsolete dependencies in your packages. By default they will be updated anyway.
To disable updating of obsolete packages run:

```bash
sebex release plan --no-update
```

Example output of `sebex release plan`:

```
Release "Purely Easy Wahoo"
===========================

1. Phase "Surely Vocal Kitten"
  * sebex_test_b, 0.2.0 -> 0.3.0, publish
  * sebex_test_e, 0.2.0 -> 0.3.0, publish
2. Phase "Easily Moved Tarpon"
  * sebex_test_c, 0.2.0 -> 0.3.0, publish
    dependencies: sebex_test_b, "~> 0.2.0" -> "~> 0.3.0"
3. Phase "Vastly Nice Impala"
  * sebex_test_d, 0.2.0 -> 0.3.0, publish
    dependencies: sebex_test_c, "~> 0.2.0" -> "~> 0.3.0"
  * sebex_test_f, 0.2.0 -> 0.3.0, publish
    dependencies:
      - sebex_test_c, "~> 0.2.0" -> "~> 0.3.0"
      - sebex_test_e, "~> 0.2.0" -> "~> 0.3.0"

Save this release? [y/N]:
```

To execute the plan run:

```bash
sebex release proceed
```

for each phase of the plan.

If at this point you encounter an error while releasing any phase of the plan there is no need to rerun `sebex release plan`. Instead run `sebex release proceed` after you've fixed the issue causing that phase to fail. Sebex will continue where you left off.

### Elixir

At the moment Elixir is the only supported language.

Sebex will modify your Elixir projects by updating your project version and dependencies in the `mix.exs` file. Those changes will be commited to Github and tagged as a version release. To publish those updated packages to [Hex](https://hex.pm/) you need to be logged in as an authorized Hex package maintainer on your machine.

You also need to set the `HEX_API_KEY` environment variable to your Hex user key. To generate the key run:

```bash
mix hex.user key generate
```

Only packages that were released at least once will be published automatically by Sebex to avoid publishing work-in-progress projects.

To publish a package that has not yet been published to hex you can edit the `force-publish` field in your `manifest.yaml` file.

## Development

We use [Poetry] to manage dependencies, virtual environments and builds. Run `poetry install` to install all dependencies. To build wheels run `make build` .

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
