import typer
import glob
import os
import shutil
import subprocess
import zipfile
from pathlib import Path


app = typer.Typer()


@app.command()
def additional_material(
    input_files: list[str] = [
        "video/gibber_demo.mp4",
        "appendix.pdf",
    ],
    output_zip: str = "additional_material.zip",
):
    """
    Generate a ZIP file containing additional material for the project.

    Args:
        input_files (list[str]): List of files to include in the ZIP archive.
        output_zip (str): Output ZIP file name.
    """
    if not input_files:
        print("No input files provided. Exiting.")
        return
    if os.path.exists(output_zip):
        typer.confirm(
            f"Output file {output_zip} already exists. Do you want to overwrite it?",
            abort=True,
        )
    with zipfile.ZipFile(output_zip, "w") as zipf:
        for file in input_files:
            if os.path.exists(file):
                print(f"Adding {file} to the ZIP archive.")
                zipf.write(file, os.path.basename(file))
            else:
                print(
                    f"Warning: {file} does not exist and will not be included in the ZIP."
                )


@app.command()
def sources(
    input_files: list[str] | None = None,
    latexmk: bool = False,
    tikz_external_dir: str = "tikz",
    output_zip: str = "sources.zip",
    verify: bool = False,
    force: bool = False,
):
    """
    Generate a ZIP file containing source files for the project.

    Args:
        input_files (list[str]): List/patterns of source files to include in the ZIP archive.
        latexmk (bool): Include latexmk touched files in the ZIP file.
        tikz_external_dir (str): Directory containing TikZ externalized graphics.
        output_zip (str): Output ZIP file name.
        verify (bool): Verify the integrity of the ZIP file after creation.
    """

    output_zip_path = Path(output_zip)
    if output_zip_path.exists() and not force:
        typer.confirm(
            f"Output file {output_zip} already exists. Do you want to overwrite it?",
            abort=True,
        )
    if input_files is None:
        input_files = ["main.tex", "abstract.tex", "*/.gitkeep"]
    input_files = []
    for file in input_files:
        globbed_files = glob.glob(file, recursive=True)
        input_files.extend(globbed_files)

    if latexmk:
        latexmk_files = []
        for file in input_files:
            fp = Path(file)
            fls_file = fp.with_suffix(".fls")
            if fls_file.exists():
                latexmk_files.append(fls_file)
        for fls_file in latexmk_files:
            with open(fls_file, "r") as f:
                for line in f:
                    if line.startswith("INPUT ./"):
                        print(f"Found INPUT line in {fls_file}: {line.strip()}")
                        input_file = line.split()[1]
                        if os.path.exists(input_file):
                            input_files.append(input_file)
        tikz_external_p = Path(tikz_external_dir)
        tikz_external_p.mkdir(parents=True, exist_ok=True)
        # get the log files
        tikz_log_files = glob.glob(tikz_external_p / "**/*.log", recursive=True)
        for log_file in tikz_log_files:
            with open(log_file, "r") as f:
                for line in f:
                    if line.startswith("File: "):
                        print(f"Found INPUT line in {log_file}: {line.strip()}")
                        input_file = line.split()[1]
                        if os.path.exists(input_file):
                            input_files.append(input_file)

    with zipfile.ZipFile(output_zip_path, "w") as zipf:
        for file in set(input_files):
            print(f"Adding {file} to the ZIP archive.")
            zipf.write(file, file)
    if verify:
        print(
            "Verifying the integrity of the ZIP file & try building the main.tex file with the sources:"
        )
        temp_dir = Path("temp_sources")
        shutil.rmtree(temp_dir, ignore_errors=True)
        temp_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output_zip_path, "r") as zipf:
            zipf.extractall(temp_dir)

            resp = subprocess.run(
                "latexmk -f -shell-escape -pdf  main",
                cwd=temp_dir,
                shell=True,
            )
            result = resp.returncode
            if result == 0:
                print(
                    "Verification successful: The main.tex file compiled successfully."
                )
            else:
                print(
                    f"Verification failed: The main.tex file did not compile successfully. Return code: {result}"
                )
