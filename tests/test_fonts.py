from typer.testing import CliRunner
from texty_tool.main import app

runner = CliRunner()


def test_fonts():
    result = runner.invoke(
        app, ["check-fonts", "check-font-usage", "tests/_testdoc.pdf"]
    )
    assert result.exit_code == 0
    assert "Headings Total Chars" in result.output
    assert "Body fonts" in result.output
