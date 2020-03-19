# Sebex

The ultimate assistant in [Membrane Framework] releasing & development.

## Installation

Sebex is a Python application and is officially supported on Linux and macOS systems. At least **Python 3.7** is required. There is also Elixir analysis code, which is written in Elixir itself and distributed as an _escript_. For this to work, a reasonably fresh **Erlang** installation is also needed.

Currently, building and installation directly from source code is the recommended way. and the whole procedure is scripted using a makefile:

```bash
git clone https://github.com/membraneframework/sebex.git
cd sebex
make install
```

Under the hood this will build Elixir analyzer script and place it in expected place, then it will install `sebex` package issuing `pip install --user .` command.

To update your existing installation, invoke `make install` again.

## Support and questions

If you have any problems with Sebex or Membrane Framework feel free to contact us on the [mailing list](https://groups.google.com/forum/#!forum/membrane-framework), [Discord](https://discord.gg/nwnfVSY) or via [e-mail](mailto:info+sebex@membraneframework.org).

## Copyright and License

Copyright 2020, [Software Mansion](https://swmansion.com/?utm_source=git&utm_medium=readme&utm_campaign=membrane)

[![Software Mansion](https://membraneframework.github.io/static/logo/swm_logo_readme.png)](
https://swmansion.com/?utm_source=git&utm_medium=readme&utm_campaign=membrane)

Licensed under the [Apache License, Version 2.0](LICENSE)

[Membrane Framework]: https://www.membraneframework.org/
[Pipenv]: https://pipenv.pypa.io/en/latest/
