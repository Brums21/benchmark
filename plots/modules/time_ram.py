import warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sns

from typing import Tuple
from pathlib import Path
from matplotlib.lines import Line2D

from modules.load_save import save_table_csv
from modules.common import SPECIES_SIZE, TOOL_MAPPING, \
                        _ensure_numeric, _filter_geanno_fixed_config, \
                        _is_abinitio_aug, _map_snap_model, \
                        _normalise_hint_column, _species_to_pretty, \
                        _subset_geanno_mesculenta_any

def _coerce_ram_to_gb(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with a canonical float `ram_gb` from various RAM columns."""
    d = df.copy()

    def to_num(col):
        return pd.to_numeric(d[col], errors="coerce") if col in d.columns else None

    if "ram_gb" in d.columns:
        d["ram_gb"] = to_num("ram_gb")
        return d

    if "ram_bytes" in d.columns:
        d["ram_gb"] = to_num("ram_bytes") / (1024.0 ** 3)
        return d

    for kb_col in ("ram_kb", "max_rss_kb"):
        if kb_col in d.columns:
            d["ram_gb"] = to_num(kb_col) / (1024.0 ** 2)
            return d

    for mb_col in ("ram_mb", "memory_mb", "max_rss_mb"):
        if mb_col in d.columns:
            d["ram_gb"] = to_num(mb_col) / (1024.0 ** 2)
            return d

    for amb in ("mem", "memory"):
        s = to_num(amb)
        if amb in d.columns:
            s = to_num(amb)
            d["ram_gb"] = s / (1024.0 ** 2)

    d["ram_gb"] = np.nan
    return d

def _make_views(d: pd.DataFrame) -> pd.DataFrame:
    """From raw benchmark DataFrame, make a view with ram_gb and time_sec, plus normalized columns."""

    d_rt = _coerce_ram_to_gb(d) 
    d_rt = _ensure_numeric(d_rt, ["time_sec"])
    d_rt = d_rt.dropna(subset=["time_sec", "ram_gb"]).copy()

    d_rt["species_pretty"] = _species_to_pretty(d_rt["species"])
    d_rt["tool_pretty"] = (d_rt["tool"].astype(str).str.lower().map(TOOL_MAPPING).fillna(d_rt["tool"]))

    d_rt["species_size_kb"] = d_rt["species"].map(SPECIES_SIZE).astype(float)
    d_rt = d_rt.dropna(subset=["species_size_kb"]).copy()
    d_rt["ram_per_kb"]  = d_rt["ram_gb"] / d_rt["species_size_kb"]
    d_rt["time_per_kb"] = d_rt["time_sec"] / d_rt["species_size_kb"]

    return d_rt

def plot_ram_time_summaries_and_plots(
    d: pd.DataFrame, out_dir: Path, dpi: int = 300
) -> None:
    """Aggregate RAM/time by species and tool and produce two line-pair plots."""
    d = _make_views(d)

    agg = (d.groupby(["species","species_pretty","tool_pretty"], as_index=False)
             [["ram_gb","time_sec","ram_per_kb","time_per_kb"]].mean())
    save_table_csv(agg, out_dir / "csv/geanno_ram_time_summary.csv")


    def lineplot_pair(metric_left, ylabel_left, title_left,
                      metric_right, ylabel_right, title_right, fname, pad=0.10):
        species = agg["species_pretty"].drop_duplicates().tolist()
        tools   = agg["tool_pretty"].drop_duplicates().tolist()
        x = np.arange(len(species))
        cmap = mpl.colormaps.get_cmap("tab10")
        colors = [cmap(i % cmap.N) for i in range(len(tools))]

        fig, axes = plt.subplots(1, 2, figsize=(12, 5.6), dpi=dpi, sharex=True)
        axL, axR = axes

        # left
        lines = []
        for i, t in enumerate(tools):
            sub = agg[agg["tool_pretty"] == t]
            y = [sub.loc[sub["species_pretty"] == s, metric_left].values[0]
                 if not sub.loc[sub["species_pretty"] == s].empty else np.nan
                 for s in species]
            ln, = axL.plot(x, y, marker="o", linewidth=1.8, markersize=6, color=colors[i], label=t)
            lines.append(ln)
        axL.set_xticks(x); axL.set_xticklabels(species, rotation=25, ha="right")
        axL.set_xlabel("Species"); axL.set_ylabel(ylabel_left); axL.set_title(title_left)
        axL.grid(axis="y", linestyle="--", alpha=0.35)
        ymaxL = float(np.nanmax(agg[metric_left].to_numpy(dtype=float)))
        axL.set_ylim(0, ymaxL * (1+pad) if ymaxL > 0 else 1.0)

        # right
        for i, t in enumerate(tools):
            sub = agg[agg["tool_pretty"] == t]
            y = [sub.loc[sub["species_pretty"] == s, metric_right].values[0]
                 if not sub.loc[sub["species_pretty"] == s].empty else np.nan
                 for s in species]
            axR.plot(x, y, marker="o", linewidth=1.8, markersize=6, color=colors[i], label=t)
        axR.set_xticks(x); axR.set_xticklabels(species, rotation=25, ha="right")
        axR.set_xlabel("Species"); axR.set_ylabel(ylabel_right); axR.set_title(title_right)
        axR.grid(axis="y", linestyle="--", alpha=0.35)
        ymaxR = float(np.nanmax(agg[metric_right].to_numpy(dtype=float)))
        axR.set_ylim(0, ymaxR * (1+pad) if ymaxR > 0 else 1.0)

        fig.legend(handles=lines, labels=[t for t in tools], loc="lower center", ncol=4, frameon=False)
        fig.tight_layout(rect=[0, 0.10, 1, 1])
        fig.savefig(out_dir / fname, bbox_inches="tight")
        plt.close(fig)

    lineplot_pair(
        metric_left="ram_gb", ylabel_left="RAM (GB)", title_left="RAM (GB) by species and model",
        metric_right="ram_per_kb", ylabel_right="RAM (GB) per genome size (KB)",
        title_right="Normalized RAM (GB) by species and model",
        fname="geanno_ram_pair.png"
    )
    lineplot_pair(
        metric_left="time_sec", ylabel_left="Runtime (s)", title_left="Runtime (s) by species and model",
        metric_right="time_per_kb", ylabel_right="Runtime (s) per genome size (KB)",
        title_right="Normalized runtime (s) by species and model",
        fname="geanno_time_pair.png"
    )


def plot_ram_time_all_tools_by_species_linepairs_plus_geanno(
    df_bench: pd.DataFrame,
    df_geanno: pd.DataFrame,
    out_dir: Path,
    dpi: int = 300
) -> Tuple[Tuple[Path, Path], pd.DataFrame]:
    """ Plot RAM and time consumption for all tools, where x is the species and lines are tools """
    
    out_dir.mkdir(parents=True, exist_ok=True)

    def _evidence_subset_local(df_: pd.DataFrame) -> pd.DataFrame:
        tools_ev = {"genemarkep", "genemarketp", "gemoma", "augustus"}
        d_ = df_[df_["tool"].astype(str).str.lower().isin(tools_ev)].copy()
        d_["hint_l"] = _normalise_hint_column(d_)

        d_ = d_[~((d_["tool"].astype(str).str.lower() == "augustus") & (d_["hint_l"].isna() | d_["hint_l"].eq("abinitio")))]
        d_ = d_[d_["hint_l"].isin(["genus", "order", "far"])]
        d_["tool_pretty"] = d_["tool"].astype(str).str.lower().map({
            "genemarkep": "GeneMark-EP+",
            "genemarketp": "GeneMark-ETP",
            "gemoma": "GeMoMa",
            "augustus": "AUGUSTUS (hints)"
        })
        return d_

    def _abinitio_subset_local(df_: pd.DataFrame) -> pd.DataFrame:
        d_ = df_.copy()
        d_["hint_l"] = _normalise_hint_column(d_)
        m_aug = _is_abinitio_aug(d_)
        m_snap = d_["tool"].astype(str).str.lower().eq("snap")
        m_gmes = d_["tool"].astype(str).str.lower().eq("genemarkes")
        d_ = d_[m_aug | m_snap | m_gmes].copy()

        def _tool_pretty_row(r) -> str:
            tl = str(r["tool"]).lower()
            if tl == "augustus":   return "AUGUSTUS (ab initio)"
            if tl == "genemarkes": return "GeneMark-ES"
            if tl == "snap":       return f"SNAP ({_map_snap_model(r.get('train_species','Unknown'))})"
            return r["tool"]
        d_["tool_pretty"] = [_tool_pretty_row(r) for _, r in d_.iterrows()]
        return d_

    d = _coerce_ram_to_gb(df_bench.copy())
    d["species_pretty"] = _species_to_pretty(d["species"])
    d["species_size_kb"] = d["species"].map(SPECIES_SIZE)
    d = d.dropna(subset=["species_size_kb"]).copy()

    if "time_sec" not in d.columns and "time" in d.columns:
        d = d.rename(columns={"time": "time_sec"})

    d["ram_per_kb"]  = d["ram_gb"]  / d["species_size_kb"]
    d["time_per_kb"] = d["time_sec"] / d["species_size_kb"]

    d_ab = _abinitio_subset_local(d)
    by_sp_ab = (d_ab.groupby(["species","species_pretty","tool_pretty"], as_index=False)
                    [["ram_gb","time_sec","ram_per_kb","time_per_kb"]].mean())

    d_ev = _evidence_subset_local(d)
    if d_ev.empty:
        by_sp_ev = pd.DataFrame(columns=by_sp_ab.columns)
    else:
        within_hint = (d_ev.groupby(["species","species_pretty","tool_pretty","hint_l"], as_index=False)
                           [["ram_gb","time_sec","ram_per_kb","time_per_kb"]].mean())
        by_sp_ev = (within_hint.groupby(["species","species_pretty","tool_pretty"], as_index=False)
                             [["ram_gb","time_sec","ram_per_kb","time_per_kb"]].mean())

    g = _coerce_ram_to_gb(df_geanno.copy())
    if "time_sec" not in g.columns and "time" in g.columns:
        g = g.rename(columns={"time": "time_sec"})

    g = _filter_geanno_fixed_config(g)

    g["species_pretty"] = _species_to_pretty(g["species"])
    g["species_size_kb"] = g["species"].map(SPECIES_SIZE)
    g = g.dropna(subset=["species_size_kb"]).copy()
    g["ram_per_kb"]  = g["ram_gb"]  / g["species_size_kb"]
    g["time_per_kb"] = g["time_sec"] / g["species_size_kb"]
    g = _subset_geanno_mesculenta_any(g)

    if g.empty:
        by_sp_ge = pd.DataFrame(columns=by_sp_ab.columns)
    else:
        by_sp_ge = (g.groupby(["species","species_pretty"], as_index=False)
                      [["ram_gb","time_sec","ram_per_kb","time_per_kb"]].mean())
        by_sp_ge["tool_pretty"] = "GeAnno (M. esculenta, PCA)"

    per_species = pd.concat([by_sp_ab, by_sp_ev, by_sp_ge], ignore_index=True)
    per_species = per_species.sort_values(["tool_pretty","species_pretty"]).reset_index(drop=True)
    save_table_csv(per_species, out_dir / "csv/all_tools_by_species_ram_time_plus_geanno.csv")

    species = ["A. thaliana","G. raimondii","M. esculenta","O. sativa"]
    species_present = [s for s in species if s in set(per_species["species_pretty"])] \
                      or list(per_species["species_pretty"].drop_duplicates())
    tools = list(per_species["tool_pretty"].drop_duplicates())
    palette = dict(zip(tools, sns.color_palette(n_colors=len(tools))))
    x = np.arange(len(species_present))

    def _linepair(metric_left, ylabel_left, title_left,
                  metric_right, ylabel_right, title_right, fname, pad=0.10) -> Path:
        fig, axes = plt.subplots(1, 2, figsize=(13.0, 6.0), dpi=dpi, sharex=True)
        axL, axR = axes
        lines = []

        for i, t in enumerate(tools):
            sub = per_species[per_species["tool_pretty"] == t]
            y = [sub.loc[sub["species_pretty"] == s, metric_left].mean() if (sub["species_pretty"] == s).any() else np.nan
                 for s in species_present]
            ln, = axL.plot(x, y, marker="o", linewidth=1.8, markersize=6, color=palette[t], label=t)
            lines.append(ln)
        axL.set_xticks(x); axL.set_xticklabels(species_present, rotation=25, ha="right")
        axL.set_xlabel("Species"); axL.set_ylabel(ylabel_left); axL.set_title(title_left)
        axL.grid(axis="y", linestyle=":", alpha=0.5)
        ymaxL = float(np.nanmax(per_species[metric_left].to_numpy(dtype=float))) if not per_species.empty else 1.0
        axL.set_ylim(0, ymaxL * (1 + pad) if ymaxL > 0 else 1.0)

        for i, t in enumerate(tools):
            sub = per_species[per_species["tool_pretty"] == t]
            y = [sub.loc[sub["species_pretty"] == s, metric_right].mean() if (sub["species_pretty"] == s).any() else np.nan
                 for s in species_present]
            axR.plot(x, y, marker="o", linewidth=1.8, markersize=6, color=palette[t], label=t)
        axR.set_xticks(x); axR.set_xticklabels(species_present, rotation=25, ha="right")
        axR.set_xlabel("Species"); axR.set_ylabel(ylabel_right); axR.set_title(title_right)
        axR.grid(axis="y", linestyle=":", alpha=0.5)
        ymaxR = float(np.nanmax(per_species[metric_right].to_numpy(dtype=float))) if not per_species.empty else 1.0
        axR.set_ylim(0, ymaxR * (1 + pad) if ymaxR > 0 else 1.0)

        fig.legend(handles=lines, labels=[t for t in tools], loc="lower center",
                   ncol=min(4, len(tools)), frameon=False, fontsize=10)
        fig.tight_layout(rect=[0, 0.10, 1, 1])
        out_path = out_dir / fname
        fig.savefig(out_path, bbox_inches="tight")
        plt.close(fig)
        return out_path

    ram_png  = _linepair(
        metric_left="ram_gb", ylabel_left="RAM (GB)", title_left="RAM (GB) by species",
        metric_right="ram_per_kb", ylabel_right="RAM (GB) per genome size (KB)",
        title_right="Normalized RAM (GB) by species", fname="all_tools_ram_pair_plus_geanno.png"
    )
    time_png = _linepair(
        metric_left="time_sec", ylabel_left="Runtime (s)", title_left="Runtime (s) by species",
        metric_right="time_per_kb", ylabel_right="Runtime (s) per genome size (KB)",
        title_right="Normalized runtime (s) by species", fname="all_tools_time_pair_plus_geanno.png"
    )

    return (ram_png, time_png), per_species


def plot_ram_time_all_tools_overall_dots_plus_geanno(df_bench: pd.DataFrame, df_geanno: pd.DataFrame, out_dir: Path, dpi: int = 300) -> Tuple[Path, pd.DataFrame]:
    """ RAM/Runtime Cleveland dots for all tools, where y is the tool and dots are the values """
    out_dir.mkdir(parents=True, exist_ok=True)

    def _evidence_subset_local(df_: pd.DataFrame) -> pd.DataFrame:
        tools_ev = {"genemarkep", "genemarketp", "gemoma", "augustus"}
        d_ = df_[df_["tool"].astype(str).str.lower().isin(tools_ev)].copy()
        d_["hint_l"] = _normalise_hint_column(d_)
        d_ = d_[~((d_["tool"].astype(str).str.lower() == "augustus") & (d_["hint_l"].isna() | d_["hint_l"].eq("abinitio")))]
        d_ = d_[d_["hint_l"].isin(["genus", "order", "far"])]
        d_["tool_pretty"] = d_["tool"].astype(str).str.lower().map({
            "genemarkep": "GeneMark-EP+",
            "genemarketp": "GeneMark-ETP",
            "gemoma": "GeMoMa",
            "augustus": "AUGUSTUS (hints)"
        })
        return d_

    def _abinitio_subset_local(df_: pd.DataFrame) -> pd.DataFrame:
        d_ = df_.copy()
        d_["hint_l"] = _normalise_hint_column(d_)
        m_aug = _is_abinitio_aug(d_)
        m_snap = d_["tool"].astype(str).str.lower().eq("snap")
        m_gmes = d_["tool"].astype(str).str.lower().eq("genemarkes")
        d_ = d_[m_aug | m_snap | m_gmes].copy()

        def _tool_pretty_row(r) -> str:
            tl = str(r["tool"]).lower()
            if tl == "augustus":   return "AUGUSTUS (ab initio)"
            if tl == "genemarkes": return "GeneMark-ES"
            if tl == "snap":       return f"SNAP ({_map_snap_model(r.get('train_species','Unknown'))})"
            return r["tool"]
        d_["tool_pretty"] = [_tool_pretty_row(r) for _, r in d_.iterrows()]
        return d_

    d = _coerce_ram_to_gb(df_bench.copy())
    d["species_size_kb"] = d["species"].map(SPECIES_SIZE)
    d = d.dropna(subset=["species_size_kb"]).copy()

    if "time_sec" not in d.columns and "time" in d.columns:
        d = d.rename(columns={"time": "time_sec"})

    d["ram_per_kb"]  = d["ram_gb"]  / d["species_size_kb"]
    d["time_per_kb"] = d["time_sec"] / d["species_size_kb"]

    d_ab = _abinitio_subset_local(d)
    by_sp_ab = (d_ab.groupby(["species","tool_pretty"], as_index=False)[["ram_gb","time_sec","ram_per_kb","time_per_kb"]].mean())
    by_sp_ab["group"] = "Ab initio"

    d_ev = _evidence_subset_local(d)
    if d_ev.empty:
        warnings.warn("No evidence-based rows; plotting Ab initio + GeAnno only.")
        by_sp_ev = pd.DataFrame(columns=by_sp_ab.columns)
    else:
        within_hint = (d_ev.groupby(["species","tool_pretty","hint_l"], as_index=False)[["ram_gb","time_sec","ram_per_kb","time_per_kb"]].mean())
        by_sp_ev = (within_hint.groupby(["species","tool_pretty"], as_index=False)[["ram_gb","time_sec","ram_per_kb","time_per_kb"]].mean())
        by_sp_ev["group"] = "Evidence-based"

    g = _coerce_ram_to_gb(df_geanno.copy())
    if "time_sec" not in g.columns and "time" in g.columns:
        g = g.rename(columns={"time": "time_sec"})

    g = _filter_geanno_fixed_config(g)

    g["species_size_kb"] = g["species"].map(SPECIES_SIZE)
    g = g.dropna(subset=["species_size_kb"]).copy()
    g["ram_per_kb"]  = g["ram_gb"]  / g["species_size_kb"]
    g["time_per_kb"] = g["time_sec"] / g["species_size_kb"]

    g = _subset_geanno_mesculenta_any(g)

    if g.empty:
        warnings.warn("No GeAnno rows for M. esculenta (PCA) with the fixed config.")
        by_sp_ge = pd.DataFrame(columns=by_sp_ab.columns)
    else:
        by_sp_ge = (g.groupby(["species"], as_index=False)[["ram_gb","time_sec","ram_per_kb","time_per_kb"]].mean())
        by_sp_ge["tool_pretty"] = "GeAnno (M. esculenta, PCA)"
        by_sp_ge["group"] = "GeAnno"

    per_species = pd.concat([by_sp_ab, by_sp_ev, by_sp_ge], ignore_index=True)
    overall = (per_species.groupby(["tool_pretty","group"], as_index=False)[["ram_gb","time_sec","ram_per_kb","time_per_kb"]].mean())

    save_table_csv(overall, out_dir / "csv/all_tools_overall_ram_time_plus_geanno.csv")

    long = overall.melt(id_vars=["tool_pretty","group"],
                        value_vars=["ram_gb","time_sec","ram_per_kb","time_per_kb"],
                        var_name="measure", value_name="value")
    measure_label = {
        "ram_gb":      "RAM (GB)",
        "time_sec":    "Runtime (s)",
        "ram_per_kb":  "RAM (GB) per genome size (KB)",
        "time_per_kb": "Runtime (s) per genome size (KB)",
    }
    long["measure"] = long["measure"].map(measure_label)

    titles = {
        "RAM (GB)":                          "Overall RAM usage (GB)",
        "Runtime (s)":                       "Overall runtime (s)",
        "RAM (GB) per genome size (KB)":     "RAM usage normalized by genome size (per KB)",
        "Runtime (s) per genome size (KB)":  "Runtime normalized by genome size (per KB)",
    }

    xlabels = {
        "RAM (GB)":                          "RAM (GB)",
        "Runtime (s)":                       "Runtime (s)",
        "RAM (GB) per genome size (KB)":     "RAM (GB) per genome size (KB)",
        "Runtime (s) per genome size (KB)":  "Runtime (s) per genome size (KB)",
    }

    hue_map = {"Ab initio": "#4C78A8", "Evidence-based": "#E45756", "GeAnno": "#2CA02C"}
    measures = list(titles.keys())

    fig, axes = plt.subplots(2, 2, figsize=(13, 7), sharey=True)
    axes = axes.ravel()

    for i, meas in enumerate(measures):
        sub = long[long["measure"] == meas].copy()
        if sub.empty: continue

        order = sub.sort_values("value")["tool_pretty"].tolist()
        sub["tool_pretty"] = pd.Categorical(sub["tool_pretty"], categories=order, ordered=True)
        sub = sub.sort_values("tool_pretty")

        ax = axes[i]
        for y in range(len(order)):
            ax.axhline(y, color="0.92", lw=0.7, zorder=0)

        sns.scatterplot(data=sub, x="value", y="tool_pretty", hue="group", palette=hue_map, s=55, ax=ax, zorder=3, legend=False)
        ax.set_title(titles[meas], fontsize=13, pad=10)
        ax.set_xlabel(xlabels[meas], fontsize=11)
        ax.set_ylabel(None)
        ax.grid(axis="x", linestyle=":", alpha=0.5)

    fig.legend(
        handles=[
            Line2D([0],[0], marker='o', color='w', label='Ab initio', markerfacecolor=hue_map["Ab initio"], markersize=8),
            Line2D([0],[0], marker='o', color='w', label='Evidence-based', markerfacecolor=hue_map["Evidence-based"], markersize=8),
            Line2D([0],[0], marker='o', color='w', label='GeAnno', markerfacecolor=hue_map["GeAnno"], markersize=8),
        ],
        loc="lower center", bbox_to_anchor=(0.5, 0.02), frameon=False, ncol=3, prop={'size': 12}
    )

    fig.suptitle("Overall RAM and runtime comparison across tools", y=0.98, fontsize=16)
    fig.tight_layout(rect=[0.05, 0.08, 1, 0.97])
    fig_path = out_dir / "all_tools_overall_cleveland_plus_geanno.png"
    fig.savefig(fig_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return fig_path, overall

    