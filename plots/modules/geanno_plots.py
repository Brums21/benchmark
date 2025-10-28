import warnings

import matplotlib as mpl
import numpy as np
import pandas as pd
import seaborn as sns

from pathlib import Path
from typing import List, Tuple

from matplotlib import pyplot as plt

from modules.load_save import save_table_csv

from modules.common import _compute_prec_rec_f1, _concat_nonempty, _ensure_numeric,\
                        _ensure_prf_metrics, _filter_geanno_fixed_config, _is_abinitio_aug, \
                        _normalise_hint_column, _species_to_pretty, _subset_geanno_mesculenta_any
from modules.time_ram import _coerce_ram_to_gb

GEANNO_WIN = 1500
GEANNO_STEP = 50
GEANNO_THR = 0.8

#def geanno_rt_from_folder(
#    csv_dir: Path,
#    window: int | None = None,
#    step: int | None = None,
#    threshold: float | None = None,
#) -> pd.DataFrame:
#    """
#    Per-(species, tool_pretty) RAM/time table from raw folder.
#    Returns columns: species, species_pretty, tool_pretty, ram_gb/time_sec etc.
#    """
#    d = _load_geanno_raw_folder(csv_dir)
#    if window is not None:
#        d = d[pd.to_numeric(d.get("window"), errors="coerce") == window]
#    if step is not None:
#        d = d[pd.to_numeric(d.get("step"), errors="coerce") == step]
#    if threshold is not None:
#        d = d[pd.to_numeric(d.get("threshold"), errors="coerce") == threshold]
#    return d

#def _load_geanno_raw_folder(csv_dir: Path) -> pd.DataFrame:
#    """Load all GeAnno CSVs from a folder and normalise column names."""
#    frames = []
#    for p in csv_dir.glob("*.csv"):
#        df = pd.read_csv(p)
#        df["__file"] = p.name
#        frames.append(df)
#    if not frames:
#        raise FileNotFoundError(f"No CSVs found in {csv_dir}")
#    d = pd.concat(frames, ignore_index=True)
#
#    rename = {
#        "model": "tool",
#        "time": "time_sec",
#        "mem": "ram_kb",
#        "mutation_rate": "mut_rate",
#    }
#    d = d.rename(columns=rename)
#
#    d["species_pretty"] = _species_to_pretty(d["species"])
#    d["tool_pretty"]    = d["tool"].map(TOOL_MAP).fillna(d["tool"])
#    return d

def _plot_metrics_triple(g: pd.DataFrame, thr_axis: np.ndarray, tools: List[str], out_path: Path, dpi: int) -> None:
    """ Three-panel line plot (Precision / Recall / F1-score) by threshold for multiple tools"""

    fig, axes = plt.subplots(1, 3, figsize=(15, 5.0), dpi=dpi, sharex=True, sharey=True)
    metrics = [("precision","Precision"), ("recall","Recall"), ("f1","F1-score")]
    cmap = mpl.colormaps.get_cmap("tab10")

    legend_lines = []
    for col_idx, (metric, title) in enumerate(metrics):
        ax = axes[col_idx]
        for i, t in enumerate(tools):
            sub = g[g["tool_pretty"] == t]
            y = [sub.loc[sub["threshold"] == thr, metric].values[0] if thr in set(sub["threshold"]) else np.nan
                 for thr in thr_axis]
            (ln,) = ax.plot(thr_axis, y, marker="o", linewidth=1.8, markersize=6, label=t, color=cmap(i % cmap.N))
            if col_idx == 0:
                legend_lines.append(ln)
        ax.set_title(title, fontsize=14)
        ax.set_xlabel("Threshold")
        ax.grid(axis="y", linestyle="--", alpha=0.35)
    axes[0].set_ylabel("Value")
    axes[0].set_xlim(float(np.nanmin(thr_axis)), float(np.nanmax(thr_axis))); axes[0].set_ylim(0, 1)

    fig.legend(handles=legend_lines, labels=[t for t in tools], loc="lower center",
               ncol=min(4, len(tools)), frameon=False, prop={'size': 12})
    fig.suptitle("Metrics by threshold", y=1, fontsize=17)
    fig.tight_layout(rect=[0, 0.12, 1, 0.95])
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)

