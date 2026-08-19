#!/usr/bin/env python3
"""OdorSig command-line interface.

Wraps the existing pipeline functions in Automation_code/ (the same
functions code/app.py's Streamlit interface calls) and dataset/code.py (the
batch dataset generator) behind a single entry point, so a user or a CI job
does not need to read Streamlit source or edit module-level constants to run
the pipeline. This is glue code only -- it adds no new docking, modelling,
or scoring logic; every subcommand below calls functions that already exist
elsewhere in this repository.

Usage (run from the `code/` directory, same convention as `streamlit run
app.py`):

    python cli.py run --receptor OR7D4 --ligands Androstenone
    python cli.py run --receptor OR1A1 --ligands "Citral,Carvone" --seed 111 222 333
    python cli.py batch --input ../dataset/pair_list.xlsx
    python cli.py reproduce ../examples/OR7D4_androstenone

Environment variables (ODORSIG_ENTREZ_EMAIL, ODORSIG_VINA_EXE, etc.) are
read the same way they always have been -- see config.py and .env.example.
This CLI does not introduce a second configuration mechanism.
"""
import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def _cmd_run(args):
    """Single receptor + one or more ligands, end-to-end -- the same
    Step_01 -> Step_05 sequence code/app.py drives from the Streamlit UI.
    Defaults (exhaustiveness=8, num_modes=10, energy_range=3) match the
    interactive app's own default slider values, not the batch dataset
    generator's (exhaustiveness=16, energy_range=4) -- `run` is the
    single-pair/interactive-equivalent path; use `batch` for the large-scale
    dataset parameters.
    """
    from Automation_code import config
    from Automation_code.Step_01_downloading_model_ligands import process_receptor_from_input
    from Automation_code.Step_02_validate_model_structure import assess_model
    from Automation_code.Step_03_prepare_receptor_ligand import prepare_receptor_and_ligands
    from Automation_code.Step_04_config_file import create_all_configs_for_receptor
    from Automation_code.Step_05_docking import run_all_dockings_for_receptor

    ligands = [l.strip() for l in args.ligands.split(",") if l.strip()]
    seed_list = args.seed if args.seed else None  # None -> random-seed mode, matching app.py

    print(f"[1/5] Downloading receptor + ligand structures for {args.receptor}...")
    ok, err = process_receptor_from_input(args.receptor, ligands, st_callback=print)
    if not ok:
        print(f"FAILED at receptor/ligand download: {err}")
        return 1

    print(f"[2/5] Structural validation (SWISS-MODEL assessment) for {args.receptor}...")
    ok, err = assess_model(args.receptor, st_callback=print)
    if not ok:
        print(f"FAILED at structural validation: {err}")
        return 1

    print("[3/5] Preparing receptor/ligand PDBQT files...")
    ok, errors = prepare_receptor_and_ligands(args.receptor, st_callback=print)
    if not ok:
        print(f"FAILED at receptor/ligand preparation: {errors}")
        return 1

    print("[4/5] Generating docking configuration...")
    create_all_configs_for_receptor(
        args.receptor,
        exhaustiveness=args.exhaustiveness,
        num_modes=args.num_modes,
        energy_range=args.energy_range,
    )

    print("[5/5] Running AutoDock Vina...")
    result = run_all_dockings_for_receptor(
        args.receptor, config.PREPARED_MODELS_DIR, seed_list
    )
    print(result)
    return 0


def _cmd_batch(args):
    """Large-scale batch docking from an Excel receptor/ligand pair list --
    wraps dataset/code.py's existing main() + master_organizer(), which
    together produced the deposited 480-pair dataset. Docking parameters
    (seeds [100, 200, 300], exhaustiveness=16, energy_range=4) are that
    module's own existing constants and are not altered here.
    """
    import os

    if args.input:
        os.environ["ODORSIG_PAIR_LIST_XLSX"] = str(Path(args.input).resolve())
    if args.output_dir:
        out = Path(args.output_dir).resolve()
        os.environ.setdefault("ODORSIG_DATASET_RECEPTOR_DIR", str(out / "receptors"))
        os.environ.setdefault("ODORSIG_DATASET_LIGAND_DIR", str(out / "ligands"))
        os.environ.setdefault("ODORSIG_DATASET_OUTPUT_DIR", str(out / "outputs"))

    dataset_dir = Path(__file__).resolve().parent.parent / "dataset"
    sys.path.insert(0, str(dataset_dir))
    import importlib.util
    spec = importlib.util.spec_from_file_location("odorsig_dataset_batch", dataset_dir / "code.py")
    dataset_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dataset_module)

    dataset_module.main()
    dataset_module.master_organizer()
    return 0


def _cmd_reproduce(args):
    """Regenerate a worked example's expected_output/ from scratch by
    invoking that example's own run_example.py (unchanged) as a subprocess.
    Currently only examples/OR7D4_androstenone/ exists; this subcommand does
    not hardcode that path -- it looks for run_example.py inside whatever
    directory is passed in.
    """
    example_dir = Path(args.example_dir).resolve()
    script = example_dir / "run_example.py"
    if not script.is_file():
        print(f"No run_example.py found in {example_dir}")
        return 1
    print(f"Running {script} (requires the vina executable on PATH)...")
    return subprocess.call([sys.executable, str(script)])


def build_parser():
    parser = argparse.ArgumentParser(
        prog="odorsig",
        description="OdorSig command-line interface (glue code around the existing pipeline).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="Dock one receptor against one or more ligands, end-to-end.")
    p_run.add_argument("--receptor", required=True, help="Receptor gene symbol, e.g. OR7D4")
    p_run.add_argument("--ligands", required=True, help="Comma-separated ligand names, e.g. Citral,Carvone")
    p_run.add_argument("--seed", type=int, nargs="+", default=None,
                        help="One or more fixed integer seeds (omit for random-seed mode)")
    p_run.add_argument("--exhaustiveness", type=int, default=8,
                        help="Vina exhaustiveness (default 8, matching the interactive app's default)")
    p_run.add_argument("--num-modes", type=int, default=10, dest="num_modes",
                        help="Number of poses per run (default 10)")
    p_run.add_argument("--energy-range", type=int, default=3, dest="energy_range",
                        help="Vina energy range in kcal/mol (default 3, matching the interactive app's default)")
    p_run.set_defaults(func=_cmd_run)

    p_batch = sub.add_parser("batch", help="Run the large-scale batch pipeline from an Excel pair list.")
    p_batch.add_argument("--input", default=None,
                          help="Path to the receptor/ligand pair-list .xlsx "
                               "(overrides ODORSIG_PAIR_LIST_XLSX for this run)")
    p_batch.add_argument("--output-dir", default=None, dest="output_dir",
                          help="Root directory for receptors/ligands/outputs "
                               "(overrides the ODORSIG_DATASET_* directories for this run "
                               "if they are not already set)")
    p_batch.set_defaults(func=_cmd_batch)

    p_repro = sub.add_parser("reproduce", help="Regenerate a worked example's expected_output/.")
    p_repro.add_argument("example_dir", help="Path to a worked-example directory, "
                                              "e.g. examples/OR7D4_androstenone")
    p_repro.set_defaults(func=_cmd_reproduce)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
