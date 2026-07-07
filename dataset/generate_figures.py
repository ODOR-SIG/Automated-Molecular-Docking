"""
Reproduce the manuscript's dataset-level figures (Fig. 2-5, 7-8) directly from
the deposited results file, Final_Docking_Results.xlsx.

This closes a reproducibility gap: the 480-pair Executive_Summary numbers
(strong/moderate/weak split, high-confidence quadrant, Ramachandran stats)
were previously verifiable only by recomputing them by hand from the raw
spreadsheet. Running this script regenerates the figures themselves and
prints the same summary statistics quoted in the manuscript, so a reviewer
(or anyone re-running the pipeline) can check both at once.

Usage:
    cd dataset
    python generate_figures.py [--input Final_Docking_Results.xlsx] [--out figures/]

Binding-strength thresholds (kept in sync with code/Automation_code/config.py
and the manuscript's Results section):
    strong   : dG <= -7.0 kcal/mol
    moderate : -7.0 < dG <= -5.0 kcal/mol
    weak     : dG > -5.0 kcal/mol
"""

import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

try:
    from scipy.cluster.hierarchy import leaves_list, linkage
    HAVE_SCIPY = True
except ImportError:
    HAVE_SCIPY = False

STRONG_CUTOFF = -7.0
MODERATE_CUTOFF = -5.0
REPRODUCIBILITY_CUTOFF = 0.2


def classify(dg):
    if dg <= STRONG_CUTOFF:
        return "Strong"
    if dg <= MODERATE_CUTOFF:
        return "Moderate"
    return "Weak"


def cluster_order(matrix):
    """Return a hierarchical-clustering leaf order for the rows of `matrix`.
    Falls back to sorting by row mean if scipy is unavailable."""
    if HAVE_SCIPY and matrix.shape[0] > 2:
        link = linkage(matrix, method="average", metric="euclidean")
        return leaves_list(link)
    return np.argsort(matrix.mean(axis=1))


def load_data(path):
    summary = pd.read_excel(path, sheet_name="Executive_Summary")
    validation = pd.read_excel(path, sheet_name="Validation_All")
    return summary, validation


def print_summary_stats(df):
    n = len(df)
    sigma_lt_02 = (df["Std_Deviation"] < REPRODUCIBILITY_CUTOFF).sum()
    sigma_eq_0 = (df["Std_Deviation"] == 0).sum()
    classes = df["Average_Affinity"].apply(classify)
    strong, moderate, weak = (classes == "Strong").sum(), (classes == "Moderate").sum(), (classes == "Weak").sum()
    high_conf = ((df["Average_Affinity"] <= STRONG_CUTOFF) & (df["Std_Deviation"] <= REPRODUCIBILITY_CUTOFF)).sum()

    print(f"Pairs: {n} ({df['Receptor'].nunique()} receptors x {df['Ligand'].nunique()} odorants)")
    print(f"sigma < {REPRODUCIBILITY_CUTOFF}: {sigma_lt_02} ({100*sigma_lt_02/n:.1f}%); sigma == 0: {sigma_eq_0}")
    print(f"Strong: {strong} ({100*strong/n:.1f}%)  Moderate: {moderate} ({100*moderate/n:.1f}%)  Weak: {weak} ({100*weak/n:.1f}%)")
    print(f"High-confidence (dG <= {STRONG_CUTOFF}, sigma <= {REPRODUCIBILITY_CUTOFF}): {high_conf}")


def fig2_heatmap(df, out_dir):
    pivot = df.pivot_table(index="Receptor", columns="Ligand", values="Average_Affinity")
    row_order = cluster_order(pivot.values)
    col_order = cluster_order(pivot.values.T)
    ordered = pivot.iloc[row_order, col_order]

    fig, ax = plt.subplots(figsize=(8, 11))
    im = ax.imshow(ordered.values, cmap="RdBu_r", vmin=-9, vmax=-4, aspect="auto")
    ax.set_xticks(range(len(ordered.columns)))
    ax.set_xticklabels(ordered.columns, rotation=90, fontsize=7)
    ax.set_yticks(range(len(ordered.index)))
    ax.set_yticklabels(ordered.index, fontsize=6)
    ax.set_title("Fig. 2 — OdorSig-predicted mean binding affinities\n(hierarchically clustered)")
    cbar = fig.colorbar(im, ax=ax, shrink=0.6)
    cbar.set_label("Mean $\\Delta G$ (kcal/mol)")
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "fig2_heatmap.png"), dpi=200)
    plt.close(fig)


def fig3_boxplot(df, out_dir):
    order = df.groupby("Receptor")["Average_Affinity"].median().sort_values().index
    data = [df.loc[df["Receptor"] == r, "Average_Affinity"].values for r in order]

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.boxplot(data, tick_labels=order, showfliers=False)
    ax.axhline(MODERATE_CUTOFF, ls="--", color="#b8862b", lw=1, label="moderate threshold (-5.0)")
    ax.axhline(STRONG_CUTOFF, ls="--", color="#a43d26", lw=1, label="strong threshold (-7.0)")
    ax.set_xticklabels(order, rotation=90, fontsize=6)
    ax.set_ylabel("Mean $\\Delta G$ (kcal/mol)")
    ax.set_title("Fig. 3 — Receptor-specific affinity distributions (ordered by median)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "fig3_boxplot.png"), dpi=200)
    plt.close(fig)


def fig4_odorant_profile(df, out_dir):
    stats = df.groupby("Ligand")["Average_Affinity"].agg(["mean", "std"]).sort_values("mean")

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(stats.index, stats["mean"], yerr=stats["std"], capsize=3, color="#21665a")
    ax.axhline(MODERATE_CUTOFF, ls="--", color="#b8862b", lw=1)
    ax.axhline(STRONG_CUTOFF, ls="--", color="#a43d26", lw=1)
    ax.set_xticks(range(len(stats.index)))
    ax.set_xticklabels(stats.index, rotation=45, ha="right")
    ax.set_ylabel("Mean $\\Delta G$ across all 40 receptors (kcal/mol)")
    ax.set_title("Fig. 4 — Odorant-specific binding affinity profile")
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "fig4_odorant_profile.png"), dpi=200)
    plt.close(fig)


