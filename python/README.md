<!-- mcp-name: io.github.demos-ra/text-spreadsheet -->

# text-spreadsheet for Python

Let a language model read a whole multi-sheet spreadsheet as text. The
model calls one tool with the path of a file on your machine, and
Excel, ODS, CSV, SQLite, Parquet and Arrow come back as
[MTSV](https://github.com/demos-ra/mtsv): one plain-text file where a
tab separates fields, a line break separates records, and a form feed
separates sheets.

The version is the `version` field of `pyproject.toml`.

* [Repository](https://github.com/demos-ra/text-spreadsheet)
* [Specification](https://github.com/demos-ra/mtsv-spec)

## Install

In an environment of its own:

```
pipx install text-spreadsheet
```

Then tell your host to launch it. For Claude Code:

```
claude mcp add text-spreadsheet -- text-spreadsheet
```

Other hosts take the same command in a configuration file, under
`mcpServers` or `servers`.

## The tool

The model calls `read` with a path:

```
read("/home/me/book.xlsx")
```

and gets a map of the file: its sheets, how many records each holds,
the columns of each, where each sheet's lines are, and what the
conversion left behind.

```
<FF>file
source	artifact	converted
/home/me/book.xlsx	/home/me/.cache/text-spreadsheet/home/me/book.xlsx.mtsv	yes
<FF>sheets
sheet	sheet name	records	first line	last line
1	People	4	1	6
2	Orders	200	7	208
<FF>columns
sheet	position	field name
1	1	Name
1	2	Age
<FF>left behind
what
cell type n
```

Adding an address returns that part of the file instead of the map:

```
read("/home/me/book.xlsx", sheet="2")
read("/home/me/book.xlsx", sheet="2", rows="40-120")
read("/home/me/book.xlsx", sheet="2", rows="40-120", fields="2;4")
```

Each address counts from 1 and is written as `2`, `1;3` or `1-3`, as
[RFC 7111](https://www.rfc-editor.org/rfc/rfc7111.html) writes a
selection of a tabular file. An address the file cannot answer is
refused rather than guessed.

## What is kept

Every conversion leaves an MTSV copy of the file under your cache
directory — `~/.cache/text-spreadsheet` on Linux,
`~/Library/Caches/text-spreadsheet` on macOS — mirroring the path of
the file it came from, with `.mtsv` added to its name. A later call
reads that copy unless the file has changed since, and the map names
where it is, so it can also be read directly.

Nothing else is kept, and nothing outside this machine is contacted.

## As a library

```python
from text_spreadsheet import read

text = read("/home/me/book.xlsx")
```

`read` returns MTSV text, whatever the format it came from. Whatever
a spreadsheet holds that MTSV does not — formatting, formulas, types
— is left behind, and named in the map.

## Layout

Each module hides one decision, named beside it.

```
src/text_spreadsheet/
  _cache       where the copy is kept, and whether it is fresh
  _report      what an integration left behind, as it reported it
  _map         what a file is made of
  _slice       how an address is written, and how a cut is made
  __init__     the operation: convert, keep, and answer
  _server      the tool, its annotations, and the transport
  __main__     the command a host launches
tests/         one test file per module above
```

Use points one way: `__main__` to `_server` to `read`, and `read` to
the four below it. Nothing points back up, and nothing but `_server`
knows the protocol.

## Test

From the root of the repository:

```
python3 -m venv .venv
.venv/bin/pip install ./python
.venv/bin/python -m unittest discover -s python/tests
```

## License

[MIT](https://github.com/demos-ra/text-spreadsheet/blob/main/LICENSE)
