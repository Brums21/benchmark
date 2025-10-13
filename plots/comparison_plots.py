from pathlib import Path
import warnings
from matplotlib.lines import Line2D
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from load_save import save_table_csv, SPECIES_SIZE

def plot_mutation_curves_ab_vs_evidence_macro_simple(df: pd.DataFrame, out_dir: Path, dpi: int):
    """
    - Ab initio: AUGUSTUS (no hints), SNAP (A. thaliana / O. sativa), GeneMark-ES
    - Evidence:  AUGUSTUS (with hints), GeneMark-EP+, GeneMark-ETP, GeMoMa
    - Evidence is MACRO-averaged across hints per (tool, mut_rate).
    - Distinguishes AUGUSTUS (ab initio) vs AUGUSTUS (hints).
    - Single legend (tools only). Line style encodes setting (solid=ab, dashed=evidence).
    """
    d = df.copy()
    d["tool_l"] = d["tool"].str.lower().str.strip()
    if "hint" in d.columns:
        d["hint_l"] = d["hint"].str.lower().str.strip()
    else:
        d["hint_l"] = pd.NA

    allowed_hints = {"genus", "order", "far"}

    if "train_species" in d.columns:
        d.loc[d["tool_l"] == "snap", "model_used"] = (
            d.loc[d["tool_l"] == "snap", "train_species"].str.lower().str.strip()
        )
    d.loc[d["tool_l"] == "genemarkes", "model_used"] = "none"

    gmep_variants  = {"genemark-ep+", "genemark-ep", "genemark_ep+", "genemark_ep", "genemarkep"}
    gmetp_variants = {"genemark-etp", "genemark_etp", "genemarketp"}
    gemoma_variants= {"gemoma", "ge-moma", "ge_moma"}

    is_ab = (
        ((d["tool_l"] == "augustus") & (d["hint_l"].isna() | (d["hint_l"] == "abinitio")))
        | (d["tool_l"] == "genemarkes")
        | (d["tool_l"] == "snap")
    )
    is_evidence = (
        d["tool_l"].isin(gmep_variants | gmetp_variants | gemoma_variants)
        | ((d["tool_l"] == "augustus") & d["hint_l"].notna() & (d["hint_l"] != "abinitio"))
    )

    ab_df = d[is_ab].copy()
    ev_df = d[is_evidence].copy()

    ev_df = ev_df[
        (ev_df["tool_l"] != "augustus") | (ev_df["hint_l"].isin(allowed_hints))
    ].copy()

    if ev_df.query("tool_l == 'augustus'").empty:
        warnings.warn("No AUGUSTUS (hints) rows found across mutation rates; that line will be absent.")

    def pretty_tool_ab(row):
        tl = row["tool_l"]
        if tl == "augustus":   return "AUGUSTUS (ab initio)"
        if tl == "genemarkes": return "GeneMark-ES"
        if tl == "snap":       return "SNAP (A. thaliana)" if row.get("model_used") == "arabidopsis" else "SNAP (O. sativa)"
        return row.get("tool", tl)

    def pretty_tool_ev(row):
        tl = row["tool_l"]
        if tl == "augustus":     return "AUGUSTUS (hints)"
        if tl in gmep_variants:  return "GeneMark-EP+"
        if tl in gmetp_variants: return "GeneMark-ETP"
        if tl in gemoma_variants:return "GeMoMa"
        return row.get("tool", tl)

    if not ab_df.empty: ab_df["tool_pretty"] = ab_df.apply(pretty_tool_ab, axis=1)
    if not ev_df.empty: ev_df["tool_pretty"] = ev_df.apply(pretty_tool_ev, axis=1)

    metrics = ["precision", "recall", "f1"]

    overall_ab = (
        ab_df.groupby(["tool_pretty", "mut_rate"])[metrics]
             .mean().reset_index()
    )
    overall_ab["setting"] = "Ab initio"

    if not ev_df.empty:
        per_hint = (
            ev_df.groupby(["tool_pretty", "mut_rate", "hint_l"])[metrics]
                 .mean().reset_index()
        )
        overall_ev = (
            per_hint.groupby(["tool_pretty", "mut_rate"])[metrics]
                    .mean().reset_index()
        )
        overall_ev["setting"] = "Evidence-based (macro)"
        overall = pd.concat([overall_ab, overall_ev], ignore_index=True)
    else:
        warnings.warn("No evidence-based rows found; plotting Ab initio only.")
        overall = overall_ab.copy()

    tool_order = [
        "GeneMark-ES", "SNAP (A. thaliana)", "SNAP (O. sativa)",
        "AUGUSTUS (ab initio)",
        "GeMoMa", "GeneMark-EP+", "GeneMark-ETP",
        "AUGUSTUS (hints)",
    ]
    tool_order = [t for t in tool_order if t in overall["tool_pretty"].unique()]
    palette = dict(zip(tool_order, sns.color_palette(n_colors=len(tool_order))))
    style_order = ["Ab initio", "Evidence-based (macro)"]

    fig, axes = plt.subplots(1, 3, figsize=(13, 5.5), sharey=True)
    axes = axes.flatten()

    for i, metric in enumerate(metrics):
        sns.lineplot(
            data=overall,
            x="mut_rate", y=metric,
            hue="tool_pretty", hue_order=tool_order, palette=palette,
            style="setting", style_order=style_order,
            marker="o", dashes=True,
            ax=axes[i], legend=False
        )
        axes[i].set_ylim(0, 1)
        axes[i].set_title(metric.capitalize(), fontsize=15, pad=10)
        axes[i].set_xlabel("Mutation rate", fontsize=13)
        axes[i].set_ylabel(metric.capitalize() if i == 0 else "", fontsize=13)
        axes[i].tick_params(axis="both", labelsize=11)

    tool_handles = [
        Line2D([0], [0], color=palette[t], marker='o', linestyle='-', linewidth=2,
            label=t) for t in tool_order
    ]

    first_legend = fig.legend(
        handles=tool_handles,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.05),
        frameon=False,
        ncol=4,
        prop={'size': 12},
    )

    fig.add_artist(first_legend)

    fig.suptitle(
        "Mutation effect: Ab initio (solid) vs Evidence-based (dashed)",
        y=0.98,
        fontsize=16,
    )
    fig.tight_layout(rect=[0.03, 0.12, 0.97, 0.95])

    fig.savefig(
        out_dir / "mutation_curves_abinitio_vs_evidence_macro.png",
        dpi=dpi,
        bbox_inches="tight"
    )
    plt.close(fig)

