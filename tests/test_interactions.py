"""Regression tests for dataset/code.py's PDBQT atom-type handling.

Background: PDBQT columns 77-78 hold the *AutoDock atom type* (e.g. OA, NA,
HD, A), not a bare element symbol. An earlier version of
``analyze_interactions`` compared that column directly against ``'O'``,
``'N'`` and ``'C'``, which silently excluded the majority of real H-bond
donor/acceptor atoms (typically typed OA/NA, not O/N) and all aromatic
carbons (typed A, not C) from the interaction counts -- undercounting both
H-bonds and hydrophobic contacts. These tests guard against that regressing.

Pure Python: no external tools, no network -- runs in a few seconds.
"""
import importlib.util
import os

import pytest

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")

# dataset/code.py is loaded by explicit path (rather than `import code` or
# adding dataset/ to sys.path) because its module name, "code", collides with
# the Python standard-library `code` module. dataset/code.py also imports
# Biopython/BeautifulSoup/Selenium at module scope for its (untested-here)
# web-automation steps, so importing it requires `pip install -r
# requirements.txt`; skip gracefully rather than failing collection if those
# aren't installed (they are, in CI).
_DATASET_CODE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dataset", "code.py"
)
try:
    _spec = importlib.util.spec_from_file_location("odorsig_dataset_code", _DATASET_CODE_PATH)
    _dataset_code = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_dataset_code)
    AUTODOCK_ATOM_TYPE_TO_ELEMENT = _dataset_code.AUTODOCK_ATOM_TYPE_TO_ELEMENT
    autodock_type_to_element = _dataset_code.autodock_type_to_element
    get_atoms_from_lines = _dataset_code.get_atoms_from_lines
    analyze_interactions = _dataset_code.analyze_interactions
except ImportError as exc:
    pytest.skip(f"dataset/code.py dependencies not installed: {exc}", allow_module_level=True)


def _atom_line(x, y, z, atom_type):
    """Build a minimal ATOM line with x/y/z and atom-type in the exact
    fixed-width columns get_atoms_from_lines() reads (30:38, 38:46, 46:54,
    76:78), matching real PDBQT output."""
    line = list(" " * 80)
    line[0:6] = list("ATOM  ")
    line[30:38] = list(f"{x:8.3f}")
    line[38:46] = list(f"{y:8.3f}")
    line[46:54] = list(f"{z:8.3f}")
    line[76:78] = list(f"{atom_type:>2}")
    return "".join(line) + "\n"


# --- atom-type -> element mapping -----------------------------------------

@pytest.mark.parametrize("atom_type,element", [
    ("OA", "O"),   # H-bond-accepting oxygen (hydroxyl/carbonyl) -- NOT "O"
    ("OS", "O"),
    ("O", "O"),
    ("NA", "N"),   # H-bond-accepting nitrogen -- NOT "N"
    ("NS", "N"),
    ("N", "N"),
    ("HD", "H"),   # H-bond-donor hydrogen -- NOT "H"
    ("HS", "H"),
    ("H", "H"),
    ("A", "C"),    # aromatic carbon -- NOT "C"
    ("C", "C"),
    ("SA", "S"),
    ("S", "S"),
])
def test_autodock_type_to_element_known_types(atom_type, element):
    assert autodock_type_to_element(atom_type) == element


def test_autodock_type_to_element_unknown_type_passthrough():
    # Anything not in the table is preserved rather than silently dropped.
    assert autodock_type_to_element("Zz") == "Zz"


def test_mapping_table_has_no_accidental_identity_only_entries():
    # Sanity check that the table actually distinguishes AutoDock types from
    # bare elements for the common H-bonding types -- if these ever collapsed
    # to identity mappings the whole point of the table would be lost.
    assert AUTODOCK_ATOM_TYPE_TO_ELEMENT["OA"] != "OA"
    assert AUTODOCK_ATOM_TYPE_TO_ELEMENT["NA"] != "NA"
    assert AUTODOCK_ATOM_TYPE_TO_ELEMENT["HD"] != "HD"
    assert AUTODOCK_ATOM_TYPE_TO_ELEMENT["A"] != "A"


# --- get_atoms_from_lines on real OdorSig output ---------------------------

