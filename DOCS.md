# `texty-tool`

**Usage**:

```console
$ texty-tool [OPTIONS] COMMAND [ARGS]...
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

## `texty-tool convert-acronyms`

Convert acronyms.tex (\newacronym entries) into a typst entry-list (acronyms.typ).

**Usage**:

```console
$ texty-tool convert-acronyms [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `convert`

### `texty-tool convert-acronyms convert`

**Usage**:

```console
$ texty-tool convert-acronyms convert [OPTIONS] [input_path] [output_path]
```

**Arguments**:

* `input_path`: [default: acronyms.tex]
* `output_path`: [default: acronyms.typ]

**Options**:

* `--help`: Show this message and exit.

## `texty-tool restructure-bib`

Restructure a BibTeX file by resolving DOIs and reformatting entries.

**Usage**:

```console
$ texty-tool restructure-bib [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `doi2bib`: Resolve a DOI to a BibTeX entry using DBLP...
* `cleanup`: Convert a BibTeX file by resolving DOIs...

### `texty-tool restructure-bib doi2bib`

Resolve a DOI to a BibTeX entry using DBLP and direct DOI resolution as fallback.

Args:
    doi (str): The DOI to resolve.

**Usage**:

```console
$ texty-tool restructure-bib doi2bib [OPTIONS] {doi}
```

**Arguments**:

* `doi`: [required]

**Options**:

* `--help`: Show this message and exit.

### `texty-tool restructure-bib cleanup`

Convert a BibTeX file by resolving DOIs and reformatting entries.

Args:
    input_path (str): Path to the input BibTeX file.
    output_path (str): Path to the output BibTeX file.

**Usage**:

```console
$ texty-tool restructure-bib cleanup [OPTIONS] [input_path] [output_path]
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

## `texty-tool runts`

Check for overhanging text in a PDF file.

**Usage**:

```console
$ texty-tool runts [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `check-overhangs`: Check for overhanging text in a PDF file.

### `texty-tool runts check-overhangs`

Check for overhanging text in a PDF file.

Args:
    pdf_path (str): Path to the PDF file.
    threshhold (float): Threshold for determining overhangs. Default is 0.25.

**Usage**:

```console
$ texty-tool runts check-overhangs [OPTIONS] [pdf_path]
```

**Arguments**:

* `pdf_path`: [default: main.pdf]

**Options**:

* `--threshhold <float>`: [default: 0.25]
* `--help`: Show this message and exit.

## `texty-tool prepare-submission`

Generate additional material ZIP files for the current directory.

**Usage**:

```console
$ texty-tool prepare-submission [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `additional-material`: Generate a ZIP file containing additional...
* `sources`: Generate a ZIP file containing source...

### `texty-tool prepare-submission additional-material`

Generate a ZIP file containing additional material for the project.

Args:
    input_files (list): List of files to include in the ZIP archive.
    output_zip (str): Output ZIP file name.

**Usage**:

```console
$ texty-tool prepare-submission additional-material [OPTIONS]
```

**Options**:

* `--input-files <str>`: [default: video/gibber_demo.mp4, appendix.pdf]
* `--output-zip <str>`: [default: additional_material.zip]
* `--help`: Show this message and exit.

### `texty-tool prepare-submission sources`

Generate a ZIP file containing source files for the project.

Args:
    input_files (list): List/patterns of source files to include in the ZIP archive.
    latexmk (bool): Include latexmk touched files in the ZIP file.
    tikz_external_dir (str): Directory containing TikZ externalized graphics.
    output_zip (str): Output ZIP file name.
    verify (bool): Verify the integrity of the ZIP file after creation.

**Usage**:

```console
$ texty-tool prepare-submission sources [OPTIONS]
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
