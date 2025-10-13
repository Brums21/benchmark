from pathlib import Path
import warnings
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from load_save import save_table_csv, SPECIES_PRETTY, SPECIES_SIZE, METRIC_LABELS


def rename_tool(row):
    if row["tool"] == "augustus":
        return "AUGUSTUS"
    elif row["tool"] == "genemarkes":
        return "GeneMark-ES"
    elif row["tool"] == "snap":
        if row["model_used"] == "arabidopsis":
            return "SNAP (A. thaliana)"
        else:
            return "SNAP (O. sativa)"
    return row["tool"]

def map_snap_model(x: str) -> str:
    if not isinstance(x, str):
        return "Unknown"
    k = x.strip().lower()
    if k in {"arabidopsis_thaliana", "a_thaliana", "arabidopsis"}:
        return "A. thaliana"
    if k in {"oryza_sativa", "o_sativa", "rice"}:
        return "O. sativa"
    return x 

def plot_model_comparison_RAM_time_consumed(df: pd.DataFrame, out_dir: Path, dpi: int):
    
    m_aug = (df["tool"] == "augustus") & (df["hint"].isna() | (df["hint"] == "abinitio"))
    m_snap = df["tool"] == "snap"
    m_gmes = df["tool"] == "genemarkes"
    
    df = df[m_aug | m_snap | m_gmes].copy()

    df["species_size_kb"] = df["species"].map(SPECIES_SIZE)

    df["ram_per_kb"] = df["ram_mb"] / df["species_size_kb"]
    df["time_per_kb"] = df["time_sec"] / df["species_size_kb"]

    save_table_csv(df, out_dir / "csv/abinitio_ram_time_per_species.csv")

    g1 = sns.catplot(
        data=df, kind="bar",
        x="species", y="ram_mb", hue="tool",
        palette="mako", height=5, aspect=1.5
    )
    g1.set_axis_labels("Species", "RAM (KB)")
    g1.set_titles("RAM consumption by species and tool")
    g1.savefig(out_dir / "abinitio_ram_per_species.png", dpi=dpi, bbox_inches="tight")
    plt.close(g1.figure)

    g2 = sns.catplot(
        data=df, kind="bar",
        x="species", y="time_sec", hue="tool",
        palette="rocket", height=5, aspect=1.5
    )
    g2.set_axis_labels("Species", "Runtime (s)")
    g2.set_titles("Runtime by species and tool")
    g2.savefig(out_dir / "abinitio_time_per_species.png", dpi=dpi, bbox_inches="tight")
    plt.close(g2.figure)

def plot_model_comparison_zero_mut_ab_initio(df: pd.DataFrame, out_dir: Path, dpi: int):
    d = df[(df["mut_rate"] == 0.0) & (df["tool"].isin(["augustus", "snap", "genemarkes"]))].copy()

    d["expected_model"] = np.where(d["species"] == "o_sativa", "rice", "arabidopsis")

    m_aug = (d["tool"] == "augustus") & (d["hint"].isna() | (d["hint"] == "abinitio"))
    d.loc[m_aug, "model_used"] = np.where(
        d.loc[m_aug, "species"] == "o_sativa", "rice", "arabidopsis"
    )

    m_snap = d["tool"] == "snap"
    d.loc[m_snap, "model_used"] = d.loc[m_snap, "train_species"].str.lower().str.strip()

    d.loc[d["tool"] == "genemarkes", "model_used"] = "none"

    d = d.dropna(subset=["model_used"])
    d = d[(d["tool"] == "genemarkes") | (d["model_used"] == d["expected_model"])]

    if d.empty:
        warnings.warn("No data after aligning models.")
        return

    metrics = ["precision", "recall", "f1"]
    agg = d.groupby(["species", "tool"])[metrics].mean().reset_index()

    tool_map = {"augustus": "AUGUSTUS", "snap": "SNAP", "genemarkes": "GeneMark-ES"}
    metric_map = {"precision": "Precision", "recall": "Recall", "f1": "F1-score"}

    agg["tool"] = agg["tool"].map(tool_map)
    agg["species"] = agg["species"].map(SPECIES_PRETTY)

    save_table_csv(agg, out_dir / "csv/augustus_snap_genemarkes_same_model_per_species.csv")

    melted = agg.melt(
        id_vars=["species", "tool"],
        value_vars=list(metric_map.keys()),
        var_name="metric",
        value_name="score",
    )

    melted["tool"] = pd.Categorical(
        melted["tool"], categories=["AUGUSTUS", "SNAP", "GeneMark-ES"], ordered=True
    )
    melted["metric"] = melted["metric"].map(metric_map)

    g = sns.catplot(
        data=melted,
        kind="bar",
        x="tool", y="score", hue="metric",
        col="species", col_wrap=2, sharey=True, height=4, aspect=1.2,
        palette="flare"
    )
    g.set_axis_labels("Tool", "Score")
    g.set_titles("{col_name}")
    for ax in g.axes.flatten():
        ax.set_ylim(0, 1)

    g.figure.suptitle("Comparison of ab initio tools at 0% mutation rate", y=1.02)
    g.savefig(out_dir / "augustus_snap_genemarkes_same_model_per_species_0_mr.png", dpi=dpi, bbox_inches="tight")
    plt.close(g.figure)

