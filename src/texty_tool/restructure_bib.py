import logging
import re
import time
import traceback
from pathlib import Path
from typing import Annotated

import bibtexparser
import pandas as pd
import requests
import tqdm
import typer
from pylatexenc.latexencode import unicode_to_latex
from rdflib.plugins.stores.sparqlstore import SPARQLStore
from rdflib.query import Result
from rdflib.term import Literal, URIRef

app = typer.Typer()

# %%
graph = SPARQLStore("https://sparql.dblp.org/sparql", method="POST")
INT_COMPATIBLE_TYPES = [
    "http://www.w3.org/2001/XMLSchema#int",
    "http://www.w3.org/2001/XMLSchema#integer",
    "http://www.w3.org/2001/XMLSchema#positiveInteger",
    "http://www.w3.org/2001/XMLSchema#nonNegativeInteger",
]
FLOAT_COMPATIBLE_TYPES = [
    "http://www.w3.org/2001/XMLSchema#float",
    "http://www.w3.org/2001/XMLSchema#double",
    "http://www.w3.org/2001/XMLSchema#decimal",
    # kilogram, seconds
]

prefixes = {
    "dblp": "https://dblp.org/rdf/schema#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "foaf": "http://xmlns.com/foaf/0.1/",
    "bibtex": "http://purl.org/net/nknouf/ns/bibtex",
}
logger = logging.getLogger(__name__)


def remove_prefix(uri: str) -> str:
    for prefix, namespace in prefixes.items():
        if uri.startswith((f"<{namespace}", f"{namespace}")):
            offset = 1 if uri.startswith("<") else 0
            end_offset = -1 if uri.endswith(">") else None
            return f"{prefix}:{uri[len(str(namespace)) + offset : end_offset]}"
    return uri


def remove_ns_from_df(df: pd.DataFrame) -> pd.DataFrame:
    df_c = df.copy()
    for column in df.columns:
        df_c[column] = df.apply(lambda row: remove_prefix(str(row[column])), axis=1)
    return df_c


def q_to_df_values(qres: Result, remove_ns: bool = True) -> pd.DataFrame:
    if isinstance(qres, tuple):
        logger.error(f"Query failed: {qres}")
        raise ValueError(f"Query failed: {qres}")
    if not qres.vars:
        return pd.DataFrame()
    cols = [str(var) for var in qres.vars]
    results = [dict(zip(cols, row)) for row in qres]  # type: ignore
    results_df = pd.DataFrame(results)
    results_df = results_df.map(to_readable)
    if remove_ns:
        results_df = remove_ns_from_df(results_df)
    return results_df


def to_readable(cls: str | Literal | URIRef):
    if isinstance(cls, Literal):
        value = cls.title()
        if cls.datatype is not None:
            try:
                cls_dtype = str(cls.datatype)
                if cls_dtype in INT_COMPATIBLE_TYPES:
                    value = int(value)
                elif (
                    cls_dtype in FLOAT_COMPATIBLE_TYPES
                    or "kilogram" in cls.datatype
                    or "metre" in cls.datatype
                    or "seconds" in cls.datatype
                    or "minute" in cls.datatype
                    or "hour" in cls.datatype
                    or "day" in cls.datatype
                ):
                    value = float(value)
            except Exception as e:
                logger.error(f"Error converting {value} to int or float: {e}")
                print(traceback.format_exc())
                print("Failed to convert", value, "to int or float", e)
        return str(cls)  # Return the string representation of the Literal
    return str(cls)
    # elif isinstance(cls, URIRef) or hasattr(cls, "n3"):
    #     return cls.n3(graph.namespace.namespace_manager)  # type: ignore
    # else:
    #     return cls


# %%
def query_dblp(q: str) -> pd.DataFrame:
    resp = graph.query(f"""
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
{q}
""")
    try:
        keys = q_to_df_values(resp, remove_ns=True)
    except Exception as e:
        logger.error(f"Error occurred while querying DBLP: {e} (query: {q})")
        raise
    return keys


