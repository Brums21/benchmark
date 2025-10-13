from pathlib import Path
import warnings
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from load_save import save_table_csv, SPECIES_PRETTY, TOOL_MAPPING, METRIC_LABELS, SPECIES_SIZE

def _evidence_subset(df: pd.DataFrame) -> pd.DataFrame:
    tools_ev = ["genemarkep", "genemarketp", "gemoma", "augustus"]
    d = df[df["tool"].isin(tools_ev)].copy()

    d = d[~((d["tool"] == "augustus") & (d["hint"].isna() | (d["hint"] == "abinitio")))].copy()

    mapped = d["species"].map(SPECIES_PRETTY)
    d["species_pretty"] = mapped.where(mapped.notna(), d["species"].astype(object))

    d["tool_pretty"] = d["tool"].map(TOOL_MAPPING).astype(object)

    d["hint"] = d["hint"].astype(str).str.lower().str.strip()
    d = d[d["hint"].isin(["genus", "order", "far"])].copy()

    return d

def plot_evidence_zero_mut_collapsed(df: pd.DataFrame, out_dir: Path, dpi: int):
    """
    Plot the hint effect per species at 0% mutation.
    Each figure corresponds to one species.
    2×2 grid: columns = tools, hue = metric (Precision, Recall, F1-score).
    """
    d = _evidence_subset(df)
    d0 = d[d["mut_rate"] == 0.0].copy()
    if d0.empty:
        warnings.warn("No evidence-based rows at 0% mutation.")
        return

    within_hint = (
        d0.groupby(["species", "species_pretty", "tool_pretty", "hint"], as_index=False)[list(METRIC_LABELS.keys())]
          .mean()
    )

    long = within_hint.melt(
        id_vars=["species", "species_pretty", "tool_pretty", "hint"],
        value_vars=list(METRIC_LABELS.keys()),
        var_name="metric",
        value_name="score"
    )

    long["metric"] = long["metric"].map(METRIC_LABELS)

    hint_order = ["genus", "order", "far"]
    species_list = sorted(long["species_pretty"].unique())

    for sp in species_list:
        sub = long[long["species_pretty"] == sp].copy()
        if sub.empty:
            continue

        g = sns.FacetGrid(
            sub, col="tool_pretty", col_wrap=2,
            sharey=True, height=3.3, aspect=1.2, legend_out=False
        )

        g.set_titles("{col_name}")
        for ax in g.axes.flatten():
            title = ax.get_title()
            if "=" in title:
                ax.set_title(title.split("=")[-1].strip(), fontsize=14)

        g.map_dataframe(
            sns.barplot,
            x="hint", y="score",
            hue="metric",
            order=hint_order,
            hue_order=["Precision", "Recall", "F1-score"],
            errorbar=None
        )

        if g._legend:
            g._legend.remove()

        handles, labels = g.axes[0].get_legend_handles_labels()

        if handles and labels:
            g.figure.legend(
                handles, labels,
                loc="lower center",
                bbox_to_anchor=(0.5, -0.05),
                frameon=False,
                ncol=len(labels),
                title="Metric",
                prop={'size': 12},
                title_fontsize=13
            )

        for ax in g.axes.flatten():
            ax.set_ylim(0, 1)
            ax.set_xlabel("Hint")
            ax.set_ylabel("Score")
            for lab in ax.get_xticklabels():
                lab.set_rotation(15)
                lab.set_ha("right")

        g.figure.suptitle(f"Hint effect for species {sp} at 0% mutation", y=1.03)
        g.figure.tight_layout(rect=[0, 0, 1, 0.95])

        fname = f"evidence_hint_effect_{sp.replace(' ', '_')}_zero_mut.png"
        g.figure.savefig(out_dir / fname, dpi=dpi, bbox_inches="tight")
        plt.close(g.figure)

