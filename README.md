# ai-spreadsheets

Read a whole multi-sheet spreadsheet as MTSV text, so that a language
model can work on it directly. A spreadsheet is named by a URI, and the
sheets come back in the data model that
[MTSV](https://github.com/demos-ra/mtsv) defines.

* [Specification](https://github.com/demos-ra/mtsv-spec)
* [Engine](https://github.com/demos-ra/mtsv)

## Layout

| Folder    | Contents                                     |
|-----------|----------------------------------------------|
| `python/` | Python implementation of the operations      |

Each language folder holds one implementation. The operations are the
same for every language, and every one of them reads and writes MTSV.

## Python

See [python/README.md](python/README.md) to install and use the package.
Its version is the `version` field of
[python/pyproject.toml](python/pyproject.toml).

## Status

Not released. The read operation and file URI addressing are in place.

## License

[MIT](LICENSE)