def plot_ram_time_all_tools_overall_dots(df: pd.DataFrame, out_dir: Path, dpi: int):

    def _evidence_subset_local(df_):
        tools_ev = ["genemarkep", "genemarketp", "gemoma", "augustus"]
        d_ = df_[df_["tool"].isin(tools_ev)].copy()
        d_ = d_[~((d_["tool"] == "augustus") & (d_["hint"].isna() | (d_["hint"] == "abinitio")))].copy()
        d_["hint"] = d_["hint"].astype(str).str.lower().str.strip()
        d_ = d_[d_["hint"].isin(["genus", "order", "far"])].copy()
        d_["tool_pretty"] = d_["tool"].map({
            "genemarkep": "GeneMark-EP+",
            "genemarketp": "GeneMark-ETP",
            "gemoma": "GeMoMa",
            "augustus": "AUGUSTUS (hints)"
        })
        return d_

    def _abinitio_subset_local(df_):
        m_aug = (df_["tool"] == "augustus") & (df_["hint"].isna() | (df_["hint"] == "abinitio"))
        m_snap = (df_["tool"] == "snap")
        m_gmes = (df_["tool"] == "genemarkes")
        d_ = df_[m_aug | m_snap | m_gmes].copy()
        def map_snap_model(x: str) -> str:
            if not isinstance(x, str): return "Unknown"
            k = x.strip().lower()
            if k in {"arabidopsis_thaliana","a_thaliana","arabidopsis"}: return "A. thaliana"
            if k in {"oryza_sativa","o_sativa","rice"}:                 return "O. sativa"
            return x
        tool_pretty = []
        for _, r in d_.iterrows():
            if r["tool"] == "augustus":
                tool_pretty.append("AUGUSTUS (ab initio)")
            elif r["tool"] == "genemarkes":
                tool_pretty.append("GeneMark-ES")
            elif r["tool"] == "snap":
                tool_pretty.append(f"SNAP ({map_snap_model(r.get('train_species','Unknown'))})")
            else:
                tool_pretty.append(r["tool"])
        d_["tool_pretty"] = tool_pretty
        return d_

    d = df.copy()
    d["species_size_kb"] = d["species"].map(SPECIES_SIZE)
    d = d.dropna(subset=["species_size_kb"]).copy()
    d["ram_per_kb"]  = d["ram_mb"]  / d["species_size_kb"]
    d["time_per_kb"] = d["time_sec"] / d["species_size_kb"]

    d_ab = _abinitio_subset_local(d)
    by_sp_ab = (d_ab.groupby(["species","tool_pretty"], as_index=False)
                  [["ram_mb","time_sec","ram_per_kb","time_per_kb"]].mean())
    by_sp_ab["group"] = "Ab initio"

    d_ev = _evidence_subset_local(d)
    if d_ev.empty:
        warnings.warn("No evidence-based rows; plotting Ab initio only.")
        by_sp_ev = pd.DataFrame(columns=by_sp_ab.columns)
    else:
        within_hint = (d_ev.groupby(["species","tool_pretty","hint"], as_index=False)
                         [["ram_mb","time_sec","ram_per_kb","time_per_kb"]].mean())
        by_sp_ev = (within_hint.groupby(["species","tool_pretty"], as_index=False)
                      [["ram_mb","time_sec","ram_per_kb","time_per_kb"]].mean())
        by_sp_ev["group"] = "Evidence-based"

    per_species = pd.concat([by_sp_ab, by_sp_ev], ignore_index=True)

    overall = (per_species.groupby(["tool_pretty","group"], as_index=False)
                 [["ram_mb","time_sec","ram_per_kb","time_per_kb"]].mean())
    save_table_csv(overall, out_dir / "csv/all_tools_overall_ram_time.csv")

    long = overall.melt(
        id_vars=["tool_pretty","group"],
        value_vars=["ram_mb","time_sec","ram_per_kb","time_per_kb"],
        var_name="measure", value_name="value"
    )
    measure_label = {
        "ram_mb": "RAM (KB)",
        "time_sec": "Runtime (s)",
        "ram_per_kb": "RAM per genome size",
        "time_per_kb": "Runtime per genome size",
    }
    long["measure"] = long["measure"].map(measure_label)

    measures = ["RAM (KB)", "Runtime (s)", "RAM per genome size", "Runtime per genome size"] 
    fig, axes = plt.subplots(2, 2, figsize=(10, 7), sharey=True)
    axes = axes.ravel()

    for i, meas in enumerate(measures):
        sub = long[long["measure"] == meas].copy()
        if sub.empty:
            continue

        order = sub.sort_values("value")["tool_pretty"].tolist()
        sub["tool_pretty"] = pd.Categorical(sub["tool_pretty"], categories=order, ordered=True)
        sub = sub.sort_values("tool_pretty")

        ax = axes[i]
        for y in range(len(order)):
            ax.axhline(y, color="0.92", lw=0.7, zorder=0)

        sns.scatterplot(
            data=sub,
            x="value", y="tool_pretty",
            hue="group", palette={"Ab initio": "#4C78A8", "Evidence-based": "#E45756"},
            s=50, ax=ax, legend=False, zorder=3
        )
        ax.set_title(meas, fontsize=14)
        ax.set_xlabel(meas, fontsize=13)
        ax.set_ylabel(None)
        ax.grid(axis="x", linestyle=":", alpha=0.5)

    handles = [
        Line2D([0], [0], marker='o', color='w', label='Ab initio',
            markerfacecolor="#4C78A8", markersize=8),
        Line2D([0], [0], marker='o', color='w', label='Evidence-based',
            markerfacecolor="#E45756", markersize=8),
    ]

    fig.legend(
        handles=handles,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.02),
        prop={'size': 12},
        ncol=2,
        frameon=False,
        title=None
    )

    fig.suptitle("Overall RAM and runtime comparison", y=0.98, fontsize=16)
    fig.tight_layout(rect=[0.05, 0.07, 1, 0.95]) 

    fig.savefig(out_dir / "all_tools_overall_cleveland.png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)