def plot_evidence_zero_mut_collapsed_hints(df: pd.DataFrame, out_dir: Path, dpi: int):
    """
    Plot comparison of evidence-based tools at 0% mutation per species.
    X-axis = tools, hue = metric (Precision, Recall, F1).
    Each species appears in its own facet.
    """
    d = _evidence_subset(df)
    d0 = d[d["mut_rate"] == 0.0].copy()
    if d0.empty:
        warnings.warn("No evidence-based rows at 0% mutation.")
        return

    metrics = list(METRIC_LABELS)

    collapsed = (
        d0.groupby(["species", "species_pretty", "tool_pretty"], as_index=False)[metrics]
          .mean()
    )

    long = collapsed.melt(
        id_vars=["species_pretty", "tool_pretty"],
        value_vars=metrics,
        var_name="metric",
        value_name="score"
    )

    species_order = sorted(long["species_pretty"].unique())
    metric_order = ["precision", "recall", "f1"]

    g = sns.catplot(
        data=long, kind="bar",
        x="tool_pretty", y="score", hue="metric",
        hue_order=metric_order,
        col="species_pretty", col_order=species_order, col_wrap=2,
        palette="rocket",
        sharey=True, height=4, aspect=1.1,
        legend=True 
    )

    handles, labels = None, None
    for ax in g.axes.flatten():
        h, l = ax.get_legend_handles_labels()
        if h and l:
            handles, labels = h, l
            break
    if g._legend:
        g._legend.remove()

    g.set_axis_labels("Tool", "Score")
    g.set_titles("{col_name}", size=14)
    for ax in g.axes.flatten():
        ax.set_ylim(0, 1)
        ax.tick_params(axis="both", labelsize=11)
        for lab in ax.get_xticklabels():
            lab.set_rotation(25)
            lab.set_ha("right")

    if handles and labels:
        g.figure.legend(
            handles, labels,
            loc="lower center",
            bbox_to_anchor=(0.5, -0.05),
            frameon=False,
            ncol=len(labels),
            title="Metric",
            prop={'size': 12},
            title_fontsize=13
        )

    g.figure.suptitle("Evidence-based tools at 0% mutation per species",
                      y=0.98, fontsize=16)
    g.figure.tight_layout(rect=[0, 0.05, 1, 0.95]) 

    fname = "evidence_zero_mut_collapsed_hints.png"
    g.figure.savefig(out_dir / fname, dpi=dpi, bbox_inches="tight")
    plt.close(g.figure)

def plot_mutation_curves_evidence(df: pd.DataFrame, out_dir: Path, dpi: int):
    d = _evidence_subset(df)
    if d.empty:
        warnings.warn("No evidence-based rows for mutation curves.")
        return

    hint_order = ["genus","order","far"]
    d["hint"] = pd.Categorical(d["hint"], hint_order, ordered=True)

    

    overall = (d.groupby(["hint","tool_pretty","mut_rate"], as_index=False)[list(METRIC_LABELS.keys())]
                 .mean())
    save_table_csv(overall, out_dir / "csv/evidence_mutation_overall_by_hint.csv")

    for metric in list(METRIC_LABELS.keys()):
        g = sns.FacetGrid(
            overall,
            col="hint",
            col_order=hint_order,
            sharey=True,
            height=4.0,
            aspect=1.2,
            hue="tool_pretty",
            palette="tab10"
        )

        g.map(sns.lineplot, "mut_rate", metric, marker="o")

        for ax in g.axes.flatten():
            ax.set_ylim(0, 1)
            ax.set_xlabel("Mutation rate", fontsize=12)
            ax.set_ylabel(metric.capitalize(), fontsize=12)
            ax.tick_params(axis="both", labelsize=12)

        g.set_titles(col_template="{col_name}", size=12)

        handles, labels = g.axes[0, 0].get_legend_handles_labels()
        g.figure.legend(
            handles,
            labels,
            loc="lower center",
            ncol=len(labels),
            bbox_to_anchor=(0.5, -0.15),
            frameon=False,
            prop={'size': 12}
        )

        g.figure.subplots_adjust(bottom=0.1, top=0.85)
        g.figure.suptitle(
            f"Evidence-based tools mutation effect - {metric.capitalize()}",
            y=1.05,
            fontsize=16,
        )

        g.savefig(
            out_dir / f"evidence_mutation_{metric}_by_hint.png",
            dpi=dpi,
            bbox_inches="tight"
        )
        plt.close(g.figure)


    within_hint = (d.groupby(["species","species_pretty","tool_pretty","mut_rate","hint"], as_index=False)[list(METRIC_LABELS.keys())]
                     .mean())
    
    species_collapsed = (within_hint.groupby(["species","species_pretty","tool_pretty","mut_rate"], as_index=False)[list(METRIC_LABELS.keys())]
                           .mean())
    
    overall_by_tool = (species_collapsed.groupby(["tool_pretty","mut_rate"], as_index=False)[list(METRIC_LABELS.keys())]
                         .mean())
    
    save_table_csv(overall_by_tool, out_dir / "csv/evidence_mutation_overall_by_tool_collapsed_hints.csv")

    species_list = list(d["species_pretty"].dropna().unique())
    for sp in species_list:
        sub = d[d["species_pretty"] == sp]
        if sub.empty:
            continue

        tool_order = ["AUGUSTUS (hints)", "GeMoMa", "GeneMark-EP+", "GeneMark-ETP"]

        sub_overall = (
            sub.groupby(["hint", "tool_pretty", "mut_rate"], as_index=False)[list(METRIC_LABELS.keys())].mean()
        )
        save_table_csv(sub_overall, out_dir / f"csv/evidence_mutation_{sp.replace(' ','_')}_by_hint.csv")

        present_hints = [h for h in hint_order if h in set(sub_overall["hint"])]

        sub_long = sub_overall.melt(
            id_vars=["hint", "tool_pretty", "mut_rate"],
            value_vars=list(METRIC_LABELS.keys()),
            var_name="metric",
            value_name="score",
        )

        g = sns.relplot(
            data=sub_long, kind="line",
            x="mut_rate", y="score",
            hue="tool_pretty", hue_order=tool_order,
            col="hint", col_order=present_hints,
            row="metric", row_order=list(METRIC_LABELS.keys()),
            marker="o", linewidth=1.8, markersize=5,
            height=3.2, aspect=1.25,
            facet_kws=dict(sharey=True, sharex=True, margin_titles=False),
            legend=True,
        )

        g.set_titles(template="")
        for r, _met in enumerate(list(METRIC_LABELS.keys())):
            for c, ax in enumerate(g.axes[r, :]):
                ax.set_title(g.col_names[c], fontsize=16)


        for r, met in enumerate(list(METRIC_LABELS.keys())):
            for c, ax in enumerate(g.axes[r, :]):
                ax.set_ylim(0, 1)
                ax.grid(True, axis="y", linestyle=":", linewidth=0.6, alpha=0.6)
                if c != 0:
                    ax.set_ylabel(None)
                else:
                    ax.set_ylabel(METRIC_LABELS.get(met, met.capitalize()), fontsize=15)
                if r != len(list(METRIC_LABELS.keys())) - 1:
                    ax.set_xlabel(None)
                else:
                    ax.set_xlabel("Mutation rate", fontsize=15)
                ax.tick_params(axis="both", labelsize=13)

        handles, labels = g.axes[0, 0].get_legend_handles_labels()
        g._legend.remove()

        g.figure.legend(
            handles, labels,
            loc="lower center",
            bbox_to_anchor=(0.5, -0.03),
            ncol=len(labels),
            frameon=False,
            prop={'size': 13}
        )

        g.figure.suptitle(
            f"{sp} metrics per mutation rate and hint type",
            y=0.995,
            fontsize=17
        )
        g.figure.tight_layout(rect=[0, 0.07, 1, 0.95])

        g.figure.savefig(
            out_dir / f"evidence_mutation_{sp.replace(' ', '_')}_by_hint.png",
            dpi=dpi,
            bbox_inches="tight"
        )
        
        plt.close(g.figure)

