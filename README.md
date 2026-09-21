# text-spreadsheet

Let a language model read a whole multi-sheet spreadsheet as text. The
model calls one tool with a path, and Excel, ODS, CSV, SQLite, Parquet
and Arrow files come back as [MTSV](https://github.com/demos-ra/mtsv),
one plain-text file that holds every sheet.

* [Specification](https://github.com/demos-ra/mtsv-spec)
* [MTSV, which does the converting](https://github.com/demos-ra/mtsv)

## Layout

| Path          | Contents                                              |
|---------------|-------------------------------------------------------|
| `server.json` | the entry that lists this server in the MCP registry  |
| `python/`     | Python implementation of the server                   |

Each language folder holds one implementation of the same server. This
repository holds no format code: every conversion is MTSV's, and what a
spreadsheet holds that MTSV does not is reported as MTSV reports it.

## Python

See [python/README.md](python/README.md) to install and use it. Its
version is the `version` field of
[python/pyproject.toml](python/pyproject.toml).

## Status

Not released. The read tool, its four levels of address, and the cache
are in place.

## Help

Report a problem or ask a question in the
[issue tracker](https://github.com/demos-ra/text-spreadsheet/issues).
text-spreadsheet is maintained by Demos Ra.

## License

[MIT](LICENSE)
