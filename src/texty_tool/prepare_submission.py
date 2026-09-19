import re
from typing import Annotated, Iterator

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


def rewrite_flatten(
    cmd_name: str, cmd_arg: str, _content: str, dest_file: str, temp_dir: Path
) -> str:
    content = _content
    cmd = (
        cmd_name
        if not re.match(r"[ \(\)\\\\ \\\{\}]", cmd_name)
        and len(cmd_name) < 32
        and "def" not in cmd_name
        else ""
    )
    # cmd = f"\\\\{cmd_name}" if len(cmd_name) > 0 else ""
    # print(f"\t\tProcessing command {cmd} with argument {cmd_arg}.")
    regex_pattern = rf"{cmd}\{{({cmd_arg})\}}"
    # print(f"\t\tSearching for pattern {regex_pattern} in {dest_file}.")
    all_runs = re.finditer(regex_pattern, content)

    run = next(all_runs, None)
    if run is None:
        print(f"\t\t!! No runs found for {cmd_name}{{{cmd_arg}}} in {dest_file}.")
        return content
    # print(f"\t\tFound {cmd}{{{run.group(1)}}} in {dest_file}.")

    run_path = Path(run.group(1))
    if run_path.is_absolute():
        # print(f"\t\tFound absolute path {run_path} in {dest_file}.")
        return content
    if not run_path.suffix:
        # try to find the file with any extension
        found_files = list(Path(".").rglob(f"{run.group(1)}.*"))
        found_files = [
            f
            for f in found_files
            if f.is_file()
            and f.suffix not in [".aux", ".log", ".fls", ".fdb_latexmk", ".typ"]
        ]
        if found_files:
            run_path = found_files[0]
    if run_path.exists():
        # print(f"\t\tFound existing file {run_path} in {dest_file}.")
        dest_run_path = temp_dir / ("_".join(run_path.parts))
        print(
            f"\t\t-> Replacing {run_path} to {dest_run_path.name} for command {cmd}{{{cmd_arg}}}."
        )
        # replace all occurrences of the original file name with the new flattened name
        dest_cmd_arg = str(dest_run_path.name)
        protected_extensions = [".cls", ".sty"]
        if run_path.suffix in protected_extensions:
            dest_cmd_arg = dest_cmd_arg.replace(run_path.suffix, "")
        content = (
            content[: run.start()]
            + cmd.removeprefix("\\")
            + "{"
            + dest_cmd_arg
            + "}"
            + content[run.end() :]
        )
    return content