def plot_model_comparison_RAM_time_consumed_evidence(df: pd.DataFrame, out_dir: Path, dpi: int):
    d = _evidence_subset(df)
    if d.empty:
        warnings.warn("No evidence-based rows for RAM/time.")
        return

    d["species_size_kb"] = d["species"].map(SPECIES_SIZE)
    d = d.dropna(subset=["species_size_kb"]).copy()
    d["ram_per_kb"]  = d["ram_mb"]  / d["species_size_kb"]
    d["time_per_kb"] = d["time_sec"] / d["species_size_kb"]

    save_table_csv(d[[
        "tool","tool_pretty","species","species_pretty","hint","mut_rate",
        "ram_mb","time_sec","species_size_kb","ram_per_kb","time_per_kb"
    ]], out_dir / "csv/evidence_ram_time_runs.csv")

    agg = (d.groupby(["species","species_pretty","tool_pretty"], as_index=False)
             [["ram_mb","time_sec","ram_per_kb","time_per_kb"]].mean())
    save_table_csv(agg, out_dir / "csv/evidence_ram_time_agg_by_species.csv")

    for y, fname, ylab, title in [
        ("ram_mb",     "evidence_ram_per_species.png",        "RAM (KB)",          "RAM by species and tool"),
        ("time_sec",   "evidence_time_per_species.png",       "Runtime (s)",       "Runtime by species and tool"),
        ("ram_per_kb", "evidence_ram_per_kb_per_species.png", "RAM per KB",        "Normalized RAM by species and tool"),
        ("time_per_kb","evidence_time_per_kb_per_species.png","Runtime per KB",    "Normalized runtime by species and tool"),
    ]:
        g = sns.catplot(
            data=d,
            kind="bar",
            x="species_pretty", y=y, hue="tool_pretty",
            height=5, aspect=1.5,
            legend=True,
            legend_out=False
        )

        g.set_axis_labels("Species", ylab)
        g.figure.suptitle(title, fontsize=15, y=1)

        handles, labels = g.ax.get_legend_handles_labels()
        if handles and labels:
            g._legend.remove() 

            g.figure.legend(
                handles, labels,
                title="Tool",
                loc="lower center",
                bbox_to_anchor=(0.5, -0.05),
                ncol=len(labels), 
                frameon=False,
                prop={'size': 11}
            )

        g.figure.tight_layout(rect=[0, 0.05, 1, 0.95])
        g.figure.savefig(out_dir / fname, dpi=dpi, bbox_inches="tight")
        plt.close(g.figure)


    overall = (d.groupby("tool_pretty", as_index=False)
                 [["ram_mb","time_sec","ram_per_kb","time_per_kb"]].mean())
    save_table_csv(overall, out_dir / "csv/evidence_ram_time_overall.csv")

