import pandas as pd
import seaborn as sns

from matplotlib import pyplot as plt
from pathlib import Path
from typing import Dict, Iterable, List, Tuple
from matplotlib.lines import Line2D

from modules.load_save import load_geanno
from modules.common import GEANNO_WIN, GEANNO_STEP, GEANNO_THR,\
                          _ensure_numeric, _compute_prec_rec_f1, _ensure_prf_metrics, \
                          _species_to_pretty, _geanno_slice_for_models, _bench_abinitio_slice_for_model, \
                          _concat_nonempty


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
        ax.set_ylabel("Value" if ax is axes[0] else "")

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

def _geanno_fixedpoint_from_df(df: pd.DataFrame,
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

def plot_geanno_vs_genemark(df_bench: pd.DataFrame, geanno_folder: Path, out_dir: Path) -> Path:
    """ Compare GeAnno (GeneMark models and PCA) vs GeneMark-ES at 0% mut. """

    ge_raw = load_geanno(geanno_folder)
    ge = _geanno_fixedpoint_from_df(ge_raw)
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
    return _cleveland_triple(comb, title_prefix="GeAnno (GeneMark variants) and GeneMark-ES comparison",
                             out_png=out_dir / "geanno_vs_genemark_triple.png")

def plot_geanno_vs_abinitio_for_model(df_bench: pd.DataFrame, geanno_folder: Path, model: str, out_dir: Path) -> Tuple[Path, Path]:
    """ Compare GeAnno (n/sPCA) vs SNAP (trained on that species) + AUGUSTUS ab initio (with that species model) at 0% mut. """
    ge_raw = load_geanno(geanno_folder)
    ge = _geanno_fixedpoint_from_df(ge_raw)  

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

    return fig_main