<!-- mcp-name: io.github.demos-ra/text-spreadsheet -->

# text-spreadsheet for Python

Let a language model read a whole multi-sheet spreadsheet as text. The
model calls one tool with the path of a file, or a folder of files, on
your machine, and Excel, ODS, CSV, JSON, SQLite, Parquet, Arrow and
MTSV come back as [MTSV](https://github.com/demos-ra/mtsv): one
plain-text file where a tab separates fields, a line break separates
records, and a form feed separates sheets.

A language model reads text, so a binary workbook is a dead end —
without pandas or openpyxl in the loop, it cannot see inside an
`.xlsx` at all. This converts the whole file, every sheet, in one
call, so the model reads a spreadsheet the way it reads any other
text file.

* [Repository](https://github.com/demos-ra/text-spreadsheet)
* [Specification](https://github.com/demos-ra/mtsv-spec)

## Install

In an environment of its own:

```
pipx install text-spreadsheet
```

Then tell your host to launch `text-spreadsheet`, with no arguments.
It is one entry, once — after that the tool is in every session. Most
hosts read a configuration file:

```json
{
  "mcpServers": {
    "text-spreadsheet": {
      "command": "text-spreadsheet"
    }
  }
}
```

Some hosts use `servers` instead of `mcpServers` and add a `type`, and
some have their own command that writes the file for you.

The version is the `version` field of `pyproject.toml`, and versions
follow [Semantic Versioning](https://semver.org).

## The tool

The model calls `read` with a path, of a file or of a folder:

```
read("/home/me/book.xlsx")
```

and gets a map: the files, their sheets, how many records each holds
and how many a filter keeps, the columns of each, where each sheet's
lines are, and what each conversion left behind.

```
<FF>file
file	source	artifact	converted	status
1	/home/me/book.xlsx	/home/me/.cache/text-spreadsheet/home/me/book.xlsx.mtsv	yes	read
<FF>sheets
sheet	file	sheet name	records	matches	first line	last line
1	1	People	4	4	1	6
2	1	Orders	200	200	7	208
<FF>columns
sheet	position	field name
1	1	Name
1	2	Age
<FF>left behind
file	what
1	cell type n
```

Adding a position returns that part instead of the map:

```
read("/home/me/book.xlsx", sheet="2")
read("/home/me/book.xlsx", sheet="2", rows="40-120")
read("/home/me/book.xlsx", sheet="2", rows="40-*", fields="2;4")
```

Each position counts from 1 and is written as `2`, `1;3`, `1-3` or
`2-*`, as [RFC 7111](https://www.rfc-editor.org/rfc/rfc7111.html)
writes a selection of a tabular file. Positions that do not exist are
left out, and a sheet left with no field comes back empty; an address
not written that way is refused.

A filter keeps the records whose fields meet a condition, written as
an [RFC 9535](https://www.rfc-editor.org/rfc/rfc9535.html) filter:
`@[0]` is a record's first field, the same position in every sheet a
call chooses.

```
read("/home/me/book.xlsx", filter="@[2] == 'open'")
read("/home/me/book.xlsx", sheet="2", rows="1-50", filter="search(@[1], 'Ltd')")
```

With no position, the map counts the matches of each sheet; with one,
`rows` counts the records the filter keeps. Text is compared exactly,
and patterns are [I-Regexp](https://www.rfc-editor.org/rfc/rfc9485.html):
`[0-9]`, not `\d`, with a backslash in a pattern written twice.

A folder is read without its subfolders and without names that begin
with a dot, in name order, and its sheets are numbered across its
files. A file with no format, or one that cannot be read, is named in
the map with its status, and so is a subfolder, or anything else that
is not a regular file, as skipped; the others are still read.

The path must be absolute. A file named directly that cannot be read
or converted, or whose extension names no format, a path that names
neither a folder nor a regular file, a folder that cannot be listed,
and an address or filter not written as its syntax writes one are each
refused with the reason. A file that holds a tab or line break inside a
value cannot be converted, as MTSV cannot hold one: named directly, it
is refused, and in a folder it is named as failed.

## What is kept

Every conversion leaves an MTSV copy of the file under your cache
directory — `~/.cache/text-spreadsheet` on Linux,
`~/Library/Caches/text-spreadsheet` on macOS — mirroring the path of
the file it came from, with `.mtsv` added to its name, and what the
conversion left behind beside it, with `-metadata.mtsv` added. A later
call reads that copy unless the file has changed since, and the map
names where it is, so it can also be read directly. A copy that cannot
be written, as on a full disk, is skipped: the read goes on, and the
map names no copy. An MTSV file is read where it is, and not copied.
The tool removes no copy: the cache is yours to manage, and anything
in it can be deleted.

Nothing else is kept, and nothing outside this machine is contacted.

## As a library

```python
from text_spreadsheet import read

text = read("/home/me/book.xlsx")
```

`read` returns MTSV text, whatever the format it came from, and takes
the same `sheet`, `rows`, `fields` and `filter` as the tool. Whatever
a spreadsheet holds that MTSV does not — formatting, formulas, types
— is left behind, and named in the map.

## Layout

Each module hides one decision, named beside it.

```
src/text_spreadsheet/
  _refusal       what a refusal is: a call the tool cannot answer, and why
  _field         what a field can hold, and how text it cannot is written
  _positions     how a list of positions is written, and what it names
  _filter        how a filter is written, and which records it keeps
  _selection     which sheets, records and fields a call names
  _left_behind   what an integration left behind, as it reported it
  _cache         where a copy and its metadata live, and when fresh
  _conversion    how one file becomes MTSV text
  _input         what a path names: a file, or a folder of files
  _map           what a group of files is made of
  __init__       the operation: input, selection, and the reply
  _server        the tool, the server, and how a refusal is reported
  __main__       the command a host launches
tests/           one test file per module above
```

Use points one way: `__main__` to `_server` to `read`; `read` to
`_input`, `_filter`, `_selection` and `_map`; `_input` to
`_conversion` and `_field`; `_conversion` to `_cache`, `_field` and
`_left_behind`; `_map` to `_field`; `_selection` to `_positions`; and
`_server`, `_input`, `_conversion`, `_filter` and `_positions` to
`_refusal`. Nothing points back up, and nothing but `_server` knows the
protocol.

## Test

From the root of the repository:

```
python3 -m venv .venv
.venv/bin/pip install ./python
.venv/bin/python -m unittest discover -s python/tests
```

## License

[MIT](https://github.com/demos-ra/text-spreadsheet/blob/main/LICENSE)
