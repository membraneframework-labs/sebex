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

Under the hood this will build Elixir analyzer script and place it in the expected place, then it will install `sebex` package issuing `pip install --user .` command.

To update your existing installation, invoke `make install` again.

## Usage
### Setup communication with GitHub API
Make sure the repositories of your GitHub Organization are public. To allow Sebex to edit your repositories:
+ Generate a GitHub [Personal Access Token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) and set it as your `SEBEX_GITHUB_ACCESS_TOKEN` environment variable or pass it with the `--github_access_token` option.
+ [Generate SSH key, add it to the ssh-agent](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent) and [add to your GitHub account](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account).

### Preparation

It's advisable to use the `--workspace` and `--profile` options when running Sebex or to set the corresponding env vars: `SEBEX_WORKSPACE` and `SEBEX_PROFILE`.
+ The workspace is a directory, where sebex clones repositories, so that it can work on them later on. It also contains `.sebex` subdirectory, with some metadata files needed for sebex to run properly. The default workspace (applicable to a situation in which you haven't explicitly specified the workspace) is the directory, from which you are running the sebex.
+ The profile helps you manage different sebex configurations. Each profile is described by the `<profile name>.txt` text file inside the `<workspace_directory>/.sebex/profiles/` directory. You need to create that file on your own. An exemplary profile description file can be found inside `examples/` subdirectory of this repository. Note, that the `<profile name>.txt` file has a `.txt` extension - later on, you will be able to refer to it with `--profile <profile name>` option within the command syntax.

To add an organization run:

```bash
sebex bootstrap -o <Github organization name>
```

This will create the `manifest.yaml` inside the `.sebex` subdirectory of your workspace directory. The manifest will contain a list of all public repositories in that organization. To exclude broken or unsupported repositories from further analysis add a new line containing `!<project name>` to your `<workspace directory>/.sebex/profiles/<your profile>.txt` file.

To perform further work Sebex must clone your organization's repositories to your local workspace:

```bash
sebex sync
```

You can view the dependency graph of your projects:

```bash
sebex graph --view
```

### Releasing packages

Prepare a release plan by listing the project names (names of the repositories) of the packages you want to release. After passing the name of each project, you will be asked to pass a tag of the version, which will be released.
At least one project name needs to be passed. When you are done with listing the needed projects, simply press enter.

```bash
sebex release plan
Project: sebex_test_b
Version: 0.10.0
Project: sebex_test_e
Version: 0.6.0
Project:
```

Important! All the projects updated with sebex must be Mix projects,  with the `@version` tag inside their `mix.exs` file.
All listed packages as well as their dependent packages will be bumped by one minor version (e.g. 0.2.1 -> 0.3.0).

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
The release plan will be saved inside the `<workspace directory>/.sebex/release.yaml` file.
The release is divided into several phases. The subsequent phase can be launched, once the previous phase is finished, which is necessary due to dependencies between projects.
In the first phase, we are releasing a new version of the listed projects. The later phase of the release comes with dependencies updates.

To execute the plan run:

```bash
sebex release proceed
```

for each phase of the plan. 
During the release, follow the instructions provided by sebex.

### Elixir

At the moment Elixir is the only supported language.

Sebex will modify your Elixir projects by updating your project version and dependencies in the `mix.exs` file. Those changes will be committed to Github and tagged as a version release. To publish those updated packages to [Hex](https://hex.pm/) you need to be logged in as an authorized Hex package maintainer on your machine.

You also need to set the `HEX_API_KEY` environment variable to your Hex user key. To generate the key run:

```bash
mix hex.user key generate
```

Only packages that were released at least once will be published automatically by Sebex to avoid publishing work-in-progress projects.
However, packages belonging to the Github `sebex-test-organization` will always be published.

## Development

We use [Poetry] to manage dependencies, virtual environments, and builds. Run `poetry install` to install all dependencies. To build wheels run `make build`.

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

