from pathlib import Path
from typing import Iterable, List, Optional, Tuple, Dict

import warnings
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D

from load_save import save_table_csv, load_geanno, SPECIES_PRETTY, TOOL_MAP, SPECIES_SIZE

GEANNO_WIN = 1500
GEANNO_STEP = 50
GEANNO_THR = 0.8

def _species_to_pretty(s: pd.Series) -> pd.Series:
    return s.map(SPECIES_PRETTY).fillna(s.astype(str).str.replace("_", " ").str.title())

def _ensure_numeric(df: pd.DataFrame, cols) -> pd.DataFrame:
    d = df.copy()
    for c in cols:
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce")
    return d

def _compute_prec_rec_f1(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    for c in ("tp","fp","fn"):
        if c not in d.columns:
            raise ValueError(f"Missing column: {c}")
    tp = pd.to_numeric(d["tp"], errors="coerce")
    fp = pd.to_numeric(d["fp"], errors="coerce")
    fn = pd.to_numeric(d["fn"], errors="coerce")
    with np.errstate(divide="ignore", invalid="ignore"):
        prec = tp / (tp + fp)
        rec  = tp / (tp + fn)
        f1   = (2 * prec * rec) / (prec + rec)
    d["precision"] = prec.replace([np.inf, -np.inf], np.nan)
    d["recall"]    = rec.replace([np.inf, -np.inf], np.nan)
    d["f1"]        = f1.replace([np.inf, -np.inf], np.nan)
    return d

def _load_geanno_raw_folder(csv_dir: Path) -> pd.DataFrame:
    """Load all GeAnno CSVs from a folder and normalise column names."""
    frames = []
    for p in csv_dir.glob("*.csv"):
        df = pd.read_csv(p)
        df["__file"] = p.name
        frames.append(df)
    if not frames:
        raise FileNotFoundError(f"No CSVs found in {csv_dir}")
    d = pd.concat(frames, ignore_index=True)

    rename = {
        "model": "tool",
        "time": "time_sec",
        "mem": "ram_kb",
        "mutation_rate": "mut_rate",
    }
    d = d.rename(columns=rename)

    d["species_pretty"] = _species_to_pretty(d["species"])
    d["tool_pretty"]    = d["tool"].map(TOOL_MAP).fillna(d["tool"])
    return d

def _ensure_prf_metrics(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    have = set(d.columns)

    if "precision" not in have and "specificity" in have:
        d["precision"] = d["specificity"]
    if "recall" not in have and "sensitivity" in have:
        d["recall"] = d["sensitivity"]
    if "f1" not in have and {"precision", "recall"}.issubset(d.columns):
        denom = (pd.to_numeric(d["precision"], errors="coerce")
                 + pd.to_numeric(d["recall"], errors="coerce")).replace(0, np.nan)
        d["f1"] = (2 * pd.to_numeric(d["precision"], errors="coerce")
                     * pd.to_numeric(d["recall"], errors="coerce")) / denom
        d["f1"] = d["f1"].fillna(0)

    for col in ("precision", "recall", "f1"):
        if col in d.columns:
            d[col] = pd.to_numeric(d[col], errors="coerce")
            if d[col].max(skipna=True) > 1:
                d[col] = d[col] / 100.0
            d[col] = d[col].clip(0, 1)

    return d

def _normalise_hint_column(df: pd.DataFrame, src_col: str = "hint") -> pd.Series:
    if src_col not in df.columns:
        return pd.Series(pd.NA, index=df.index, name="hint_l")
    s = df[src_col].copy()
    m = s.notna()
    s.loc[m] = s.loc[m].astype(str).str.lower().str.strip()
    return s.rename("hint_l")

def _is_abinitio_aug(df: pd.DataFrame) -> pd.Series:
    hint_l = df.get("hint_l", _normalise_hint_column(df))
    return (df["tool"].astype(str).str.lower().eq("augustus") & (hint_l.isna() | hint_l.eq("abinitio")))

def _map_snap_model(x: str) -> str:
    if not isinstance(x, str): return "Unknown"
    k = x.strip().lower()
    if k in {"arabidopsis_thaliana", "a_thaliana", "arabidopsis"}: return "A. thaliana"
    if k in {"oryza_sativa", "o_sativa", "rice"}:                 return "O. sativa"
    return x

def _concat_nonempty(dfs: Iterable[pd.DataFrame], cols: Optional[List[str]] = None) -> pd.DataFrame:
    parts = [x for x in dfs if x is not None and not x.empty]
    if not parts:
        return pd.DataFrame(columns=cols or [])
    return pd.concat(parts, ignore_index=True)

def _palette_for_tools(tools: List[str]) -> Dict[str, Tuple[float, float, float]]:
    base_palette = sns.color_palette("tab10", n_colors=max(4, len(tools)))
    return {t: base_palette[i % len(base_palette)] for i, t in enumerate(tools)}

def _linestyle_for_tools(tools: Iterable[str]) -> Tuple[Dict[str, str], Dict[str, float]]:
    tool_ls, tool_lw = {}, {}
    for t in tools:
        is_geanno = "geanno" in str(t).lower()
        tool_ls[t] = "--" if is_geanno else "-"
        tool_lw[t] = 2.4 if is_geanno else 1.8
    return tool_ls, tool_lw


def _filter_geanno_fixed_config(df: pd.DataFrame,
                                win: int = GEANNO_WIN,
                                step: int = GEANNO_STEP,
                                thr: float = GEANNO_THR) -> pd.DataFrame:
    """
    Keep only GeAnno rows at the fixed operating point: window=win, step=step, threshold=thr.
    Works with alternate column names (win/stride, thr).
    Does NOT filter mutation rate (so curves across mut_rate still work).
    """
    d = df.copy()

    def _col_like(cols: Iterable[str], *cands: str) -> Optional[str]:
        cols = set(cols)
        for c in cands:
            if c in cols:
                return c
        return None

    win_col  = _col_like(d.columns, "window", "win")
    step_col = _col_like(d.columns, "step", "stride")
    thr_col  = _col_like(d.columns, "threshold", "thr")

    if win_col is not None:
        d = d[pd.to_numeric(d[win_col], errors="coerce") == win]
    if step_col is not None:
        d = d[pd.to_numeric(d[step_col], errors="coerce") == step]
    if thr_col is not None:
        d = d[pd.to_numeric(d[thr_col], errors="coerce") == thr]

    return d

def geanno_fixedpoint_from_df(df: pd.DataFrame,
                              window: int = GEANNO_WIN,
                              step: int = GEANNO_STEP,
                              threshold: float = GEANNO_THR,
                              mut_rate: float = 0.0) -> pd.DataFrame:
    d = df.copy()
    d = _ensure_numeric(d, ["window","step","threshold","tp","fp","fn","mut_rate"])
    sel = (
        (d["window"] == window) &
        (d["step"] == step) &
        (d["threshold"] == threshold) &
        (d["mut_rate"].fillna(0) == mut_rate)
    )
    d = d[sel].copy()
    if d.empty:
        return pd.DataFrame(columns=["species","species_pretty","tool_pretty","precision","recall","f1"])

    if {"tp","fp","fn"}.issubset(d.columns):
        d = _compute_prec_rec_f1(d)
    else:
        d = _ensure_prf_metrics(d)
    out = (d.groupby(["species","species_pretty","tool_pretty"], as_index=False)
             .agg(precision=("precision","mean"),
                  recall=("recall","mean"),
                  f1=("f1","mean")))
    return out

def geanno_rt_from_folder(
    csv_dir: Path,
    window: int | None = None,
    step: int | None = None,
    threshold: float | None = None,
) -> pd.DataFrame:
    """
    Per-(species, tool_pretty) RAM/time table from raw folder.
    Returns columns: species, species_pretty, tool_pretty, ram_kb/time_sec etc.
    """
    d = _load_geanno_raw_folder(csv_dir)
    if window is not None:
        d = d[pd.to_numeric(d.get("window"), errors="coerce") == window]
    if step is not None:
        d = d[pd.to_numeric(d.get("step"), errors="coerce") == step]
    if threshold is not None:
        d = d[pd.to_numeric(d.get("threshold"), errors="coerce") == threshold]
    return d




def _bench_abinitio_slice_for_model(df: pd.DataFrame, model: str) -> pd.DataFrame:
    d = df.copy()
    d["species_pretty"] = _species_to_pretty(d["species"])
    d = d[d["mut_rate"] == 0.0].copy()
    d["hint_l"] = _normalise_hint_column(d)

    m_aug_ab = _is_abinitio_aug(d)
    aug = d[m_aug_ab].copy()
    aug["model_used"] = np.where(aug["species"] == "oryza_sativa", "rice", "arabidopsis")
    aug = aug[aug["model_used"] == model]

    snap = d[d["tool"].astype(str).str.lower().eq("snap")].copy()
    snap["train_species_norm"] = snap.get("train_species", "").astype(str).str.lower().str.strip()
    ok = {"arabidopsis", "arabidopsis_thaliana", "a_thaliana"} if model == "arabidopsis" else {"rice", "oryza_sativa", "o_sativa"}
    snap = snap[snap["train_species_norm"].isin(ok)]

    def _keep_cols(x: pd.DataFrame, name: str) -> pd.DataFrame:
        cols = ["species", "species_pretty", "precision", "recall", "f1"]
        y = x[cols].copy()
        y["tool_pretty"] = name
        return y

    aug_lbl  = f"AUGUSTUS (ab initio, {'A. thaliana' if model=='arabidopsis' else 'O. sativa'} model)"
    snap_lbl = f"SNAP ({'A. thaliana' if model=='arabidopsis' else 'O. sativa'})"
    return _concat_nonempty([_keep_cols(aug, aug_lbl), _keep_cols(snap, snap_lbl)],
                            cols=["species","species_pretty","precision","recall","f1","tool_pretty"])

def _geanno_slice_for_models(geanno_df: pd.DataFrame, model_keys: List[str], labels: List[str]) -> pd.DataFrame:
    rows = []
    for key, lab in zip(model_keys, labels):
        sub = geanno_df[geanno_df["tool_pretty"].astype(str).str.contains(key, case=False, regex=False)].copy()
        if sub.empty:
            continue
        sub = sub[["species", "species_pretty", "precision", "recall", "f1"]]
        sub["tool_pretty"] = lab
        rows.append(sub)
    return _concat_nonempty(rows, cols=["species","species_pretty","precision","recall","f1","tool_pretty"])

def _cleveland_triple(df_plot: pd.DataFrame, title_prefix: str, out_png: Path, dpi: int = 300) -> Path:
    group_cols = ["species", "species_pretty", "tool_pretty"]
    metric_cols = ["precision", "recall", "f1"]

    if df_plot.duplicated(group_cols).any():
        agg = (df_plot.groupby(group_cols, as_index=False).agg({m: ["mean", "std"] for m in metric_cols}))
        agg.columns = ["_".join(col).rstrip("_") if isinstance(col, tuple) else col for col in agg.columns]
    else:
        agg = df_plot.copy()
        for m in metric_cols:
            if f"{m}_std" not in agg.columns: agg[f"{m}_std"] = 0.0
            if f"{m}_mean" not in agg.columns and m in agg.columns:
                agg[f"{m}_mean"] = pd.to_numeric(agg[m], errors="coerce")

    for m in metric_cols:
        if m not in agg.columns and f"{m}_mean" in agg.columns: agg[m] = agg[f"{m}_mean"]
        if f"{m}_std" not in agg.columns: agg[f"{m}_std"] = 0.0

    preferred_species = ["A. thaliana", "G. raimondii", "M. esculenta", "O. sativa"]
    species_present = [s for s in preferred_species if s in set(agg["species_pretty"])]
    if not species_present:
        species_present = list(agg["species_pretty"].drop_duplicates())

    tools = list(agg["tool_pretty"].drop_duplicates())
    if not tools:
        raise ValueError("No tools found in df_plot['tool_pretty'].")

    tool_color = _palette_for_tools(tools)
    tool_ls, tool_lw = _linestyle_for_tools(tools)
    marker_size = 6

    base_x = {s: i for i, s in enumerate(species_present)}
    n_tools = len(tools)
    width = 0.16 if n_tools >= 4 else 0.18
    offsets = {t: (j - (n_tools - 1) / 2.0) * width for j, t in enumerate(tools)}

    panels = [("precision", "Precision"), ("recall", "Recall"), ("f1", "F1-score")]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.8), sharey=True)

    for ax, (mkey, mtitle) in zip(axes, panels):
        mean_col = mkey if mkey in agg.columns else f"{mkey}_mean"
        std_col  = f"{mkey}_std"

        for t in tools:
            xs, ys = [], []
            for s in species_present:
                rows = agg[(agg["species_pretty"] == s) & (agg["tool_pretty"] == t)]
                if not rows.empty:
                    xs.append(base_x[s] + offsets[t])
                    ys.append(float(rows[mean_col].iloc[0]))
            if xs:
                ax.plot(xs, ys, linestyle=tool_ls[t], linewidth=tool_lw[t], alpha=0.9, zorder=1, color=tool_color[t])

        for t in tools:
            c = tool_color[t]
            lw = tool_lw[t]
            for s in species_present:
                rows = agg[(agg["species_pretty"] == s) & (agg["tool_pretty"] == t)]
                if rows.empty: continue
                x = base_x[s] + offsets[t]
                y = float(rows[mean_col].iloc[0])
                ysd = float(rows[std_col].iloc[0])
                ax.errorbar(x, y, yerr=(ysd if ysd > 0 else None),
                            fmt="o", markersize=marker_size,
                            linewidth=max(lw * 0.8, 1.0), capsize=2,
                            color=c, ecolor=c, markerfacecolor=c, markeredgecolor=c, zorder=3)

        ax.set_title(mtitle, fontsize=16)
        ax.set_ylim(0, 1)
        ax.set_xticks([base_x[s] for s in species_present])
        ax.set_xticklabels(species_present, rotation=15, ha="right", fontsize=13)
        ax.grid(axis="y", linestyle=":", alpha=0.5)
        ax.set_ylabel(mtitle if ax is axes[0] else "")

    fig.tight_layout(rect=[0, 0.15, 1, 0.92])
    handles = [Line2D([0], [0], marker="o", linestyle=tool_ls[t], linewidth=tool_lw[t],
                      markersize=marker_size, label=str(t), color=tool_color[t]) for t in tools]
    fig.legend(handles, [h.get_label() for h in handles], loc="lower center", bbox_to_anchor=(0.5, 0.03),
               ncol=len(tools), frameon=False, prop={"size": 13},
               handlelength=2.0, handletextpad=0.6, columnspacing=1.2, borderpad=0.3, labelspacing=0.6)

    fig.suptitle(title_prefix, y=0.99, fontsize=16)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return out_png

