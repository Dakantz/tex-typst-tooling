from pathlib import Path
import sys
from typing import Annotated

import pymupdf
import typer

app = typer.Typer()


@app.command()
def check_overhangs(
    pdf_path: Annotated[str, typer.Argument()] = "main.pdf", threshhold: float = 0.25
):
    """
    Check for overhanging text in a PDF file.

    Args:
        pdf_path (str): Path to the PDF file.
        threshhold (float): Threshold for determining overhangs. Default is 0.25.
    """
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print(f"PDF file {pdf_file} does not exist.")
        sys.exit(1)

    d = pymupdf.open(pdf_file)
    for pno, p in enumerate(d, 1):
        for b in p.get_text("dict")["blocks"]:
            if b["type"] != 0 or len(b["lines"]) < 2:
                continue
        ws = [l["bbox"][2] - l["bbox"][0] for l in b["lines"]]
        if ws[-1] < threshhold * max(ws):
            print(pno, "".join(s["text"] for s in b["lines"][-1]["spans"]))