def resolve_from_doi_dblp(doi: str) -> dict:

    try:
        keys = query_dblp(f"""
    SELECT ?s ?k ?v WHERE {{
    ?s rdf:type dblp:Publication .
    ?s dblp:doi <https://doi.org/{doi}>;
    ?k ?v .
    }}
    """)
        if keys.empty:
            raise ValueError(f"No results found in DBLP for DOI: {doi}")
        authors = query_dblp(f"""
    SELECT ?sign ?s ?author ?author_name ?ord WHERE {{
    ?s rdf:type dblp:Publication .
    ?s dblp:doi <https://doi.org/{doi}>.
    ?sign dblp:signaturePublication ?s.
    ?sign dblp:signatureOrdinal ?ord .
    ?sign dblp:signatureCreator ?author .
    ?author dblp:creatorName ?author_name .
    }} ORDER BY ?ord
    """)
        partOf = query_dblp(f"""SELECT ?s ?publ ?k ?v WHERE {{
  ?s rdf:type dblp:Publication .
  ?s dblp:doi <https://doi.org/{doi}>.
  ?s dblp:publishedAsPartOf ?publ.
  ?publ ?k ?v .
}}""")
        entry_keys = {row["k"]: row["v"] for _, row in keys.iterrows()}
        partOf_keys = {row["k"]: row["v"] for _, row in partOf.iterrows()}
        editors = pd.DataFrame()
        if not partOf.empty:
            editors = query_dblp(f"""
            SELECT ?editor ?editor_name ?ord WHERE {{
            <{entry_keys.get("dblp:publishedAsPartOf", "")}>  dblp:hasSignature ?sign .
            ?sign dblp:signaturePublication ?s.
            ?sign dblp:signatureOrdinal ?ord .
            ?sign dblp:signatureCreator ?editor .
            ?editor dblp:creatorName ?editor_name .
            }} ORDER BY ?ord
            """)
        bibtex_type = entry_keys.get("dblp:bibtexType", "article").lower()
        bibtex_type = re.sub(r"bibtex:", "", bibtex_type).strip()
        entry = {
            "doi": doi,
            "ID": doi.replace("/", "_"),
            "ENTRYTYPE": bibtex_type.lstrip("#"),
        }

        def author_name_to_bibtex(name: str) -> str:
            parts = name.split(" ")
            parts = [part.strip() for part in parts]
            final_name = parts[-1] + ", " + " ".join(parts[:-1])
            return name  # final_name

        if not authors.empty:
            entry["author"] = " and ".join(
                [
                    author_name_to_bibtex(row["author_name"])
                    for _, row in authors.iterrows()
                ]
            )
        if not editors.empty:
            entry["editor"] = " and ".join(
                [
                    author_name_to_bibtex(row["editor_name"])
                    for _, row in editors.iterrows()
                ]
            )
        kv_pairs = {
            "dblp:title": "title",
            "dblp:month": "month",
            "dblp:publishedInJournalVolume": "volume",
            "dblp:publishedInJournalVolumeIssue": "number",
            "dblp:pagination": "pages",
            "dblp:publishedInJournal": "journal",
            "dblp:yearOfPublication": "year",
            "dblp:yearOfEvent": "year",
        }
        for dblp_key, bibtex_key in kv_pairs.items():
            if dblp_key in entry_keys:
                entry[bibtex_key] = str(entry_keys.get(dblp_key, ""))
        if not partOf.empty:
            kv_pairs_partOf = {
                "dblp:title": "booktitle",
                "dblp:publishedBy": "publisher",
            }
            for dblp_key, bibtex_key in kv_pairs_partOf.items():
                if dblp_key in partOf_keys:
                    entry[bibtex_key] = str(partOf_keys.get(dblp_key, ""))
        assert "title" in entry, f"Missing title for DOI {doi}"

        return entry
    except Exception as e:
        print(f"Error resolving DOI {doi} from DBLP: {e}")
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
    remove_pages: bool = False,
    remove_editor: bool = True,
    preserve_title_capitalization: bool = True,
    sleep_time: float = 0,
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
                    if "title" not in resolved_entry or not resolved_entry["title"]:
                        resolved_entry = (
                            entry  # Fallback to original entry if title is missing
                        )
                        print(
                            f"Warning: Resolved entry for DOI {entry['doi']} is missing title. Keeping original entry."
                        )
                    resolved_entry["ID"] = entry["ID"]  # Preserve the original ID
                    if sleep_time > 0:
                        time.sleep(sleep_time)  # Sleep to avoid rate limiting
                else:
                    print(
                        f"Warning: Could not resolve DOI {entry['doi']} for entry {entry['ID']}. Keeping original entry."
                    )
            resolved_entries.append(resolved_entry)

    for entry in resolved_entries:
        for k, v in entry.items():
            if "&amp;" in v:
                entry[k] = v.replace("&amp;", "\\&")
            if isinstance(v, str):
                entry[k] = unicode_to_latex(v)
            if "\\&amp;" in entry[k]:
                entry[k] = entry[k].replace("\\&amp;", "\\&")
        try:
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
                if "booktitle" in entry:
                    entry["booktitle"] = f"{{{entry['booktitle']}}}"
                if "journal" in entry:
                    entry["journal"] = f"{{{entry['journal']}}}"
                if "publisher" in entry:
                    entry["publisher"] = f"{{{entry['publisher']}}}"
            entry["title"] = re.sub(
                r"<\/?\w+>", "", entry["title"]
            )  # Remove <i> and similar tags
        except Exception as e:
            print(
                f"Error processing entry {entry.get('ID', 'unknown')} / {entry.get('title', 'unknown')}: {e}"
            )
            print(traceback.format_exc())
            continue
    with open(output_file, "w") as bibtex_file:
        bib_database.entries = resolved_entries
        bibtexparser.dump(bib_database, bibtex_file)