@app.command()
def sources(
    input_files: Annotated[list[str] | None, typer.Option()] = None,
    latexmk: Annotated[
        bool, typer.Option(help="Include latexmk touched files in the ZIP file.")
    ] = True,
    main_file: Annotated[
        str, typer.Option(help="Main LaTeX file to compile for verification.")
    ] = "main.tex",
    tikz_external_dir: str = "tikz",
    tmp_dir: str = "temp_sources",
    tmp_build_dir: str = "temp_build",
    output_zip: str = "sources.zip",
    verify: bool = False,
    force: bool = False,
    rerun: bool = False,
    flatten: bool = False,
):
    """
    Generate a ZIP file containing source files for the project.

    Args:
        input_files (list[str]): List/patterns of source files to include in the ZIP archive.
        latexmk (bool): Include latexmk touched files in the ZIP file.
        tikz_external_dir (str): Directory containing TikZ externalized graphics.
        output_zip (str): Output ZIP file name.
        verify (bool): Verify the integrity of the ZIP file after creation.
        force (bool): Overwrite existing output ZIP file without confirmation.
        rerun (bool): Rerun the LaTeX compilation for verification.
        flatten (bool): Flatten the directory structure in the ZIP file (Useful for submissions to conferences/journals that require a flat structure, e.g. Elsevier).
    """

    output_zip_path = Path(output_zip)
    if output_zip_path.exists():
        if not force:
            typer.confirm(
                f"Output file {output_zip} already exists. Do you want to overwrite it?",
                abort=True,
            )
        print(f"Output file {output_zip} already exists. Overwriting it.")
    if input_files is None:
        input_files = ["main.tex", "abstract.tex", "*/.gitkeep"]

    # 1. Collect all input files based on the provided patterns
    _input_files: list[Path] = []
    for file in input_files:
        print(f"Processing input file/pattern: {file}")
        globbed_files = glob.glob(file, recursive=True)
        _input_files.extend(globbed_files)

    _input_files = [Path(f) for f in _input_files if Path(f).exists()]
    # 2. Include latexmk touched files if requested
    if latexmk:
        print("Including latexmk touched files in the ZIP file.")
        latexmk_files = []
        for file in _input_files:
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
                            _input_files.append(Path(input_file))
        tikz_external_p = Path(tikz_external_dir)
        tikz_external_p.mkdir(parents=True, exist_ok=True)
        # 2.1 Get the log files - these contain the INPUT lines for the externalized TikZ graphics
        tikz_log_files = tikz_external_p.rglob("**/*.log")
        for log_file in tikz_log_files:
            with open(log_file, "r", encoding="latin-1") as f:
                for line in f:
                    if line.startswith("File: "):
                        print(f"Found INPUT line in {log_file}: {line.strip()}")
                        input_file = line.split()[1]
                        if os.path.exists(input_file):
                            _input_files.append(Path(input_file))
    # 3. Flatten the directory structure if requested
    if flatten:
        print("Flattening the directory structure in the ZIP file.")
        # copy all files to a temporary directory and add them to the ZIP from there
        temp_dir = Path(tmp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
        temp_dir.mkdir(parents=True, exist_ok=True)
        if tikz_external_dir:
            tikz_temp_dir = temp_dir / Path(tikz_external_dir).name
            tikz_temp_dir.mkdir(parents=True, exist_ok=True)

        unflattened_files = [f for f in set(_input_files) if f.is_file()]
        mapped_file = {
            file: temp_dir / ("_".join(file.parts)) for file in set(unflattened_files)
        }
        print(f"Flattening {len(unflattened_files)} files into {temp_dir}.")

        _input_files = list(mapped_file.values())

        for file, dest_file in mapped_file.items():
            print(f"\t-> Copying {file} to {dest_file}.")
            shutil.copy(file, dest_file)
            if dest_file.suffix not in [".tex", ".sty", ".cls"]:
                print(f"\t-> Skipping content modification for {dest_file}.")
                continue
            with open(file, "r", errors="ignore", encoding="utf-8") as f:
                content = f.read()
                cmd_matches: list[tuple[str, str]] = []
                # for cmd in commands:
                #     matches = list(re.finditer(rf"({cmd})\{{(.*?)\}}", content))
                #     cmd_matches.extend([(m.group(1), m.group(2)) for m in matches])
                for file in set(mapped_file.keys()):
                    # print(
                    #     f"\t\tChecking for additional matches for {file} in {dest_file}."
                    # )
                    file_without_ext = file.with_suffix("")

                    matches = list(
                        re.finditer(rf"\\(.*?)\{{({file_without_ext})}}", content)
                    ) + list(re.finditer(rf"\\(.*?)\{{({file})}}", content))
                    matches = [
                        (m.group(1), m.group(2))
                        for m in matches
                        # if m.group(1) not in original_match_files
                    ]
                    protecteded_commands = [
                        "begin",
                        "end",
                        "documentclass",
                        "usepackage",
                    ]
                    if len(matches) > 0:
                        matches = [
                            (cmd, arg)
                            for cmd, arg in matches
                            if cmd not in protecteded_commands
                        ]
                    if len(matches) > 0:
                        print(
                            f"\t\t? Found {matches} addtional matches for {file} in {dest_file}."
                        )
                    cmd_matches.extend(matches)

                # print(
                #     f"\t\tFound {len(original_matches)} original matches in {dest_file}."
                # )
                for cmd_name, cmd_arg in cmd_matches:
                    content = rewrite_flatten(
                        cmd_name, cmd_arg, content, dest_file, temp_dir
                    )
                with open(dest_file, "w", errors="ignore") as f:
                    f.write(content)

    print(f"Creating ZIP file {output_zip} with {len(set(_input_files))} unique files.")
    with zipfile.ZipFile(output_zip_path, "w") as zipf:
        for file in set(_input_files):
            print(f"Adding {file} to the ZIP archive.")
            if flatten:
                zipf.write(file, file.name)
            else:
                zipf.write(file, file)
    if verify:
        print(
            "Verifying the integrity of the ZIP file & try building the main.tex file with the sources:"
        )
        if rerun:
            resp = subprocess.run(
                "latexmk -f -shell-escape -pdf -c  main",
                cwd=".",
                shell=True,
            )
            resp = subprocess.run(
                "latexmk -f -shell-escape -pdf main",
                cwd=".",
                shell=True,
            )
        temp_build_dir = Path(tmp_build_dir)
        shutil.rmtree(temp_build_dir, ignore_errors=True)
        temp_build_dir.mkdir(parents=True, exist_ok=True)
        tikz_temp_build_dir = temp_build_dir / tikz_external_dir
        tikz_temp_build_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output_zip_path, "r") as zipf:
            zipf.extractall(temp_build_dir)

            resp = subprocess.run(
                "latexmk -f -shell-escape -pdf  main",
                cwd=temp_build_dir,
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
