import typer
from texty_tool.convert_acronyms import app as convert_acronyms
from texty_tool.prepare_submission import app as prepare_submission
from texty_tool.restructure_bib import app as restructure_bib
from texty_tool.runts import app as runts
from texty_tool.check_fonts import app as check_fonts

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

app.add_typer(
    check_fonts,
    name="check-fonts",
    help="Check the font usage in a PDF file.",
)


def main():
    app()


def cli():
    app()


if __name__ == "__main__":
    app()