def plot_mutation_curves_ab_initio(df: pd.DataFrame, out_dir: Path, dpi: int):
    d = df[df["tool"].isin(["augustus", "snap", "genemarkes"])].copy()

    d["species"] = d["species"].map(SPECIES_PRETTY).fillna(d["species"])

    d["expected_model"] = np.where(d["species"] == "O. sativa", "rice", "arabidopsis")

    m_aug = (d["tool"] == "augustus") & (d["hint"].isna() | (d["hint"] == "abinitio"))
    d.loc[m_aug, "model_used"] = np.where(
        d.loc[m_aug, "species"] == "O. sativa", "rice", "arabidopsis"
    )

    m_snap = d["tool"] == "snap"
    d.loc[m_snap, "model_used"] = d.loc[m_snap, "train_species"].str.lower().str.strip()
    d.loc[d["tool"] == "genemarkes", "model_used"] = "none"

    d = d.dropna(subset=["model_used"])
    d = d[(d["tool"] == "genemarkes") | (d["tool"] == "augustus") | (d["tool"] == "snap")]

    if d.empty:
        warnings.warn("No data after filtering models")
        return

    d["tool"] = d.apply(rename_tool, axis=1)

    species_list = ["A. thaliana", "O. sativa", "G. raimondii", "M. esculenta"]

    save_table_csv(d, out_dir / "csv/ab_initio_mr_all_species.csv")

    overall = d.groupby(["tool", "mut_rate"])[list(METRIC_LABELS.keys())].mean().reset_index()
    save_table_csv(overall, out_dir / "csv/ab_initio_mr_overall.csv")

    fig, axes = plt.subplots(1, 3, figsize=(12, 4), sharey=True)
    axes = axes.flatten()

    for i, metric in enumerate(list(METRIC_LABELS.keys())):
        keep_legend = (i == 0)
        sns.lineplot(
            data=overall, x="mut_rate", y=metric, hue="tool",
            marker="o", legend="auto" if keep_legend else False, ax=axes[i]
        )
        axes[i].set_ylim(0, 1)
        axes[i].set_title(metric.capitalize(), fontsize=15)
        axes[i].set_xlabel("Mutation rate", fontsize=13)
        axes[i].set_ylabel(metric.capitalize() if i == 0 else "", fontsize=13)
        axes[i].tick_params(axis="both", labelsize=11)

        if keep_legend and axes[i].legend_ is not None:
            handles, labels = axes[i].get_legend_handles_labels()
            axes[i].legend_.remove()

    handles, labels = axes[0].get_legend_handles_labels()
    if handles and labels and len(labels) > 0:
        fig.legend(
            handles, labels,
            loc="lower center", bbox_to_anchor=(0.5, -0.05),
            frameon=False, ncol=max(1, len(labels)), title=None, prop={'size': 12}
        )
    else:
        warnings.warn("No legend handles found for overall ab initio plot; skipping legend.")

    fig.suptitle("Overall mutation effect for ab initio tools", y=0.98, fontsize=16)
    fig.tight_layout(rect=[0.03, 0.08, 1, 0.95])

    fig.savefig(out_dir / "mutation_curves_overall.png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)

    for sp in species_list:
        sub = d[d["species"] == sp]
        if sub.empty:
            warnings.warn(f"No data for {sp}")
            continue

        save_table_csv(sub, out_dir / f"csv/ab_initio_mr_{sp.replace(' ', '_')}.csv")

        fig, axes = plt.subplots(1, 3, figsize=(12, 4), sharey=True)
        axes = axes.flatten()

        handles = labels = None
        for i, metric in enumerate(METRIC_LABELS.keys()):
            keep_legend = (i == 0)
            sns.lineplot(
                data=sub, x="mut_rate", y=metric, hue="tool",
                marker="o", legend="auto" if keep_legend else False, ax=axes[i]
            )
            axes[i].set_ylim(0, 1)
            axes[i].set_title(metric.capitalize(), fontsize=15)
            axes[i].set_xlabel("Mutation rate", fontsize=13)
            axes[i].set_ylabel(metric.capitalize() if i == 0 else "", fontsize=13)
            axes[i].tick_params(axis="both", labelsize=11)

            if keep_legend and axes[i].legend_ is not None:
                handles, labels = axes[i].get_legend_handles_labels()
                axes[i].legend_.remove()

        if len(axes) > len(list(METRIC_LABELS.keys())):
            for j in range(len(list(METRIC_LABELS.keys())), len(axes)):
                fig.delaxes(axes[j])

        if handles and labels and len(labels) > 0:
            fig.legend(
                handles, labels,
                loc="lower center", bbox_to_anchor=(0.5, -0.05),
                frameon=False, ncol=max(1, len(labels)), title=None, prop={'size': 12}
            )
        else:
            warnings.warn(f"No legend handles found for {sp} plot; skipping legend.")

        fig.suptitle(f"Mutation effect for {sp} species", y=0.98, fontsize=16)
        fig.tight_layout(rect=[0.03, 0.08, 1, 0.95])

        fig.savefig(out_dir / f"mutation_curves_{sp.replace(' ', '_')}.png",
                    dpi=dpi, bbox_inches="tight")
        plt.close(fig)

def plot_model_comparison_RAM_time_consumed_ab_initio(df: pd.DataFrame, out_dir: Path, dpi: int):
    """
    Compare RAM and runtime for ab initio tools:
      - AUGUSTUS (ab initio only)
      - SNAP (reported separately by training species)
      - GeneMark-ES
    Produces absolute and genome-size-normalised plots, plus CSVs.

    Expected columns: tool, species, ram_mb, time_sec, mut_rate (any),
                      hint (may be NaN), train_species (for SNAP).
    """

    m_aug_ab = (df["tool"] == "augustus") & (df["hint"].isna() | (df["hint"] == "abinitio"))
    m_snap   = (df["tool"] == "snap")
    m_gmes   = (df["tool"] == "genemarkes")
    d = df[m_aug_ab | m_snap | m_gmes].copy()
    if d.empty:
        warnings.warn("No ab initio rows found for RAM/time comparison.")
        return

    mapped = d["species"].map(SPECIES_PRETTY)
    d["species_pretty"] = mapped.where(mapped.notna(), d["species"].astype(object))

    # Map genome size and compute normalised metrics
    d["species_size_kb"] = d["species"].map(SPECIES_SIZE)
    d = d.dropna(subset=["species_size_kb"]).copy()
    d["ram_per_kb"]  = d["ram_mb"]  / d["species_size_kb"]
    d["time_per_kb"] = d["time_sec"] / d["species_size_kb"]

    # Build pretty tool labels (split SNAP by training model)
    tool_pretty = []
    for i, row in d.iterrows():
        if row["tool"] == "augustus":
            tool_pretty.append("AUGUSTUS (ab initio)")
        elif row["tool"] == "genemarkes":
            tool_pretty.append("GeneMark-ES")
        elif row["tool"] == "snap":
            model = map_snap_model(row.get("train_species", "Unknown"))
            tool_pretty.append(f"SNAP ({model})")
        else:
            tool_pretty.append(row["tool"])

    d["tool_pretty"] = tool_pretty

    hue_order = ["AUGUSTUS (ab initio)", "SNAP (A. thaliana)", "SNAP (O. sativa)", "GeneMark-ES"]
    d["tool_pretty"] = pd.Categorical(d["tool_pretty"], categories=hue_order, ordered=True)

    cols_runs = [
        "tool","tool_pretty","species","species_pretty","mut_rate",
        "ram_mb","time_sec","species_size_kb","ram_per_kb","time_per_kb"
    ]

    if "train_species" in d.columns:
        cols_runs.append("train_species")

    g1 = sns.catplot(
        data=d, kind="bar",
        x="species_pretty", y="ram_mb", hue="tool_pretty",
        hue_order=hue_order, height=5, aspect=1.5
    )
    g1.set_axis_labels("Species", "RAM (KB)")
    g1.figure.suptitle("RAM consumption by species and tool", y=1.02, fontsize=14)
    if g1._legend is not None:
        g1._legend.set_title("Tool")
    g1.savefig(out_dir / "abinitio_ram_per_species.png", dpi=dpi, bbox_inches="tight")
    plt.close(g1.figure)

    g2 = sns.catplot(
        data=d, kind="bar",
        x="species_pretty", y="time_sec", hue="tool_pretty",
        hue_order=hue_order, height=5, aspect=1.5
    )
    g2.set_axis_labels("Species", "Runtime (s)")
    g2.figure.suptitle("Runtime by species and tool", y=1.02, fontsize=14)
    if g2._legend is not None:
        g2._legend.set_title("Tool")
    g2.savefig(out_dir / "abinitio_time_per_species.png", dpi=dpi, bbox_inches="tight")
    plt.close(g2.figure)

    g3 = sns.catplot(
        data=d, kind="bar",
        x="species_pretty", y="ram_per_kb", hue="tool_pretty",
        hue_order=hue_order, height=5, aspect=1.5
    )
    g3.set_axis_labels("Species", "RAM per KB")
    g3.figure.suptitle("Normalised RAM by species and tool", y=1.02, fontsize=14)
    if g3._legend is not None:
        g3._legend.set_title("Tool")
    g3.savefig(out_dir / "abinitio_ram_per_kb_per_species.png", dpi=dpi, bbox_inches="tight")
    plt.close(g3.figure)

    g4 = sns.catplot(
        data=d, kind="bar",
        x="species_pretty", y="time_per_kb", hue="tool_pretty",
        hue_order=hue_order, height=5, aspect=1.5
    )
    g4.set_axis_labels("Species", "Runtime per KB")
    g4.figure.suptitle("Normalised runtime by species and tool", y=1.02, fontsize=14)
    if g4._legend is not None:
        g4._legend.set_title("Tool")
    g4.savefig(out_dir / "abinitio_time_per_kb_per_species.png", dpi=dpi, bbox_inches="tight")
    plt.close(g4.figure)

    d_csv = d.copy()

    tool_pretty_obj = d_csv["tool_pretty"].astype(object)

    d_csv["tool_pretty_csv"] = tool_pretty_obj.replace({
        "SNAP (A. thaliana)": "SNAP",
        "SNAP (O. sativa)": "SNAP"
    })

    d_csv["tool_pretty_csv"] = d_csv["tool_pretty_csv"].where(
        d_csv["tool_pretty_csv"].notna(), tool_pretty_obj
    )

    def _agg_mean(df, by):
        num = ["ram_mb","time_sec","ram_per_kb","time_per_kb"]
        out = (df.groupby(by, as_index=False)
                 .agg({**{c: "mean" for c in num}, "species_size_kb": "first"}))
        return out

    runs_csv = _agg_mean(
        d_csv,
        by=["tool_pretty_csv","species","species_pretty","mut_rate"]
    )[["tool_pretty_csv","species","species_pretty","mut_rate",
       "ram_mb","time_sec","species_size_kb","ram_per_kb","time_per_kb"]]
    runs_csv = runs_csv.rename(columns={"tool_pretty_csv": "tool_pretty"})
    save_table_csv(runs_csv, out_dir / "csv/abinitio_ram_time_runs.csv")

    agg_csv = _agg_mean(
        d_csv,
        by=["species","species_pretty","tool_pretty_csv"]
    )[["species","species_pretty","tool_pretty_csv",
       "ram_mb","time_sec","ram_per_kb","time_per_kb"]]
    
    agg_csv = agg_csv.rename(columns={"tool_pretty_csv": "tool_pretty"})
    save_table_csv(agg_csv, out_dir / "csv/abinitio_ram_time_agg_by_species.csv")

    overall_csv = _agg_mean(
        d_csv,
        by=["tool_pretty_csv"]
    )[["tool_pretty_csv","ram_mb","time_sec","ram_per_kb","time_per_kb"]]

    overall_csv = overall_csv.rename(columns={"tool_pretty_csv": "tool_pretty"})
    save_table_csv(overall_csv, out_dir / "csv/abinitio_ram_time_overall.csv")