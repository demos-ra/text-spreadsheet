# text-spreadsheet

Let a language model read a whole multi-sheet spreadsheet as text. The
model calls one tool with the path of a file on your machine, and
Excel, ODS, CSV, SQLite, Parquet and Arrow come back as
[MTSV](https://github.com/demos-ra/mtsv): one plain-text file where a
tab separates fields, a line break separates records, and a form feed
separates sheets.

A language model reads text, so a binary workbook is a dead end —
without pandas or openpyxl in the loop, it cannot see inside an
`.xlsx` at all. This converts the whole file, every sheet, in one
call, so the model reads a spreadsheet the way it reads any other
text file.

* [Specification](https://github.com/demos-ra/mtsv-spec)
* [MTSV, which does the converting](https://github.com/demos-ra/mtsv)

## Install

The Python implementation, in an environment of its own:

```
pipx install text-spreadsheet
```

Then tell your host to launch `text-spreadsheet`, with no arguments.
Most hosts read a configuration file that maps a name to a command;
some write that file for you from their own command line. It is one
entry, once — after that the tool is in every session.

Released on PyPI as
[text-spreadsheet](https://pypi.org/project/text-spreadsheet/) and in
the [MCP registry](https://registry.modelcontextprotocol.io) as
`io.github.demos-ra/text-spreadsheet`.

See [python/README.md](python/README.md) for the tool, the addresses it
takes and what it keeps. Its version is the `version` field of
[python/pyproject.toml](python/pyproject.toml), and versions follow
[Semantic Versioning](https://semver.org).

## Layout

| Path          | Contents                                              |
|---------------|-------------------------------------------------------|
| `server.json` | the entry that lists this server in the MCP registry  |
| `python/`     | Python implementation of the server                   |

Each language folder holds one implementation of the same server. This
repository holds no format code: every conversion is MTSV's, and what a
spreadsheet holds that MTSV does not is reported as MTSV reports it.

## Help

Report a problem or ask a question in the
[issue tracker](https://github.com/demos-ra/text-spreadsheet/issues).
text-spreadsheet is maintained by Demos Ra.

## License

[MIT](LICENSE)
