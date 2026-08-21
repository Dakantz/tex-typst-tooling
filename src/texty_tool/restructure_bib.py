import re
import time
from pathlib import Path
from typing import Annotated

import bibtexparser
import requests
import tqdm
import typer
from rdflib.plugins.stores.sparqlstore import SPARQLStore

app = typer.Typer()

# %%
graph = SPARQLStore("https://sparql.dblp.org/sparql", method="POST")

# %%


# %%
def resolve_from_doi_dblp(doi: str) -> dict:
    resp = graph.query(f"""
## Publication types in dblp
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
SELECT ?s WHERE {{
  ?s rdf:type dblp:Publication .
  ?s dblp:doi <https://doi.org/{doi}>.
}}
""")
    dblp_url = list(resp)[0][0].n3().strip("<>")
    print(f"Resolved DOI {doi} via DBLP to {dblp_url}")
    retries = 5
    while retries > 0:
        try:
            bib = requests.get(dblp_url + ".bib").text
            e = bibtexparser.loads(bib).entries[0]
            return e
        except Exception as e:
            print(f"Error resolving DOI {doi}: {e}, retrying...")

            time.sleep(1)
            retries -= 1
    raise ValueError(f"Failed to resolve DOI: {doi}")


def resolve_from_doi_direct(doi: str) -> dict:
    url = f"https://doi.org/{doi}"
    try:
        response = requests.get(url, headers={"Accept": "application/x-bibtex"})
        print(f"Resolved DOI {doi} with {response.text}")
        if response.status_code == 200:
            # replace month=ssss with month = {ssss} to avoid parsing issues
            response_text = re.sub(
                r"month\s*=\s*([a-zA-Z]+)", r"month = {\1}", response.text
            )
            e = bibtexparser.loads(response_text).entries[0]
            return e
        else:
            print(f"Failed to resolve DOI: {doi}, status code: {response.status_code}")
            raise ValueError(f"Failed to resolve DOI: {doi}")
    except Exception as e:
        print(f"Error resolving DOI {doi}: {e}")
        raise e


resolver_order = [resolve_from_doi_dblp, resolve_from_doi_direct]


def __doi2bib(doi: str):
    """
    Resolve a DOI to a BibTeX entry using DBLP and direct DOI resolution as fallback.

    Args:
        doi (str): The DOI to resolve.
    """
    resolved_entry = None
    for resolver in resolver_order:
        print(f"Trying to resolve DOI {doi} with resolver {resolver.__name__}...")
        try:
            resolved_entry = resolver(doi)
            break
        except Exception as e:
            print(
                f"Error resolving DOI {doi} with resolver {resolver.__name__}: {e}, trying next resolver..."
            )
    if resolved_entry is None:
        print(f"Error resolving DOI {doi}, skipping entry.")
    return resolved_entry


@app.command()
def doi2bib(doi: Annotated[str, typer.Argument()]):
    """
    Resolve a DOI to a BibTeX entry using DBLP and direct DOI resolution as fallback.

    Args:
        doi (str): The DOI to resolve.
    """
    resolved_entry = __doi2bib(doi)
    if resolved_entry is None:
        print(f"Error resolving DOI {doi}, no entry found.")
        return
    single_bib_database = bibtexparser.bibdatabase.BibDatabase()
    single_bib_database.entries = [resolved_entry]
    print(bibtexparser.dumps(single_bib_database))


@app.command()
def cleanup(
    input_path: Annotated[str, typer.Argument()] = "references.bib",
    output_path: Annotated[str, typer.Argument()] = "references_resolved.bib",
    remove_duplicates: bool = True,
    remove_issn: bool = True,
    remove_url: bool = True,
    remove_isbn: bool = True,
    remove_pages: bool = True,
    remove_editor: bool = True,
    preserve_title_capitalization: bool = True,
):
    """
    Convert a BibTeX file by resolving DOIs and reformatting entries.

    Args:
        input_path (str): Path to the input BibTeX file.
        output_path (str): Path to the output BibTeX file.
    """
    bib_file = Path(input_path)
    output_file = Path(output_path)
    if not bib_file.exists():
        typer.echo(f"Input file {bib_file} does not exist.")
        raise typer.Exit(code=1)
    if output_file.exists():
        typer.confirm(
            f"Output file {output_file} already exists. Do you want to overwrite it?",
            abort=True,
        )
    resolved_entries = []
    with open(bib_file) as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file)
        entries = bib_database.entries
        entries_filtered = entries.copy()
        if remove_duplicates:
            non_doi_entries = [e for e in entries if "doi" not in e]
            entries_filtered = non_doi_entries
            doi_entries = [e for e in entries if "doi" in e]
            doi_seen = set()
            for e in doi_entries:
                if e["doi"] not in doi_seen:
                    entries_filtered.append(e)
                    doi_seen.add(e["doi"])

        typer.echo(f"Processing {len(entries_filtered)} entries...")
        for entry in tqdm.tqdm(entries_filtered, desc="Resolving DOIs", unit="entry"):
            resolved_entry = entry
            if "doi" in entry:
                resolved_entry_result = __doi2bib(entry["doi"])
                if resolved_entry_result is not None:
                    resolved_entry = resolved_entry_result
                    resolved_entry["ID"] = entry["ID"]  # Preserve the original ID
                else:
                    print(
                        f"Warning: Could not resolve DOI {entry['doi']} for entry {entry['ID']}. Keeping original entry."
                    )
            resolved_entries.append(resolved_entry)

    for entry in resolved_entries:
        if (
            remove_url
            and ("doi" in entry or "issn" in entry or "isbn" in entry)
            and "url" in entry
        ):
            del entry["url"]
        if remove_issn and "issn" in entry and "isbn" in entry:
            del entry["issn"]
        if remove_issn and "issn" in entry and "doi" in entry:
            del entry["issn"]
        if remove_isbn and "isbn" in entry and "doi" in entry:
            del entry["isbn"]
        if remove_editor and "editor" in entry and "author" in entry:
            del entry["editor"]
        if remove_pages and "pages" in entry:
            del entry["pages"]
        if preserve_title_capitalization and "title" in entry:
            entry["title"] = (
                f"{{{entry['title']}}}"  # Wrap title in extra braces to preserve capitalization
            )
        entry["title"] = re.sub(
            r"<\/?\w+>", "", entry["title"]
        )  # Remove <i> and similar tags
        for k, v in entry.items():
            if "&amp;" in v:
                entry[k] = v.replace("&amp;", "\\&")

    with open(output_file, "w") as bibtex_file:
        bib_database.entries = resolved_entries
        bibtexparser.dump(bib_database, bibtex_file)
