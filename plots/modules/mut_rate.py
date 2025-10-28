import pandas as pd
import numpy as np
import seaborn as sns

from pathlib import Path
from typing import Optional, Tuple
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D

from modules.common import GEANNO_STEP, GEANNO_THR, GEANNO_WIN, _compute_prec_rec_f1, \
                        _ensure_numeric, _ensure_prf_metrics, _filter_geanno_fixed_config, \
                        _is_abinitio_aug, _map_snap_model, _normalise_hint_column, _species_to_pretty, \
                        _subset_geanno_mesculenta_any

from modules.load_save import save_table_csv

def plot_geanno_vs_tools_mut_rate_per_species(
    df_bench: pd.DataFrame,
    df_geanno: pd.DataFrame,
    out_dir: Path,
    dpi: int = 300
):
    out_dir.mkdir(parents=True, exist_ok=True)

    d = df_bench.copy()
    d["tool_l"] = d["tool"].astype(str).str.lower().str.strip()
    d["hint_l"] = _normalise_hint_column(d)
    d["species_pretty"] = _species_to_pretty(d["species"])

    g = _ensure_prf_metrics(df_geanno.copy())
    if "mut_rate" not in g.columns:
        raise RuntimeError("GeAnno dataframe must contain 'mut_rate' for mutation-rate plotting.")
    g = _filter_geanno_fixed_config(g)
    g = _subset_geanno_mesculenta_any(g)

    need = {"species","mut_rate","precision","recall","f1"}
    if not need.issubset(g.columns):
        raise RuntimeError(f"GeAnno dataframe missing columns: {need - set(g.columns)}")

    g["species_pretty"] = _species_to_pretty(g["species"])

    geanno_overall = (
        g.groupby(["species","species_pretty","mut_rate"], as_index=False)[["precision","recall","f1"]]
        .mean()
        .assign(tool_pretty="GeAnno (M. esculenta, PCA)", setting="GeAnno")
    )

    is_ab = (_is_abinitio_aug(d) | d["tool_l"].eq("genemarkes") | d["tool_l"].eq("snap"))
    ab_df = d[is_ab].copy()
    ab_df["tool_pretty"] = np.where(
        ab_df["tool_l"].eq("augustus"), "AUGUSTUS (ab initio)",
        np.where(ab_df["tool_l"].eq("genemarkes"), "GeneMark-ES",
                 np.where(ab_df["tool_l"].eq("snap"),
                          "SNAP (" + ab_df.get("train_species","Unknown").map(_map_snap_model) + ")",
                          ab_df["tool"]))
    )
    overall_ab = (
        ab_df.groupby(["species","species_pretty","tool_pretty","mut_rate"], as_index=False)
             [["precision","recall","f1"]].mean()
             .assign(setting="Ab initio")
    )

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
        per_hint = (
            ev_df.groupby(["species","species_pretty","tool_pretty","mut_rate","hint_l"], as_index=False)
                 [["precision","recall","f1"]].mean()
        )
        overall_ev = (
            per_hint.groupby(["species","species_pretty","tool_pretty","mut_rate"], as_index=False)
                    [["precision","recall","f1"]].mean()
                    .assign(setting="Evidence-based (macro)")
        )
    else:
        overall_ev = pd.DataFrame(columns=["species","species_pretty","tool_pretty","mut_rate",
                                           "precision","recall","f1","setting"])

    overall = pd.concat([overall_ab, overall_ev, geanno_overall], ignore_index=True)

    tool_order_master = [
        "GeneMark-ES","SNAP (A. thaliana)","SNAP (O. sativa)","AUGUSTUS (ab initio)",
        "GeMoMa","GeneMark-EP+","GeneMark-ETP","AUGUSTUS (hints)",
        "GeAnno (M. esculenta, PCA)",
    ]
    style_order = ["Ab initio","Evidence-based (macro)","GeAnno"]

    present_tools = [t for t in tool_order_master if t in set(overall["tool_pretty"])]
    palette = dict(zip(present_tools, sns.color_palette(n_colors=len(present_tools))))
    dashes_map = {"Ab initio": "", "Evidence-based (macro)": (3, 2), "GeAnno": ""}

    species_list = [s for s in ["A. thaliana","O. sativa","G. raimondii","M. esculenta"]
                    if s in set(overall["species_pretty"])]

    fig_paths = {}
    metrics = [("precision","Precision"),("recall","Recall"),("f1","F1-score")]

    for sp_pretty in species_list:
        sp_df = overall[overall["species_pretty"] == sp_pretty].copy()
        tool_order = [t for t in tool_order_master if t in set(sp_df["tool_pretty"])]

        fig, axes = plt.subplots(1, 3, figsize=(15, 6), sharey=True)
        axes = axes.flatten()
        for i, (metric, mname) in enumerate(metrics):
            sns.lineplot(
                data=sp_df, x="mut_rate", y=metric,
                hue="tool_pretty", hue_order=tool_order, palette=palette,
                style="setting", style_order=style_order, dashes=dashes_map,
                marker="o", linewidth=1.8, ax=axes[i], legend=False
            )
            if "GeAnno (M. esculenta, PCA)" in sp_df["tool_pretty"].unique():
                ge_sub = sp_df[sp_df["tool_pretty"] == "GeAnno (M. esculenta, PCA)"]
                axes[i].plot(ge_sub["mut_rate"], ge_sub[metric], marker="o", linewidth=2.8,
                             color=palette["GeAnno (M. esculenta, PCA)"], linestyle="-", zorder=5)
            axes[i].set_ylim(0, 1)
            axes[i].set_title(mname, fontsize=13)
            axes[i].set_xlabel("Mutation rate", fontsize=12)
            axes[i].set_ylabel("Value" if i == 0 else "", fontsize=12)
            axes[i].grid(axis="y", linestyle=":", alpha=0.6)

        handles = [Line2D([0],[0], color=palette[t], marker='o', linestyle='-', label=t, markersize=6, linewidth=1.8)
                   for t in tool_order]
        for h in handles:
            if h.get_label() == "GeAnno (M. esculenta, PCA)":
                h.set_linewidth(2.8)

        fig.legend(handles, [h.get_label() for h in handles],
                   loc="lower center", bbox_to_anchor=(0.5, 0.05), frameon=False,
                   ncol=min(5, len(handles)), title=None, prop={'size': 12})

        fig.suptitle(f"Comparison between tools across different mutation rates — {sp_pretty}\n",
                     y=0.985, fontsize=16)
        fig.tight_layout(rect=[0.06, 0.15, 1, 1])

        safe_sp = sp_pretty.replace(" ", "_").replace(".", "")
        fig_path = out_dir / f"mutation_curves_ab_vs_evidence_plus_geanno_{safe_sp}.png"
        fig.savefig(fig_path, dpi=dpi, bbox_inches="tight")
        plt.close(fig)
        fig_paths[sp_pretty] = fig_path

    return fig_paths, overall

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
        axes[i].set_ylabel("Value" if i == 0 else "", fontsize=12)
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