def export_threshold_curves_and_tripanel(
    d: pd.DataFrame, out_dir: Path, dpi: int = 300,
    window: int = GEANNO_WIN, step: int = GEANNO_STEP, mut_rate: float = 0.0
) -> None:
    """Export mean metrics by tool and threshold at a fixed window/step and mutation rate, plus a 3-panel figure."""
    dd = _ensure_numeric(d, ["window","step","threshold","tp","fp","fn","mut_rate"])
    df = dd[(dd["window"] == window) & (dd["step"] == step) & (dd["mut_rate"].fillna(0) == mut_rate)].copy()
    df = _compute_prec_rec_f1(df)

    g = (df.groupby(["tool_pretty","threshold"], as_index=False)
           .agg(precision=("precision","mean"),
                recall=("recall","mean"),
                f1=("f1","mean"))
           .sort_values(["tool_pretty","threshold"]))
    save_table_csv(g, out_dir / "csv/geanno_metrics_by_threshold.csv")

    tools = g["tool_pretty"].drop_duplicates().tolist()
    thr_axis = np.sort(g["threshold"].dropna().unique())
    _plot_metrics_triple(g, thr_axis, tools, out_dir / "geanno_metrics_by_threshold_triple.png", dpi)

def export_window_step_by_species_mut0(d_perf: pd.DataFrame, out_dir: Path) -> None:
    """Table: mean metrics and resources by species, window and step at mut_rate=0"""
    dd = _coerce_ram_to_gb(d_perf.copy())

    dd = _ensure_numeric(dd, ["tp","fp","fn","time_sec","ram_gb","window","step","sensitivity","specificity","mut_rate"])
    dd = dd[dd["mut_rate"].fillna(0) == 0].copy()
    dd = _compute_prec_rec_f1(dd)

    agg = (dd.groupby(["species","species_pretty","window","step"], as_index=False)
             .agg(
                 n_runs           = ("time_sec", "size"),
                 mean_time_sec    = ("time_sec","mean"),
                 mean_ram_gb      = ("ram_gb","mean"),
                 mean_sensitivity = ("sensitivity","mean"),
                 mean_specificity = ("specificity","mean"),
                 mean_precision   = ("precision","mean"),
                 mean_recall      = ("recall","mean"),
                 mean_f1          = ("f1","mean"),
             ))
    save_table_csv(agg, out_dir / "csv/geanno_window_step_by_species.csv")