def test_receptor_fixture_OA_and_NA_atoms_resolve_to_O_and_N():
    """tests/fixtures/receptor.pdbqt is a genuine OdorSig-prepared receptor
    (OR7D4) and, like any real protein PDBQT, carries OA/NA/A-typed atoms for
    its polar and aromatic residues. Confirm they resolve to elements, not
    raw AutoDock type strings."""
    with open(os.path.join(FIXTURES, "receptor.pdbqt")) as f:
        atoms = get_atoms_from_lines(f.readlines())

    elements = {a["elem"] for a in atoms}
    # Every previously-mis-set raw type string must be gone...
    assert "OA" not in elements
    assert "NA" not in elements
    assert "HD" not in elements
    # ...and resolved to proper elements.
    assert {"O", "N", "C", "S"} <= elements

    n_oxygens = sum(1 for a in atoms if a["elem"] == "O")
    n_nitrogens = sum(1 for a in atoms if a["elem"] == "N")
    # A ~360-residue receptor has hundreds of backbone/sidechain O and N
    # atoms; under the old bug (elem == raw type 'OA'/'NA') these would be 0
    # or near-0 because almost all protein O/N atoms are typed OA/NA, not
    # bare O/N.
    assert n_oxygens > 100, f"suspiciously few oxygens resolved: {n_oxygens}"
    assert n_nitrogens > 100, f"suspiciously few nitrogens resolved: {n_nitrogens}"


def test_receptor_fixture_aromatic_carbons_resolve_to_C():
    """The receptor fixture contains 'A' (aromatic carbon) typed atoms, e.g.
    from Phe/Tyr/Trp/His rings; they must count as carbon."""
    with open(os.path.join(FIXTURES, "receptor.pdbqt")) as f:
        raw_types = {ln[76:78].strip() for ln in f if ln.startswith(("ATOM", "HETATM"))}
    assert "A" in raw_types, "fixture no longer has aromatic-carbon atoms; test needs updating"

    with open(os.path.join(FIXTURES, "receptor.pdbqt")) as f:
        atoms = get_atoms_from_lines(f.readlines())
    n_carbons = sum(1 for a in atoms if a["elem"] == "C")
    n_lines = sum(1 for a in atoms)
    # Carbon (C + aromatic A) is the majority element in any protein.
    assert n_carbons > n_lines * 0.4


# --- analyze_interactions end to end ---------------------------------------

def _write_ligand_pose(path, atoms):
    """Write a single-pose ligand PDBQT (MODEL/ENDMDL wrapped, as Vina
    output looks) containing the given (x, y, z, atom_type) atoms."""
    with open(path, "w") as f:
        f.write("MODEL 1\n")
        for x, y, z, atype in atoms:
            f.write(_atom_line(x, y, z, atype))
        f.write("ENDMDL\n")


def test_hbond_counted_between_OA_and_NA_atoms(tmp_path):
    """Regression test for the core bug: a receptor OA atom and a ligand NA
    atom 1.0 A apart (well within the 3.5 A H-bond cutoff) must be counted.
    Under the pre-fix code (elem == 'O'/'N' against raw AutoDock types) this
    pair would contribute zero H-bonds because 'OA' != 'O' and 'NA' != 'N'."""
    receptor_path = tmp_path / "receptor.pdbqt"
    ligand_path = tmp_path / "ligand_out.pdbqt"

    with open(receptor_path, "w") as f:
        f.write(_atom_line(0.0, 0.0, 0.0, "OA"))

    _write_ligand_pose(ligand_path, [(1.0, 0.0, 0.0, "NA")])

    results = analyze_interactions(str(receptor_path), str(ligand_path))
    assert len(results) == 1
    assert results[0]["h_bonds"] == 1, (
        "OA (receptor) / NA (ligand) atoms 1.0 A apart were not counted as "
        "an H-bond -- the AutoDock atom-type bug has regressed"
    )


def test_hydrophobic_counted_between_aromatic_carbons(tmp_path):
    """A receptor aromatic carbon (type 'A') and a ligand aromatic carbon,
    2.0 A apart (within the 4.5 A hydrophobic cutoff), must be counted.
    Under the pre-fix code, type 'A' != 'C' so aromatic rings were excluded
    from hydrophobic-contact counts entirely."""
    receptor_path = tmp_path / "receptor.pdbqt"
    ligand_path = tmp_path / "ligand_out.pdbqt"

    with open(receptor_path, "w") as f:
        f.write(_atom_line(0.0, 0.0, 0.0, "A"))

    _write_ligand_pose(ligand_path, [(2.0, 0.0, 0.0, "A")])

    results = analyze_interactions(str(receptor_path), str(ligand_path))
    assert len(results) == 1
    assert results[0]["hydrophobic"] == 1, (
        "aromatic-carbon (type 'A') atoms 2.0 A apart were not counted as a "
        "hydrophobic contact -- the AutoDock atom-type bug has regressed"
    )


def test_no_hbond_when_out_of_range(tmp_path):
    receptor_path = tmp_path / "receptor.pdbqt"
    ligand_path = tmp_path / "ligand_out.pdbqt"

    with open(receptor_path, "w") as f:
        f.write(_atom_line(0.0, 0.0, 0.0, "OA"))

    _write_ligand_pose(ligand_path, [(10.0, 0.0, 0.0, "NA")])

    results = analyze_interactions(str(receptor_path), str(ligand_path))
    assert results[0]["h_bonds"] == 0
