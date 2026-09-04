from typer.testing import CliRunner
from texty_tool.main import app

runner = CliRunner()


def test_app():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output
