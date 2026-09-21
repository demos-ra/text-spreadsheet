# text-spreadsheet

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

Each language folder holds one implementation. An operation returns the
data model that MTSV defines; MTSV itself is what crosses the boundary
to whoever asked.

## Python

See [python/README.md](python/README.md) to install and use the package.
Its version is the `version` field of
[python/pyproject.toml](python/pyproject.toml).

## Status

Not released. The read operation and file URI addressing are in place.

## Help

Report a problem or ask a question in the
[issue tracker](https://github.com/demos-ra/text-spreadsheet/issues).
text-spreadsheet is maintained by Demos Ra.

## License

[MIT](LICENSE)
