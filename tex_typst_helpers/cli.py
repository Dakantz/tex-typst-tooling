import typer
from .convert_acronyms import app as convert_acronyms
from .prepare_submission import app as prepare_submission
from .restructure_bib import app as restructure_bib
from .runts import app as runts

app = typer.Typer()
app.add_typer(
    convert_acronyms,
    name="convert-acronyms",
    help="Convert acronyms.tex (\\newacronym entries) into a typst entry-list (acronyms.typ).",
)
app.add_typer(
    restructure_bib,
    name="restructure-bib",
    help="Restructure a BibTeX file by resolving DOIs and reformatting entries.",
)
app.add_typer(
    runts,
    name="runts",
    help="Check for overhanging text in a PDF file.",
)
app.add_typer(
    prepare_submission,
    name="prepare-submission",
    help="Generate additional material ZIP files for the current directory.",
)


def main():
    app()


if __name__ == "__main__":
    app()