def export_all_tools_table_csv(
    df_bench: pd.DataFrame,
    df_geanno: pd.DataFrame,
    out_dir: Path,
    mut_rate: float = 0.0,
    window: int = GEANNO_WIN,
    step: int = GEANNO_STEP,
    threshold: float = GEANNO_THR,
    decimals: int = 2,
) -> Tuple[Path, pd.DataFrame]:
    """ Precision, Recall, F1-score table for ALL tools at a fixed mutation rate. """
    
    out_dir.mkdir(parents=True, exist_ok=True)

    def _pct_round(s: pd.Series) -> pd.Series:
        return (pd.to_numeric(s, errors="coerce") * 100.0).round(decimals)

    b = df_bench.copy()
    b["tool_l"] = b["tool"].astype(str).str.lower().str.strip()
    b["hint_l"] = _normalise_hint_column(b)
    b["species_pretty"] = _species_to_pretty(b["species"])

    b = _ensure_prf_metrics(b)
    if "mut_rate" in b.columns:
        b = b[pd.to_numeric(b["mut_rate"], errors="coerce").fillna(0) == mut_rate].copy()

    aug_ab = b[_is_abinitio_aug(b)][["species","species_pretty","precision","recall","f1"]].copy()
    aug_ab["column"] = "AUGUSTUS (ab initio)"

    snap = b[b["tool_l"].eq("snap")].copy()
    snap["train_species_norm"] = snap.get("train_species","").astype(str).str.lower().str.strip()

    snap_arab = snap[snap["train_species_norm"].isin({"arabidopsis","arabidopsis_thaliana","a_thaliana"})]
    snap_arab = snap_arab[["species","species_pretty","precision","recall","f1"]].copy()
    snap_arab["column"] = "SNAP (A. thaliana*)"

    snap_rice = snap[snap["train_species_norm"].isin({"oryza_sativa","o_sativa","rice"})]
    snap_rice = snap_rice[["species","species_pretty","precision","recall","f1"]].copy()
    snap_rice["column"] = "SNAP (O. sativa*)"

    gmes = b[b["tool_l"].eq("genemarkes")][["species","species_pretty","precision","recall","f1"]].copy()
    gmes["column"] = "GeneMark-ES"

    ab_parts = [aug_ab, snap_arab, snap_rice, gmes]
    ab_block = _concat_nonempty(ab_parts, cols=["species","species_pretty","precision","recall","f1","column"])

    allowed_hints = {"genus","order","far"}
    is_ev = (
        b["tool_l"].isin({"genemarkep","genemarketp","gemoma"}) |
        (b["tool_l"].eq("augustus") & b["hint_l"].notna() & ~b["hint_l"].eq("abinitio"))
    )
    ev = b[is_ev & b["hint_l"].isin(allowed_hints)].copy()
    if not ev.empty:
        ev["tool_pretty"] = ev["tool_l"].map({
            "genemarkep":  "GeneMark-EP+",
            "genemarketp": "GeneMark-ETP",
            "gemoma":      "GeMoMa",
            "augustus":    "AUGUSTUS (hints)",
        }).fillna(ev["tool"])
        per_hint = (
            ev.groupby(["species","species_pretty","tool_pretty","hint_l"], as_index=False)
              [["precision","recall","f1"]].mean()
        )
        ev_macro = (
            per_hint.groupby(["species","species_pretty","tool_pretty"], as_index=False)
                    [["precision","recall","f1"]].mean()
        )
        ev_macro = ev_macro.rename(columns={"tool_pretty":"column"})
    else:
        ev_macro = pd.DataFrame(columns=["species","species_pretty","precision","recall","f1","column"])

    g = _ensure_prf_metrics(df_geanno.copy())
    g = _filter_geanno_fixed_config(g, win=window, step=step, thr=threshold)
    g = _subset_geanno_mesculenta_any(g).copy()
    if "mut_rate" in g.columns:
        g = g[pd.to_numeric(g["mut_rate"], errors="coerce").fillna(0) == mut_rate].copy()
    if not g.empty:
        g["species_pretty"] = _species_to_pretty(g["species"])
        ge = (g.groupby(["species","species_pretty"], as_index=False)
                [["precision","recall","f1"]].mean())
        ge["column"] = "GeAnno (M. esculenta, PCA)"
    else:
        ge = pd.DataFrame(columns=["species","species_pretty","precision","recall","f1","column"])

    comb = _concat_nonempty([ab_block, ev_macro, ge],
                            cols=["species","species_pretty","precision","recall","f1","column"])

    col_order_master = [
        "AUGUSTUS (ab initio)",
        "SNAP (A. thaliana*)", "SNAP (O. sativa*)",
        "GeneMark-ES",
        "GeneMark-EP+", "GeneMark-ETP", "GeMoMa", "AUGUSTUS (hints)",
        "GeAnno (M. esculenta, PCA)",
    ]
    present_cols = [c for c in col_order_master if c in set(comb["column"])]

    species_pref = ["A. thaliana", "G. raimondii", "M. esculenta", "O. sativa"]
    species_present = [s for s in species_pref if s in set(comb["species_pretty"])] \
                      or list(comb["species_pretty"].drop_duplicates())

    blocks = []
    for metric, mlabel in (("precision","Precision"), ("recall","Recall"), ("f1","F1-score")):
        piv = (comb.pivot_table(index="species_pretty", columns="column", values=metric, aggfunc="mean")
                     .reindex(index=species_present, columns=present_cols))

        piv = piv.apply(_pct_round)
        piv.insert(0, "Metric", mlabel)
        piv.insert(1, "Species", piv.index)
        block = piv.reset_index(drop=True)

        avg_vals = {c: round(block[c].mean(skipna=True), decimals) for c in present_cols}
        avg_row = {"Metric": mlabel, "Species": "Avg.", **avg_vals}
        block = pd.concat([block, pd.DataFrame([avg_row])], ignore_index=True)
        blocks.append(block)

    out_df = pd.concat(blocks, ignore_index=True)
    out_df = out_df[["Metric","Species"] + present_cols]

    csv_path = out_dir / f"csv/all_tools_table_mut{mut_rate}_win{window}_step{step}_thr{threshold}.csv"
    save_table_csv(out_df, csv_path)
    return csv_path, out_df