def fig5_classification(df, out_dir):
    classes = df["Average_Affinity"].apply(classify)
    counts = classes.value_counts().reindex(["Strong", "Moderate", "Weak"])
    colors = {"Strong": "#a43d26", "Moderate": "#b8862b", "Weak": "#5b6167"}

    per_receptor = (
        df.assign(Class=classes)
        .groupby(["Receptor", "Class"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=["Strong", "Moderate", "Weak"], fill_value=0)
    )
    per_receptor_pct = per_receptor.div(per_receptor.sum(axis=1), axis=0) * 100
    per_receptor_pct = per_receptor_pct.sort_values("Strong", ascending=False)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6), gridspec_kw={"width_ratios": [1, 3]})

    axes[0].bar(counts.index, counts.values, color=[colors[c] for c in counts.index])
    for i, v in enumerate(counts.values):
        axes[0].text(i, v + 3, f"{v}\n({100*v/len(df):.1f}%)", ha="center", fontsize=8)
    axes[0].set_title("(a) Overall distribution")
    axes[0].set_ylabel("Number of pairs")

    bottom = np.zeros(len(per_receptor_pct))
    for cls in ["Strong", "Moderate", "Weak"]:
        axes[1].bar(per_receptor_pct.index, per_receptor_pct[cls], bottom=bottom, color=colors[cls], label=cls)
        bottom += per_receptor_pct[cls].values
    axes[1].set_xticks(range(len(per_receptor_pct.index)))
    axes[1].set_xticklabels(per_receptor_pct.index, rotation=90, fontsize=6)
    axes[1].set_title("(b) Per-receptor binding-class distribution")
    axes[1].set_ylabel("% of odorants")
    axes[1].legend(fontsize=8)

    fig.suptitle("Fig. 5 — Binding strength classification (strong ≤ -7.0, moderate -7.0..-5.0, weak > -5.0 kcal/mol)")
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "fig5_classification.png"), dpi=200)
    plt.close(fig)


def fig7_reproducibility(df, out_dir):
    fig, ax = plt.subplots(figsize=(7, 6))
    sc = ax.scatter(df["Average_Affinity"], df["Std_Deviation"], c=df["Average_Affinity"], cmap="RdBu_r", s=18, alpha=0.8)
    ax.axvline(STRONG_CUTOFF, ls="--", color="#a43d26", lw=1)
    ax.axhline(REPRODUCIBILITY_CUTOFF, ls="--", color="#21665a", lw=1)
    ax.set_xlabel("Mean $\\Delta G$ (kcal/mol)")
    ax.set_ylabel("$\\sigma$ across 3 runs (kcal/mol)")
    ax.set_title("Fig. 7 — Binding affinity vs. docking reproducibility")
    fig.colorbar(sc, ax=ax, label="Mean $\\Delta G$ (kcal/mol)")
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "fig7_reproducibility.png"), dpi=200)
    plt.close(fig)


def fig8_ramachandran(validation, out_dir):
    fav = validation[validation["Metric"] == "Ramachandran Favoured"].copy()
    fav["Value"] = fav["Value"].astype(str).str.rstrip("%").astype(float)
    fav = fav.sort_values("Value")

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.bar(fav["Receptor"], fav["Value"], color="#21665a")
    ax.axhline(90, ls="--", color="#b8862b", lw=1, label="90% (acceptable)")
    ax.axhline(95, ls="--", color="#2f7d4f", lw=1, label="95% (excellent)")
    ax.set_xticks(range(len(fav["Receptor"])))
    ax.set_xticklabels(fav["Receptor"], rotation=90, fontsize=6)
    ax.set_ylabel("Ramachandran favoured (%)")
    ax.set_title("Fig. 8 — Structural quality of the 40 homology models")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "fig8_ramachandran.png"), dpi=200)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="Final_Docking_Results.xlsx")
    parser.add_argument("--out", default="figures")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        raise SystemExit(f"Input file not found: {args.input}")
    os.makedirs(args.out, exist_ok=True)

    summary, validation = load_data(args.input)
    print_summary_stats(summary)

    fig2_heatmap(summary, args.out)
    fig3_boxplot(summary, args.out)
    fig4_odorant_profile(summary, args.out)
    fig5_classification(summary, args.out)
    fig7_reproducibility(summary, args.out)
    fig8_ramachandran(validation, args.out)

    print(f"\nFigures written to {os.path.abspath(args.out)}/")
    if not HAVE_SCIPY:
        print("Note: scipy not installed — Fig. 2 used mean-value ordering instead of hierarchical clustering.")


if __name__ == "__main__":
    main()
