# Test fixtures

Small input files used by the OdorSig test suite. None are generated at test
time; they are committed so the tests are self-contained.

| File | Used by | Origin |
|------|---------|--------|
| `ethanol.pdb` | `test_pdbqt_conversion.py` | Hand-authored minimal small molecule (3 heavy atoms: C, C, O) for exercising the Open Babel PDB→PDBQT conversion. Synthetic, by design — it only needs to be a valid tiny molecule. |
| `receptor.pdbqt` | `test_docking_smoke.py` | Genuine OdorSig output: prepared receptor **OR7D4** (2885 atoms). |
| `ligand.pdbqt` | `test_docking_smoke.py` | Genuine OdorSig output: prepared ligand **androstenone** (a docking-ready AutoDock ligand with a torsion tree). |

## Provenance of `receptor.pdbqt` / `ligand.pdbqt`

These are **real outputs of the OdorSig pipeline itself**, not synthetic data
and not files from a different docking tool or unrelated project. They come
from the OdorSig **wild-type OR7D4 docking run** that was carried out within
this same OdorSig project and happened to be stored in a working folder used
for the separate SNP paper (`snp paper/docking/wild/dock_Prep/`).

The evidence is in each file's own `REMARK Name` header, which references
OdorSig's own pipeline directory structure (the exact directory names created
by `code/Automation_code/config.py`):

```
receptor.pdbqt:  ...\Automated_Molecular_Docking\model_chain_A_only\OR7D4.pdb
ligand.pdbqt:    ...\Automated_Molecular_Docking\first_stage_model_download\OR7D4_folder\ligands\Androstenone.pdb
```

OR7D4 is one of the 40 receptors and androstenone one of the 12 odorants in the
published 480-pair dataset, so this is a genuine OdorSig receptor–odorant pair.
The docking smoke test uses them purely as fixed, deterministic inputs to check
that the docking step runs and reproduces on a fixed seed; it asserts no
biological result.
