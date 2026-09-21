# text-spreadsheet for Python

Read a whole multi-sheet spreadsheet as MTSV sheets. A file is named by
a file URI, and its extension names the format. The version is the
`version` field of `pyproject.toml`.

* [Repository](https://github.com/demos-ra/text-spreadsheet)
* [Specification](https://github.com/demos-ra/mtsv-spec)

## Install

```
pip install text-spreadsheet
```

A Python that an operating system manages does not accept packages
directly, so install into a virtual environment:

```
python3 -m venv .venv
.venv/bin/pip install text-spreadsheet
```

To install from a clone instead, run the same commands from the root of
the repository with `./python` in place of `text-spreadsheet`.

## Read a spreadsheet

```python
from text_spreadsheet import read

sheets = read("file:///home/me/book.xlsx")
```

Sheets are a list of dictionaries with `"sheet name"`, `"header"`, and
`"records"`, the same shape as the
[conformance results](https://github.com/demos-ra/mtsv/blob/main/conformance/README.md).

Whatever a spreadsheet holds that MTSV does not raises `ValueError` by
default. To confirm and leave it behind, pass `errors="ignore"`.

## Addressing

A file is named by a file URI, as
[RFC 8089](https://www.rfc-editor.org/rfc/rfc8089.html) defines it: the
path is absolute, and the URI is local, meaning it carries no authority
or the authority `localhost`.

```
file:///home/me/book.xlsx
file://localhost/home/me/book.xlsx
```

## Layout

| Path                      | Contents                          |
|---------------------------|-----------------------------------|
| `src/text_spreadsheet/`    | the operations, and addressing    |
| `tests/`                  | the test suite, run against the install |

## Test

From the root of the repository:

```
.venv/bin/python -m unittest discover -s python/tests
```

## License

[MIT](https://github.com/demos-ra/text-spreadsheet/blob/main/LICENSE)
