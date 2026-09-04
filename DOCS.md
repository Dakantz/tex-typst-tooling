# CLI

**Usage**:

```console
$ [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `convert-acronyms`: Convert acronyms.tex (\newacronym entries)...
* `restructure-bib`: Restructure a BibTeX file by resolving...
* `runts`: Check for overhanging text in a PDF file.
* `prepare-submission`: Generate additional material ZIP files for...
* `check-fonts`: Check the font usage in a PDF file.

## `convert-acronyms`

Convert acronyms.tex (\newacronym entries) into a typst entry-list (acronyms.typ).

**Usage**:

```console
$ convert-acronyms [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `convert`

### `convert-acronyms convert`

**Usage**:

```console
$ convert-acronyms convert [OPTIONS] [input_path] [output_path]
```

**Arguments**:

* `input_path`: [default: acronyms.tex]
* `output_path`: [default: acronyms.typ]

**Options**:

* `--help`: Show this message and exit.

## `restructure-bib`

Restructure a BibTeX file by resolving DOIs and reformatting entries.

**Usage**:

```console
$ restructure-bib [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `doi2bib`: Resolve a DOI to a BibTeX entry using DBLP...
* `cleanup`: Convert a BibTeX file by resolving DOIs...

### `restructure-bib doi2bib`

Resolve a DOI to a BibTeX entry using DBLP and direct DOI resolution as fallback.

Args:
    doi (str): The DOI to resolve.

**Usage**:

```console
$ restructure-bib doi2bib [OPTIONS] {doi}
```

**Arguments**:

* `doi`: [required]

**Options**:

* `--help`: Show this message and exit.

### `restructure-bib cleanup`

Convert a BibTeX file by resolving DOIs and reformatting entries.

Args:
    input_path (str): Path to the input BibTeX file.
    output_path (str): Path to the output BibTeX file.

**Usage**:

```console
$ restructure-bib cleanup [OPTIONS] [input_path] [output_path]
```

**Arguments**:

* `input_path`: [default: references.bib]
* `output_path`: [default: references_resolved.bib]

**Options**:

* `--remove-duplicates / --no-remove-duplicates`: [default: remove-duplicates]
* `--remove-issn / --no-remove-issn`: [default: remove-issn]
* `--remove-url / --no-remove-url`: [default: remove-url]
* `--remove-isbn / --no-remove-isbn`: [default: remove-isbn]
* `--remove-pages / --no-remove-pages`: [default: remove-pages]
* `--remove-editor / --no-remove-editor`: [default: remove-editor]
* `--preserve-title-capitalization / --no-preserve-title-capitalization`: [default: preserve-title-capitalization]
* `--help`: Show this message and exit.

## `runts`

Check for overhanging text in a PDF file.

**Usage**:

```console
$ runts [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `check-overhangs`: Check for overhanging text in a PDF file.

### `runts check-overhangs`

Check for overhanging text in a PDF file.

Args:
    pdf_path (str): Path to the PDF file.
    threshhold (float): Threshold for determining overhangs. Default is 0.25.

**Usage**:

```console
$ runts check-overhangs [OPTIONS] [pdf_path]
```

**Arguments**:

* `pdf_path`: [default: main.pdf]

**Options**:

* `--threshhold <float>`: [default: 0.25]
* `--help`: Show this message and exit.

## `prepare-submission`

Generate additional material ZIP files for the current directory.

**Usage**:

```console
$ prepare-submission [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `additional-material`: Generate a ZIP file containing additional...
* `sources`: Generate a ZIP file containing source...

### `prepare-submission additional-material`

Generate a ZIP file containing additional material for the project.

Args:
    input_files (list): List of files to include in the ZIP archive.
    output_zip (str): Output ZIP file name.

**Usage**:

```console
$ prepare-submission additional-material [OPTIONS]
```

**Options**:

* `--input-files <str>`: [default: video/gibber_demo.mp4, appendix.pdf]
* `--output-zip <str>`: [default: additional_material.zip]
* `--help`: Show this message and exit.

### `prepare-submission sources`

Generate a ZIP file containing source files for the project.

Args:
    input_files (list): List/patterns of source files to include in the ZIP archive.
    latexmk (bool): Include latexmk touched files in the ZIP file.
    tikz_external_dir (str): Directory containing TikZ externalized graphics.
    output_zip (str): Output ZIP file name.
    verify (bool): Verify the integrity of the ZIP file after creation.

**Usage**:

```console
$ prepare-submission sources [OPTIONS]
```

**Options**:

* `--input-files <str>`
* `--latexmk / --no-latexmk`: Include latexmk touched files in the ZIP file.  [default: latexmk]
* `--tikz-external-dir <str>`: [default: tikz]
* `--output-zip <str>`: [default: sources.zip]
* `--verify / --no-verify`: [default: no-verify]
* `--force / --no-force`: [default: no-force]
* `--rerun / --no-rerun`: [default: no-rerun]
* `--help`: Show this message and exit.

## `check-fonts`

Check the font usage in a PDF file.

**Usage**:

```console
$ check-fonts [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `check-font-usage`

### `check-fonts check-font-usage`

**Usage**:

```console
$ check-fonts check-font-usage [OPTIONS] {pdf_path}
```

**Arguments**:

* `pdf_path`: Path to the PDF file to check.  [required]

**Options**:

* `--pages-to-check <str>`: Comma-separated list of page numbers to check (0-indexed). Checks all pages if not specified.
* `--help`: Show this message and exit.