def _subset_geanno_mesculenta_any(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keep only the GeAnno M. esculenta PCA line, whether identified by raw key or pretty name.
    """
    d = df.copy()
    if "tool" in d.columns:
        m_raw = d["tool"].astype(str).str.contains("m_esculenta_model_PCA", case=False, regex=False)
    else:
        m_raw = pd.Series(False, index=d.index)
    if "tool_pretty" in d.columns:
        m_pretty = d["tool_pretty"].astype(str).str.contains("M. esculenta", case=False, regex=False)
    else:
        m_pretty = pd.Series(False, index=d.index)
    mask = m_raw | m_pretty
    return d[mask] if mask.any() else d




def plot_geanno_vs_abinitio_for_model(df_bench: pd.DataFrame, geanno_folder: Path, model: str, out_dir: Path) -> Tuple[Path, Path]:
    """
    model is {"arabidopsis", "rice"}.
    Compare GeAnno (±PCA) vs SNAP (trained on that species) + AUGUSTUS ab initio (with that species model) at 0% mut.
    """
    ge_raw = load_geanno(geanno_folder)
    ge = geanno_fixedpoint_from_df(ge_raw)  

    if model == "arabidopsis":
        ge_slice = _geanno_slice_for_models(ge,
            model_keys=["A. thaliana model", "A. thaliana model (PCA)"],
            labels    =["GeAnno (A. thaliana)", "GeAnno (A. thaliana, PCA)"])
    else:
        ge_slice = _geanno_slice_for_models(ge,
            model_keys=["O. sativa model", "O. sativa model (PCA)"],
            labels    =["GeAnno (O. sativa)", "GeAnno (O. sativa, PCA)"])

    ab = _bench_abinitio_slice_for_model(df_bench, model=model)
    comb = _concat_nonempty([ge_slice, ab])
    comb = (comb.groupby(["species","species_pretty","tool_pretty"], as_index=False)[["precision","recall","f1"]].mean())

    out_dir.mkdir(parents=True, exist_ok=True)
    title_prefix = ("A. thaliana" if model == "arabidopsis" else "O. sativa") + "-trained models comparison"
    fig_main = _cleveland_triple(comb, title_prefix=title_prefix,
                                 out_png=out_dir / f"geanno_vs_abinitio_{'thaliana' if model=='arabidopsis' else 'osativa'}_triple.png")

    fig_gm = _cleveland_triple(comb, title_prefix="GeneMark variants comparison",
                               out_png=out_dir / "geanno_vs_genemark_triple.png")
    return fig_main, fig_gm

def plot_geanno_vs_genemark(df_bench: pd.DataFrame, geanno_folder: Path, out_dir: Path) -> Path:
    ge_raw = load_geanno(geanno_folder)
    ge = geanno_fixedpoint_from_df(ge_raw)
    ge_slice = _geanno_slice_for_models(ge,
        model_keys=["GeneMark model", "GeneMark model (PCA)"],
        labels    =["GeAnno (GeneMark)", "GeAnno (GeneMark, PCA)"])

    d = df_bench.copy()
    d["species_pretty"] = _species_to_pretty(d["species"])
    gmes = d[(d["tool"].astype(str).str.lower() == "genemarkes") & (d["mut_rate"] == 0.0)][
        ["species","species_pretty","precision","recall","f1"]].copy()
    gmes["tool_pretty"] = "GeneMark-ES"

    comb = _concat_nonempty([ge_slice, gmes])
    comb = (comb.groupby(["species","species_pretty","tool_pretty"], as_index=False)[["precision","recall","f1"]].mean())

    out_dir.mkdir(parents=True, exist_ok=True)
    return _cleveland_triple(comb, title_prefix="GeAnno (GeneMark variants) vs GeneMark-ES",
                             out_png=out_dir / "geanno_vs_genemark_triple.png")

def plot_geanno_vs_tools_mut_rate(df_bench: pd.DataFrame, df_geanno: pd.DataFrame, out_dir: Path, dpi: int = 300) -> Tuple[Path, pd.DataFrame]:
    """
    Macro-averaged Precision/Recall/F1 vs mutation rate for:
      - Ab initio (AUG ab initio, GeneMark-ES, SNAP per training species)
      - Evidence-based (AUG hints, GeneMark-EP+, GeneMark-ETP, GeMoMa)
      - GeAnno (M. esculenta PCA) with fixed config.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    d = df_bench.copy()
    d["tool_l"] = d["tool"].astype(str).str.lower().str.strip()
    d["hint_l"] = _normalise_hint_column(d)

    g = _ensure_prf_metrics(df_geanno.copy())
    if "mut_rate" not in g.columns:
        raise RuntimeError("GeAnno dataframe must contain 'mut_rate' for mutation-rate plotting.")

    g = _filter_geanno_fixed_config(g)
    g = _subset_geanno_mesculenta_any(g)

    need = {"species","mut_rate","precision","recall","f1"}
    if not need.issubset(g.columns):
        raise RuntimeError(f"GeAnno dataframe missing columns: {need - set(g.columns)}")

    geanno_overall = (g.groupby(["mut_rate"], as_index=False)[["precision","recall","f1"]].mean()
                        .assign(tool_pretty="GeAnno (M. esculenta, PCA)", setting="GeAnno"))

    is_ab = (_is_abinitio_aug(d) | d["tool_l"].eq("genemarkes") | d["tool_l"].eq("snap"))
    ab_df = d[is_ab].copy()
    ab_df["tool_pretty"] = np.where(
        ab_df["tool_l"].eq("augustus"),   "AUGUSTUS (ab initio)",
        np.where(ab_df["tool_l"].eq("genemarkes"), "GeneMark-ES",
                 np.where(ab_df["tool_l"].eq("snap"), "SNAP (" + ab_df.get("train_species","Unknown").map(_map_snap_model) + ")",
                          ab_df["tool"]))
    )
    overall_ab = (ab_df.groupby(["tool_pretty","mut_rate"], as_index=False)[["precision","recall","f1"]].mean()
                        .assign(setting="Ab initio"))

    allowed_hints = {"genus","order","far"}
    is_ev = (d["tool_l"].isin({"genemarkep","genemarketp","gemoma"})
             | (d["tool_l"].eq("augustus") & d["hint_l"].notna() & ~d["hint_l"].eq("abinitio")))
    ev_df = d[is_ev & d["hint_l"].isin(allowed_hints)].copy()
    if not ev_df.empty:
        ev_df["tool_pretty"] = ev_df["tool_l"].map({
            "genemarkep": "GeneMark-EP+",
            "genemarketp": "GeneMark-ETP",
            "gemoma": "GeMoMa",
            "augustus": "AUGUSTUS (hints)",
        })
        per_hint = ev_df.groupby(["tool_pretty","mut_rate","hint_l"], as_index=False)[["precision","recall","f1"]].mean()
        overall_ev = per_hint.groupby(["tool_pretty","mut_rate"], as_index=False)[["precision","recall","f1"]].mean().assign(setting="Evidence-based (macro)")
    else:
        overall_ev = pd.DataFrame(columns=["tool_pretty","mut_rate","precision","recall","f1","setting"])

    overall = pd.concat([overall_ab, overall_ev, geanno_overall], ignore_index=True)

    tool_order = [
        "GeneMark-ES", "SNAP (A. thaliana)", "SNAP (O. sativa)", "AUGUSTUS (ab initio)",
        "GeMoMa", "GeneMark-EP+", "GeneMark-ETP", "AUGUSTUS (hints)",
        "GeAnno (M. esculenta, PCA)",
    ]
    tool_order = [t for t in tool_order if t in set(overall["tool_pretty"])]
    style_order = ["Ab initio", "Evidence-based (macro)", "GeAnno"]

    save_table_csv(overall, out_dir / "csv/mutation_curves_ab_vs_evidence_plus_geanno.csv")

    metrics = [("precision","Precision"), ("recall","Recall"), ("f1","F1-score")]
    palette = dict(zip(tool_order, sns.color_palette(n_colors=len(tool_order))))
    dashes_map = {"Ab initio": "", "Evidence-based (macro)": (3, 2), "GeAnno": ""}

    fig, axes = plt.subplots(1, 3, figsize=(15, 6), sharey=True)
    axes = axes.flatten()

    for i, (metric, mname) in enumerate(metrics):
        sns.lineplot(
            data=overall, x="mut_rate", y=metric,
            hue="tool_pretty", hue_order=tool_order, palette=palette,
            style="setting", style_order=style_order, dashes=dashes_map,
            marker="o", linewidth=1.8, ax=axes[i], legend=False
        )
        if "GeAnno (M. esculenta, PCA)" in overall["tool_pretty"].unique():
            ge_sub = overall[overall["tool_pretty"] == "GeAnno (M. esculenta, PCA)"]
            axes[i].plot(ge_sub["mut_rate"], ge_sub[metric], marker="o", linewidth=2.8,
                         color=palette["GeAnno (M. esculenta, PCA)"], linestyle="-", zorder=5)
        axes[i].set_ylim(0, 1)
        axes[i].set_title(mname, fontsize=13)
        axes[i].set_xlabel("Mutation rate", fontsize=12)
        axes[i].set_ylabel(mname if i == 0 else "", fontsize=12)
        axes[i].grid(axis="y", linestyle=":", alpha=0.6)

    tool_handles = [Line2D([0],[0], color=palette[t], marker='o', linestyle='-', label=t, markersize=6, linewidth=1.8) for t in tool_order]
    for h in tool_handles:
        if h.get_label() == "GeAnno (M. esculenta, PCA)":
            h.set_linewidth(2.8)

    fig.legend(tool_handles, [h.get_label() for h in tool_handles],
               loc="lower center", bbox_to_anchor=(0.5, 0.05), frameon=False, ncol=5, title=None, prop={'size': 12})
    fig.suptitle("Comparison between tools across different mutation rates\n", y=0.985, fontsize=16)

    fig.tight_layout(rect=[0.06, 0.15, 1, 1])
    fig_path = out_dir / "mutation_curves_ab_vs_evidence_plus_geanno.png"
    fig.savefig(fig_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return fig_path, overall

def plot_ram_time_all_tools_overall_dots_plus_geanno(df_bench: pd.DataFrame, df_geanno: pd.DataFrame, out_dir: Path, dpi: int = 300) -> Tuple[Path, pd.DataFrame]:
    """
    Overall RAM/Runtime Cleveland dots (macro-averaged per species) with:
      - Ab initio tools
      - Evidence-based tools
      - GeAnno fixed config (M. esculenta PCA)
    """
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

    d = df_bench.copy()
    d["species_size_kb"] = d["species"].map(SPECIES_SIZE)
    d = d.dropna(subset=["species_size_kb"]).copy()

    if "ram_mb" not in d.columns and "ram_kb" in d.columns:
        d = d.rename(columns={"ram_kb": "ram_mb"})
    if "time_sec" not in d.columns and "time" in d.columns:
        d = d.rename(columns={"time": "time_sec"})

    d["ram_per_kb"]  = d["ram_mb"]  / d["species_size_kb"]
    d["time_per_kb"] = d["time_sec"] / d["species_size_kb"]

    d_ab = _abinitio_subset_local(d)
    by_sp_ab = (d_ab.groupby(["species","tool_pretty"], as_index=False)[["ram_mb","time_sec","ram_per_kb","time_per_kb"]].mean())
    by_sp_ab["group"] = "Ab initio"

    d_ev = _evidence_subset_local(d)
    if d_ev.empty:
        warnings.warn("No evidence-based rows; plotting Ab initio + GeAnno only.")
        by_sp_ev = pd.DataFrame(columns=by_sp_ab.columns)
    else:
        within_hint = (d_ev.groupby(["species","tool_pretty","hint_l"], as_index=False)[["ram_mb","time_sec","ram_per_kb","time_per_kb"]].mean())
        by_sp_ev = (within_hint.groupby(["species","tool_pretty"], as_index=False)[["ram_mb","time_sec","ram_per_kb","time_per_kb"]].mean())
        by_sp_ev["group"] = "Evidence-based"

    g = df_geanno.copy()
    g = _filter_geanno_fixed_config(g)

    if "ram_mb" not in g.columns and "ram_kb" in g.columns:
        g = g.rename(columns={"ram_kb": "ram_mb"})
    if "time_sec" not in g.columns and "time" in g.columns:
        g = g.rename(columns={"time": "time_sec"})

    g["species_size_kb"] = g["species"].map(SPECIES_SIZE)
    g = g.dropna(subset=["species_size_kb"]).copy()
    g["ram_per_kb"]  = g["ram_mb"]  / g["species_size_kb"]
    g["time_per_kb"] = g["time_sec"] / g["species_size_kb"]

    g = _subset_geanno_mesculenta_any(g)

    if g.empty:
        warnings.warn("No GeAnno rows for M. esculenta (PCA) with the fixed config.")
        by_sp_ge = pd.DataFrame(columns=by_sp_ab.columns)
    else:
        by_sp_ge = (g.groupby(["species"], as_index=False)[["ram_mb","time_sec","ram_per_kb","time_per_kb"]].mean())
        by_sp_ge["tool_pretty"] = "GeAnno (M. esculenta, PCA)"
        by_sp_ge["group"] = "GeAnno"

    per_species = pd.concat([by_sp_ab, by_sp_ev, by_sp_ge], ignore_index=True)
    overall = (per_species.groupby(["tool_pretty","group"], as_index=False)[["ram_mb","time_sec","ram_per_kb","time_per_kb"]].mean())

    save_table_csv(overall, out_dir / "csv/all_tools_overall_ram_time_plus_geanno.csv")

    long = overall.melt(id_vars=["tool_pretty","group"],
                        value_vars=["ram_mb","time_sec","ram_per_kb","time_per_kb"],
                        var_name="measure", value_name="value")
    measure_label = {
        "ram_mb": "RAM (KB)",
        "time_sec": "Runtime (s)",
        "ram_per_kb": "RAM per genome size",
        "time_per_kb": "Runtime per genome size",
    }
    long["measure"] = long["measure"].map(measure_label)

    titles = {
        "RAM (KB)": "Overall RAM usage",
        "Runtime (s)": "Overall runtime",
        "RAM per genome size": "RAM usage normalized by genome size",
        "Runtime per genome size": "Runtime normalized by genome size"
    }
    xlabels = {
        "RAM (KB)": "RAM (KB)",
        "Runtime (s)": "Runtime (s)",
        "RAM per genome size": "RAM per genome size (KB per KB genome)",
        "Runtime per genome size": "Runtime per genome size (s per KB genome)"
    }

    hue_map = {"Ab initio": "#4C78A8", "Evidence-based": "#E45756", "GeAnno": "#2CA02C"}
    measures = ["RAM (KB)", "Runtime (s)", "RAM per genome size", "Runtime per genome size"]

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

    fig.suptitle("Overall RAM and Runtime Comparison Across Tools", y=0.98, fontsize=16)
    fig.tight_layout(rect=[0.05, 0.08, 1, 0.97])
    fig_path = out_dir / "all_tools_overall_cleveland_plus_geanno.png"
    fig.savefig(fig_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return fig_path, overall

def plot_auc_heatmap_stack_geanno_mesc_vs_aug_abinitio(geanno_auc_csv: Path, bench_auc_dir: Path, out_dir: Path, dpi: int = 300) -> Optional[Path]:
    """
    Two stacked heatmaps: columns=species, rows=tools (GeAnno M. esculenta PCA vs AUGUSTUS ab initio)
    Top=AUC_ROC, Bottom=AU_PRC. Filters to 0% mutation and fixed GeAnno config.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    ge = pd.read_csv(geanno_auc_csv)
    col_lower = {c.lower(): c for c in ge.columns}

    model_col = col_lower.get("model", col_lower.get("tool"))
    mr_col    = col_lower.get("mutation_rate", col_lower.get("mut_rate"))
    win_col   = col_lower.get("window", col_lower.get("win"))
    step_col  = col_lower.get("step", col_lower.get("stride"))
    thr_col   = col_lower.get("threshold", col_lower.get("thr"))
    aucroc_c  = col_lower.get("auc_roc")
    aucprc_c  = col_lower.get("auc_prc")

    if model_col is None or mr_col is None or aucroc_c is None or aucprc_c is None:
        warnings.warn("GeAnno AUC CSV missing required columns.")
        ge = ge.iloc[0:0]

    if not ge.empty:
        ge = ge[
            (ge[model_col] == "m_esculenta_model_PCA") &
            (pd.to_numeric(ge[mr_col], errors="coerce") == 0) &
            ((win_col  is None) | (pd.to_numeric(ge[win_col],  errors="coerce") == GEANNO_WIN)) &
            ((step_col is None) | (pd.to_numeric(ge[step_col], errors="coerce") == GEANNO_STEP)) &
            ((thr_col  is None) | (pd.to_numeric(ge[thr_col],  errors="coerce") == GEANNO_THR))
        ].copy()

    ge["tool_pretty"] = "GeAnno (M. esculenta, PCA)"
    ge = ge.rename(columns={aucroc_c: "AUC_ROC", aucprc_c: "AUC_PRC"})
    ge_part = ge[["species", "tool_pretty", "AUC_ROC", "AUC_PRC"]].copy()

    rows = []
    for fp in bench_auc_dir.glob("*_auc.csv"):
        parts = fp.stem.split("_")
        if not parts or parts[0].lower() != "augustus": continue
        if "abinitio" not in (p.lower() for p in parts): continue
        if len(parts) < 4: continue

        species_guess = "_".join(parts[1:3])

        mut_rate = None
        for tok in parts[1:]:
            t = tok.lower()
            if t == "original":
                mut_rate = 0.0; break
            try:
                mut_rate = float(tok); break
            except ValueError:
                continue
        if mut_rate is None or mut_rate != 0.0:
            continue

        df_auc = pd.read_csv(fp)
        kmap = {c.lower(): c for c in df_auc.columns}
        roc_c = kmap.get("auc_roc"); prc_c = kmap.get("auc_prc")
        if roc_c is None or prc_c is None:
            warnings.warn(f"Skipping {fp.name}: missing AUC_ROC/AUC_PRC columns."); continue

        rows.append({
            "species": species_guess,
            "tool_pretty": "AUGUSTUS (ab initio)",
            "AUC_ROC": float(pd.to_numeric(df_auc[roc_c], errors="coerce").mean()),
            "AUC_PRC": float(pd.to_numeric(df_auc[prc_c], errors="coerce").mean()),
        })

    aug_part = pd.DataFrame(rows)
    combined = pd.concat([ge_part, aug_part], ignore_index=True)

    if combined.empty:
        warnings.warn("No AUC data to plot.")
        return None

    combined["species_pretty"] = _species_to_pretty(combined["species"])
    tool_order = ["GeAnno (M. esculenta, PCA)", "AUGUSTUS (ab initio)"]
    species_order = [s for s in ["A. thaliana", "G. raimondii", "M. esculenta", "O. sativa"]
                     if s in set(combined["species_pretty"])]

    save_table_csv(combined[["species", "species_pretty", "tool_pretty", "AUC_ROC", "AUC_PRC"]],
                   out_dir / "csv/auc_abinitio_per_species_summary.csv")

    piv_roc = (combined.pivot_table(index="tool_pretty", columns="species_pretty", values="AUC_ROC", aggfunc="mean")
                        .reindex(index=tool_order, columns=species_order))
    piv_prc = (combined.pivot_table(index="tool_pretty", columns="species_pretty", values="AUC_PRC", aggfunc="mean")
                        .reindex(index=tool_order, columns=species_order))

    fig, axes = plt.subplots(2, 1, figsize=(1.8 + 1.6*max(3, len(species_order)), 6.0))
    ax1, ax2 = axes
    sns.heatmap(piv_roc, ax=ax1, annot=True, fmt=".3f", cmap="viridis", cbar_kws={"shrink": 0.9})
    ax1.set_xlabel(""); ax1.set_ylabel(""); ax1.set_title("AUC-ROC")
    sns.heatmap(piv_prc, ax=ax2, annot=True, fmt=".3f", cmap="viridis", cbar_kws={"shrink": 0.9})
    ax2.set_xlabel(""); ax2.set_ylabel(""); ax2.set_title("AU-PRC")

    fig.suptitle("GeAnno (M. esculenta, PCA) and AUGUSTUS (ab initio) AUC comparison", y=0.98, fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.96])

    out_png = out_dir / "auc_abinitio_geanno_mesc_vs_aug_stacked.png"
    fig.savefig(out_png, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return out_png
