#!/usr/bin/env python3
"""Convert acronyms.tex (\\newacronym entries) into a typst entry-list (acronyms.typ).
Written using Claude Code
"""

import re
import sys
from pathlib import Path

import typer

app = typer.Typer()

NEWACRONYM_RE = re.compile(
    r"""\\newacronym
        (?:\[(?P<opts>[^\]]*)\])?   # optional [shortplural=..., longplural=...]
        \{(?P<key>[^}]*)\}
        \{(?P<short>[^}]*)\}
        \{(?P<long>[^}]*)\}
    """,
    re.VERBOSE,
)


def parse_opts(opts):
    result = {}
    if not opts:
        return result
    for part in opts.split(","):
        if "=" not in part:
            continue
        k, v = part.split("=", 1)
        result[k.strip()] = v.strip()
    return result


def typ_escape(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def parse_acronyms(text):
    entries = []
    for m in NEWACRONYM_RE.finditer(text):
        opts = parse_opts(m.group("opts"))
        key = m.group("key").strip()
        short = m.group("short").strip()
        long_ = m.group("long").strip()
        plural = opts.get("shortplural", short + "s")
        longplural = opts.get("longplural", long_ + "s")
        entries.append(
            {
                "key": key,
                "short": short,
                "plural": plural,
                "long": long_,
                "longplural": longplural,
            }
        )
    return entries


def render_typ(entries):
    lines = ["#let entry-list = ("]
    for e in entries:
        lines.append("  (")
        lines.append(f'    key: "{typ_escape(e["key"])}",')
        lines.append(f'    short: "{typ_escape(e["short"])}",')
        lines.append(f'    plural: "{typ_escape(e["plural"])}",')
        lines.append(f'    long: "{typ_escape(e["long"])}",')
        lines.append(f'    longplural: "{typ_escape(e["longplural"])}",')
        lines.append("  ),")
    lines.append(")")
    lines.append("")
    return "\n".join(lines)


@app.command()
def convert_bib(input_path: str, output_path: str):
    input_file = Path(input_path)
    output_file = Path(output_path)
    if not input_file.exists():
        print(f"Input file {input_file} does not exist.")
        sys.exit(1)
    if output_file.exists():
        typer.confirm(
            f"Output file {output_file} already exists. Overwrite?", abort=True
        )
    text = input_file.read_text()
    entries = parse_acronyms(text)
    output_file.write_text(render_typ(entries))
    print(f"Wrote {len(entries)} entries to {output_file}")
