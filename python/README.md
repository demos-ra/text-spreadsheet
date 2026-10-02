<!-- mcp-name: io.github.demos-ra/text-spreadsheet -->

# text-spreadsheet for Python

Let a language model read a whole multi-sheet spreadsheet as text. The
model calls one tool with the pathname of a file, or of a directory of
files, on your machine, and Excel, ODS, CSV, JSON, SQLite, Parquet,
Arrow and MTSV come back as [MTSV](https://github.com/demos-ra/mtsv):
one plain-text file where a tab separates fields, a line break
separates records, and a form feed separates sheets.

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

The model calls `read` with a pathname, of a file or of a directory:

```
read("/home/me/book.xlsx")
```

Everything it reads is one of five things, each inside the one before
and named by its position there: a directory, a file, a sheet, a
record, a field. Every reply is written in that order, from big to
small. It begins with the report, four sheets that say where you are
and how the call went:

* `file`: each file, and its pathname;
* `not read`: each file that was not read, and why;
* `left behind`: what each conversion lost;
* `sheets`: each sheet chosen, with how many records it holds, how
  many a filter keeps, and the positions of the records named.

Then comes the answer. With a pathname alone it is the map, the names
of the fields of each sheet:

```
<FF>file
file	source
1	/home/me/book.xlsx
<FF>not read
file	status
<FF>left behind
file	what
1	cell type n
<FF>sheets
file	sheet	sheet name	records	matches	positions
1	1	People	4	4	1-4
1	2	Orders	200	200	1-200
<FF>fields
file	sheet	field	field name
1	1	1	Name
1	1	2	Age
```

With a selection it is those values, after the same report:

```
read("/home/me/book.xlsx", sheet="2")
read("/home/me/book.xlsx", sheet="2", records="40-120")
read("/home/me/book.xlsx", sheet="2", records="40-*", fields="2;4")
```

Nothing but the answer differs between the two, so no reply needs an
earlier one to be understood.

Each selection counts from 1 inside what holds it — `sheet` in its
file, `records` in their sheet, `fields` in their record — and is
written as `2`, `1;3`, `1-3` or `2-*`, as
[RFC 7111](https://www.rfc-editor.org/rfc/rfc7111.html) writes a
selection of a tabular file. Positions that do not exist are left out,
and a sheet left with no field comes back empty; a selection not
written that way is refused.

A filter keeps the records whose fields meet a condition, written as
an [RFC 9535](https://www.rfc-editor.org/rfc/rfc9535.html) filter:
`@[0]` is a record's first field, the same position in every sheet a
call chooses.

```
read("/home/me/book.xlsx", filter="@[2] == 'open'")
read("/home/me/book.xlsx", sheet="2", records="1-50", filter="search(@[1], 'Ltd')")
```

The report counts the matches of each sheet and gives their positions,
which can be given back as `records` without the filter to read around
a match; with a filter, `records` counts the records it keeps. Text is
compared exactly, and patterns are
[I-Regexp](https://www.rfc-editor.org/rfc/rfc9485.html): `[0-9]`, not
`\d`, with a backslash in a pattern written twice.

A directory is read without the directories within it and without
names that begin with a dot, in name order, and `sheet` names the same
position in each of its files. A file with no format, or one that
cannot be read, is named in `not read` with its status, and so is a
directory, or anything else that is not a regular file, as skipped;
the others are still read.

The pathname must be absolute. A file named directly that cannot be
read or converted, whose extension names no format, or whose name
holds a tab or line break, a pathname that names neither a directory
nor a regular file, a directory that cannot be listed, and a selection
or filter not written as its syntax writes one are each refused with
the reason. A file that holds a tab or line break inside a value
cannot be converted, as MTSV cannot hold one: named directly, it is
refused, and in a directory it is named as failed.

## What is kept

Every conversion leaves an MTSV copy of the file under your cache
directory — `~/.cache/text-spreadsheet` on Linux,
`~/Library/Caches/text-spreadsheet` on macOS — mirroring the resolved
pathname of the file it came from, with `.mtsv` added to its name, and
what the conversion left behind beside it, with `-metadata.mtsv`
added. A file reached by two pathnames has one copy. A later call
reads that copy unless the file has changed since. A copy that cannot
be written, as on a full disk, is skipped: the read goes on. An MTSV
file is read where it is, and not copied. The tool removes no copy:
the cache is yours to manage, and anything in it can be deleted.

Nothing else is kept, and nothing outside this machine is contacted.

## As a library

```python
from text_spreadsheet import read

text = read("/home/me/book.xlsx")
```

`read` returns MTSV text, whatever the format it came from, and takes
the same `sheet`, `records`, `fields` and `filter` as the tool.
Whatever a spreadsheet holds that MTSV does not — formatting,
formulas, types — is left behind, and named in the report.

## Layout

Each module hides one decision, named beside it.

```
src/text_spreadsheet/
  _refusal       what a refusal is: a call the tool cannot answer, and why
  _field         what a field can hold, and how text it cannot is written
  _positions     how a selection is written, and what it names
  _filter        how a filter is written, and which records it keeps
  _selection     which sheets, records and fields a call names
  _left_behind   what an integration left behind, as it reported it
  _cache         where a copy and its metadata are kept, and when fresh
  _conversion    how one file becomes MTSV sheets
  _input         what a pathname names: a file, or a directory of files
  _report        what every reply states of its files and sheets
  _map           what the map answers with: the names of the fields
  __init__       the operation: input, selection, and the reply
  _server        the tool, the server, and how a refusal is reported
  __main__       the command a host launches
tests/           one test file per module above
```

Use points one way: `__main__` to `_server` to `read`; `read` to
`_input`, `_filter`, `_selection`, `_report` and `_map`; `_input` to
`_conversion` and `_field`; `_conversion` to `_cache`, `_field` and
`_left_behind`; `_report` to `_field` and `_positions`; `_selection`
to `_positions`; and `_server`, `_input`, `_conversion`, `_filter` and
`_positions` to `_refusal`. Nothing points back up, and nothing but
`_server` knows the protocol.

## Test

From the root of the repository:

```
python3 -m venv .venv
.venv/bin/pip install ./python
.venv/bin/python -m unittest discover -s python/tests
```

## License

[MIT](https://github.com/demos-ra/text-spreadsheet/blob/main/LICENSE)