def plot_hint_effect_curves(df: pd.DataFrame, out_dir: Path, dpi: int):
    """
    Hint effect at 0% mutation for evidence-based tools.
    For each species, produce one figure with a 2x2 facet layout (one facet per tool),
    showing bars of Precision/Recall/F1 vs hint (genus/order/far) in the same plot.

    Also produces an overall plot macro-averaged across species.

    Outputs:
      - evidence_hint_effect_zero_mut_summary.csv                (per species × tool × hint)
      - evidence_hint_effect_<Species>_zero_mut.png              (per species plots)
      - evidence_hint_effect_zero_mut_overall_summary.csv        (macro-avg across species)
      - evidence_hint_effect_overall_zero_mut.png                (overall 2×2 plot)
    """
    d = _evidence_subset(df)
    if d.empty:
        warnings.warn("No evidence-based rows for hint curves.")
        return

    d0 = d[d["mut_rate"] == 0.0].copy()
    if d0.empty:
        warnings.warn("No rows at 0% mutation for hint curves.")
        return

    metrics = ["precision", "recall", "f1"]
    metric_title = {"precision": "Precision", "recall": "Recall", "f1": "F1-score"}
    hint_order = ["genus", "order", "far"]
    d0["hint"] = pd.Categorical(d0["hint"], hint_order, ordered=True)

    summ = (d0.groupby(["species", "species_pretty", "tool_pretty", "hint"], as_index=False)[metrics]
              .mean())
    save_table_csv(summ, out_dir / "csv/evidence_hint_effect_zero_mut_summary.csv")

    for sp in sorted(summ["species_pretty"].dropna().unique()):
        sub = summ[summ["species_pretty"] == sp]
        if sub.empty:
            continue

        sub_melt = sub.melt(
            id_vars=["tool_pretty", "hint"],
            value_vars=metrics,
            var_name="metric",
            value_name="score"
        )
        sub_melt["metric"] = sub_melt["metric"].map(metric_title)

        g = sns.FacetGrid(
            sub_melt, col="tool_pretty", col_wrap=2,
            sharey=True, height=3.3, aspect=1.2
        )
        g.map_dataframe(
            sns.barplot,
            x="hint", y="score",
            hue="metric",
            order=hint_order,
            errorbar=None
        )
        for ax in g.axes.flatten():
            ax.set_ylim(0, 1)
            ax.set_xlabel("Hint")
            ax.set_ylabel("Score")
            for lab in ax.get_xticklabels():
                lab.set_rotation(15); lab.set_ha("right")

        g.set_titles("{col_name}")
        g.add_legend(title="Metric")
        g.figure.suptitle(f"Hint effect for species {sp} at 0% mutation", y=1.03)

        fname = f"evidence_hint_effect_{sp.replace(' ', '_')}_zero_mut.png"
        g.savefig(out_dir / fname, dpi=dpi, bbox_inches="tight")
        plt.close(g.figure)

    overall = (summ.groupby(["tool_pretty", "hint"], as_index=False)[metrics]
                  .mean())

    save_table_csv(overall, out_dir / "csv/evidence_hint_effect_zero_mut_overall_summary.csv")

    overall_melt = overall.melt(
        id_vars=["tool_pretty", "hint"],
        value_vars=metrics,
        var_name="metric",
        value_name="score"
    )
    overall_melt["metric"] = overall_melt["metric"].map(metric_title)

    g = sns.FacetGrid(
        overall_melt, col="tool_pretty", col_wrap=2, palette="flare",
        sharey=True, height=3.3, aspect=1.2
    )
    g.map_dataframe(
        sns.barplot,
        x="hint", y="score",
        hue="metric",
        order=hint_order,
        errorbar=None
    )

    for ax in g.axes.flatten():
        ax.set_ylim(0, 1)
        ax.set_xlabel("Hint")
        ax.set_ylabel("Score")
        for lab in ax.get_xticklabels():
            lab.set_rotation(15); lab.set_ha("right")

    g.set_titles("{col_name}")
    g.add_legend(title="Metric")
    g.figure.suptitle("Hint effect at 0% mutation averaged across species", y=1.03)

    g.savefig(out_dir / "evidence_hint_effect_overall_zero_mut.png", dpi=dpi, bbox_inches="tight")
    plt.close(g.figure)