def export_fixedpoint_species_model(
    d: pd.DataFrame, out_dir: Path,
    window: int = GEANNO_WIN, step: int = GEANNO_STEP, threshold: float = GEANNO_THR, mut_rate: float = 0.0
) -> None:
    """Per (species, model) metrics at a fixed operating point."""
    dd = _ensure_numeric(d, ["window","step","threshold","tp","fp","fn","mut_rate"])
    df = dd[(dd["window"] == window) & (dd["step"] == step) &
            (dd["threshold"] == threshold) & (dd["mut_rate"].fillna(0) == mut_rate)].copy()
    df = _compute_prec_rec_f1(df)

    out = (df.groupby(["species","species_pretty","tool_pretty"], as_index=False)
             .agg(precision=("precision","mean"),
                  recall=("recall","mean"),
                  f1=("f1","mean"))
           .sort_values(["species_pretty","tool_pretty"]))
    out[["precision","recall","f1"]] = out[["precision","recall","f1"]].round(4)
    save_table_csv(out, out_dir / f"csv/geanno_metrics_by_tool_mutrate_win{window}_step{step}_thr{threshold}.csv")

def export_tool_mutation_drop_csv(
    df_bench: pd.DataFrame,
    df_geanno: pd.DataFrame,
    out_dir: Path,
    decimals: int = 2
) -> Tuple[Path, pd.DataFrame]:
    """
    

    Build a table of metric drops between 0% mutation and 7% mutation (or 4% if 7% is not available)
    for each tool:
      - Ab initio: AUGUSTUS (ab initio), GeneMark-ES, SNAP (A. thaliana), SNAP (O. sativa)
      - Evidence-based (macro across hints: genus/order/far): GeMoMa, GeneMark-EP+, GeneMark-ETP, AUGUSTUS (hints)
      - GeAnno: M. esculenta, PCA @ fixed config

    Output CSV columns:
      tool_type, tool_pretty, mut_rate_ref, mut_rate_target, precision_diff, recall_diff, f1_diff
    where diffs are (score at 0.0) - (score at target), in percentage points.
    """
    out_dir.mkdir(parents=True, exist_ok=True)


    d = df_bench.copy()
    d["tool_l"] = d["tool"].astype(str).str.lower().str.strip()
    d["hint_l"] = _normalise_hint_column(d)
    d = _ensure_prf_metrics(d)
    d["species_pretty"] = _species_to_pretty(d["species"])


    is_ab = (_is_abinitio_aug(d) | d["tool_l"].eq("genemarkes") | d["tool_l"].eq("snap"))
    ab = d[is_ab].copy()
    def _tool_pretty_row(r) -> str:
        tl = str(r["tool"]).lower()
        if tl == "augustus":   return "AUGUSTUS (ab initio)"
        if tl == "genemarkes": return "GeneMark-ES"
        if tl == "snap":       return f"SNAP ({_map_snap_model(r.get('train_species','Unknown'))})"
        return r["tool"]
    ab["tool_pretty"] = [_tool_pretty_row(r) for _, r in ab.iterrows()]

    ab_avg = (ab.groupby(["tool_pretty","mut_rate"], as_index=False)[["precision","recall","f1"]].mean()
                .assign(tool_type="Ab initio"))


    allowed_hints = {"genus","order","far"}
    is_ev = (d["tool_l"].isin({"genemarkep","genemarketp","gemoma"})
             | (d["tool_l"].eq("augustus") & d["hint_l"].notna() & ~d["hint_l"].eq("abinitio")))
    ev = d[is_ev & d["hint_l"].isin(allowed_hints)].copy()

    ev["tool_pretty"] = ev["tool_l"].map({
        "genemarkep":  "GeneMark-EP+",
        "genemarketp": "GeneMark-ETP",
        "gemoma":      "GeMoMa",
        "augustus":    "AUGUSTUS (hints)",
    }).fillna(ev["tool"])

    ev_sp_hint = (ev.groupby(["species","tool_pretty","hint_l","mut_rate"], as_index=False)
                    [["precision","recall","f1"]].mean())
    ev_species_mean = (ev_sp_hint.groupby(["tool_pretty","species","mut_rate"], as_index=False)
                       [["precision","recall","f1"]].mean())
    ev_avg = (ev_species_mean.groupby(["tool_pretty","mut_rate"], as_index=False)
                         [["precision","recall","f1"]].mean()
                         .assign(tool_type="Evidence-based"))

    g = _ensure_prf_metrics(df_geanno.copy())
    g = _filter_geanno_fixed_config(g)
    g = _subset_geanno_mesculenta_any(g)
    if not g.empty:
        geanno_avg = (g.groupby(["mut_rate"], as_index=False)[["precision","recall","f1"]].mean()
                        .assign(tool_pretty="GeAnno (M. esculenta, PCA)", tool_type="GeAnno"))
    else:
        geanno_avg = pd.DataFrame(columns=["tool_pretty","mut_rate","precision","recall","f1","tool_type"])

    overall = pd.concat([ab_avg, ev_avg, geanno_avg], ignore_index=True)

    def _pick_target_rate(df_tool: pd.DataFrame) -> Optional[float]:
        rates = set(pd.to_numeric(df_tool["mut_rate"], errors="coerce").dropna())
        if 0.07 in rates: return 0.07
        if 0.04 in rates: return 0.04
        return None

    rows = []
    for (ttype, tname), sub in overall.groupby(["tool_type","tool_pretty"]):
        mr0 = 0.0
        mrt = _pick_target_rate(sub)
        if mrt is None:
            continue

        def _vals(mr, key):
            s = sub[pd.to_numeric(sub["mut_rate"], errors="coerce") == mr]
            return float(s[key].mean()) if not s.empty else np.nan

        p0, r0, f0 = _vals(mr0, "precision"), _vals(mr0, "recall"), _vals(mr0, "f1")
        pt, rt, ft = _vals(mrt, "precision"), _vals(mrt, "recall"), _vals(mrt, "f1")

        rows.append({
            "tool_type": ttype,
            "tool_pretty": tname,
            "mut_rate_ref": mr0,
            "mut_rate_target": mrt,

            "precision_diff": round((p0 - pt) * 100.0, decimals) if not np.isnan(p0) and not np.isnan(pt) else np.nan,
            "recall_diff":    round((r0 - rt) * 100.0, decimals) if not np.isnan(r0) and not np.isnan(rt) else np.nan,
            "f1_diff":        round((f0 - ft) * 100.0, decimals) if not np.isnan(f0) and not np.isnan(ft) else np.nan,
        })

    out = pd.DataFrame(rows)
    
    type_order = ["Ab initio", "Evidence-based", "GeAnno"]
    tool_order = [
        "AUGUSTUS (ab initio)", "SNAP (A. thaliana)", "SNAP (O. sativa)", "GeneMark-ES",
        "AUGUSTUS (hints)", "GeMoMa", "GeneMark-EP+", "GeneMark-ETP",
        "GeAnno (M. esculenta, PCA)"
    ]
    out["tool_type"] = pd.Categorical(out["tool_type"], categories=type_order, ordered=True)
    out["tool_pretty"] = pd.Categorical(out["tool_pretty"], categories=tool_order, ordered=True)
    out = out.sort_values(["tool_type","tool_pretty"]).reset_index(drop=True)

    csv_path = out_dir / "csv/tool_mutation_drop_0_vs_7pct_fallback4pct.csv"
    save_table_csv(out, csv_path)
    return csv_path, out

def export_tool_by_mutrate_avg_across_species(
    d: pd.DataFrame, out_dir: Path,
    window: int = GEANNO_WIN, step: int = GEANNO_STEP, threshold: float = GEANNO_THR):
    """ GeAnno's tools per mutation rate averaged across species, for window 1500, step 50 and threshold 0.8 """

    dd = _ensure_numeric(d, ["window","step","threshold","tp","fp","fn","mut_rate"])
    df = dd[(dd["window"] == window) & (dd["step"] == step) & (dd["threshold"] == threshold)].copy()
    df = df.dropna(subset=["tp","fp","fn","mut_rate","tool_pretty"])
    df = _compute_prec_rec_f1(df)

    out = (df.groupby(["tool_pretty","mut_rate"], as_index=False)
             .agg(precision=("precision","mean"),
                  recall=("recall","mean"),
                  f1=("f1","mean"))
           .sort_values(["tool_pretty","mut_rate"]))
    out[["precision","recall","f1"]] = out[["precision","recall","f1"]].round(4)
    save_table_csv(out, out_dir / f"csv/geanno_metrics_by_tool_mutrate_win{window}_step{step}_thr{threshold}.csv")