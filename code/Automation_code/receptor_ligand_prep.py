"""Shared receptor/ligand file-preparation primitives.

Extracted so that the interactive-app pipeline (Step_03_prepare_receptor_ligand.py,
driven by code/app.py) and the batch dataset-generation pipeline
(dataset/code.py, used to produce the deposited 480-pair dataset) call one
implementation instead of two independently-written, divergent copies of the
same chain-A-extraction and Open Babel conversion logic.

Both call sites pass their own parameters explicitly (obabel path, flags,
buffer, exhaustiveness, etc.) -- this module does not hardcode any docking or
chemistry parameter, so refactoring either caller to use it does not change
any existing numeric behaviour.
"""
import subprocess


def extract_chain_a(input_pdb_path, output_pdb_path, chain_id="A"):
    """Filter a PDB file down to ATOM/HETATM records for one chain (default
    'A'), preserving the END record, exactly as both pipelines previously did
    with their own separate copies of this loop.

    Args:
        input_pdb_path: source PDB file (e.g. a raw SWISS-MODEL output).
        output_pdb_path: destination path for the single-chain PDB.
        chain_id: single-character chain identifier to keep (PDB column 22 /
            0-indexed line[21]).
    """
    with open(input_pdb_path, "r") as infile, open(output_pdb_path, "w") as outfile:
        for line in infile:
            if line.startswith(("ATOM", "HETATM")) and line[21] == chain_id:
                outfile.write(line)
            elif line.startswith("END"):
                outfile.write(line)


def convert_to_pdbqt(obabel_path, input_path, output_path, receptor=False,
                      capture_output=False, check=True):
    """Convert a structure file to AutoDock PDBQT via Open Babel, adding
    hydrogens and Gasteiger partial charges.

    Args:
        obabel_path: path/command for the Open Babel executable.
        input_path: source file (PDB or SDF -- Open Babel selects its parser
            from the file extension, so either input works unchanged).
        output_path: destination .pdbqt path.
        receptor: if True, adds the '-xr' flag (treat the incoming molecule
            as a rigid receptor), matching both pipelines' existing receptor
            conversion calls. Ligand conversions omit this flag.
        capture_output: passed straight through to subprocess.run -- the two
            existing call sites disagree on this (the interactive app streams
            Open Babel's own progress output to the console; the batch
            dataset generator captures it silently), so callers choose it
            explicitly rather than this function picking a default that would
            change either one's existing behaviour.
        check: passed straight through to subprocess.run.

    Returns:
        The subprocess.CompletedProcess from the Open Babel invocation.
    """
    cmd = [obabel_path, input_path, "-O", output_path]
    if receptor:
        cmd.append("-xr")
    cmd.extend(["-h", "--partialcharge", "gasteiger"])
    return subprocess.run(cmd, check=check, capture_output=capture_output)
