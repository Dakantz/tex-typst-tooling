#
# File: check-libbyhead.py
# Version: 0.98
#
# Checks whether the PDF files in the current directory have issues in matching the CEURART style.
# (C) 2024-2026 by Manfred Jeusfeld. This script is made available under the
# Creative Commons Attribution-ShareAlike CC-BY-SA 4.0 license.
#
# Call by python3 $HOME/bin/check-libbyhead.py <pdffile>
# Returns exit code 0 if the headings on page 1 of the pdffile are in Libertinus Sans font
# and the body text is in Libertinus Serif font.
# Returns exit code 1 if headings are not in Libertinus Sans.
# Returns exit code 2 if body text is not in Libertinus Serif.
# Returns exit code 3 if body text is not in Libertinus Serif and headings are not in Libertinus Sans.
#
# Created with the help of GenAI; requires python3 and pdfminer.six
#  pip install pdfminer.six
#
# 2026-01-08: Have a dedicated BODY_SIZE_FACTOR to identify the body text.
# 2026-09-04: Adapted to typer; from https://ceur-ws.org/ceurtools/
#

import sys
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTChar, LTAnno, LTTextBox, LTTextLine
import statistics
import logging
import re

import typer

app = typer.Typer()


HEADING_SIZE_FACTOR = 1.35  # Check fonts 35% larger than the body text
BODY_SIZE_FACTOR = 1.05  # Check fonts smaller than 105% of the body text
SUCCESS_THRESHOLD = 0.80  # 80% usage of the target font in headings and body required
PAGES_TO_CHECK = [0]  # Only check the first page (index 0)
# ----------------------------


def get_all_chars(layout):
    """
    Helper function to recursively yield all LTChar objects from a layout element.
    """
    for item in layout:
        if isinstance(item, LTChar):
            yield item
        elif isinstance(item, (LTTextBox, LTTextLine)):
            yield from get_all_chars(item)
        elif hasattr(item, "__iter__"):
            yield from get_all_chars(item)


@app.command()
def check_font_usage(
    pdf_path: str = typer.Argument(..., help="Path to the PDF file to check."),
    pages_to_check: str = typer.Option(
        "",
        help="Comma-separated list of page numbers to check (0-indexed). Checks all pages if not specified.",
    ),
):
    all_font_sizes = []
    all_font_names = set()
    pages_to_check_list = None
    if pages_to_check:
        try:
            pages_to_check_list = [int(p.strip()) for p in pages_to_check.split(",")]
        except ValueError:
            typer.echo(
                "Invalid page numbers provided. Please provide a comma-separated list of integers."
            )
            raise typer.Exit(code=1)
    total_chars = 0
    for page_layout in extract_pages(pdf_path, page_numbers=pages_to_check_list):
        for character in get_all_chars(page_layout):
            total_chars += 1
            all_font_sizes.append(character.size)
            all_font_names.add(character.fontname)

    try:
        body_font_size = statistics.mode(all_font_sizes)
    except statistics.StatisticsError:
        body_font_size = statistics.median(all_font_sizes)

    heading_size_threshold = body_font_size * HEADING_SIZE_FACTOR

    # 2. Second Pass: Check only characters above the heading size threshold (Page 1 only)
    heading_chars_total = 0

    heading_font_names = set()

    for page_layout in extract_pages(pdf_path, page_numbers=PAGES_TO_CHECK):
        for character in get_all_chars(page_layout):
            if character.size >= heading_size_threshold:
                heading_chars_total += 1
                font_name = character.fontname
                heading_font_names.add(font_name)

    # 3. Calculate and return success/failure

    print(f"Headings Total Chars: {heading_chars_total}")
    print(f"Total Chars: {heading_chars_total}")
    print(f"All fonts: {all_font_names}")
    print(f"Heading fonts: {heading_font_names}")
    print(f"Body fonts: {all_font_names - heading_font_names}")
