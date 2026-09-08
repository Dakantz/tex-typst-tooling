import pytest
from typer.testing import CliRunner

from texty_tool.main import app
from texty_tool.restructure_bib import resolve_from_doi_dblp
import os

runner = CliRunner()


def test_basic_entry():
    doi = "10.1109/ACCESS.2026.3656368"
    entry = resolve_from_doi_dblp(doi)
    assert "title" in entry
    assert "author" in entry
    assert "year" in entry
    assert "journal" in entry
    assert "pages" in entry
    assert "and" in entry["author"]


def test_editor_and_booktitle():
    doi = "10.1145/3340531.3417439"
    entry = resolve_from_doi_dblp(doi)
    assert "editor" in entry
    assert "booktitle" in entry


# def test_doi_with_ampersand():
#     doi = "10.1016/j.ipm.2022.103026"
#     entry = resolve_from_doi_dblp(doi)
#     assert "&" in entry["journal"] or "\\&" in entry["journal"]


def test_e2e_ipm():
    result = runner.invoke(
        app,
        [
            "restructure-bib",
            "cleanup",
            "tests/_testbib.bib",
            "tests/references_resolved.bib",
        ],
    )
    assert result.exit_code == 0

    import bibtexparser

    # read generated bib file and check for expected entries
    with open("tests/references_resolved.bib", "r") as f:
        bib_database = bibtexparser.load(f)
        for entry in bib_database.entries:
            if "journal" in entry:
                assert "amp;" not in entry["journal"]  # check that & is not escaped


@pytest.fixture(autouse=True)
def run_around_tests():
    # Code that will run before your test, for example:
    # Check if the test file exists
    assert os.path.exists("tests/_testbib.bib")

    yield
    # cleanup should remove generated bib
    try:
        os.unlink("tests/references_resolved.bib")  # cleanup after test
    except OSError:
        pass  # If the file doesn't exist, that's fine
