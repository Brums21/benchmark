import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from pathlib import Path
from typing import Tuple
from matplotlib.lines import Line2D


from modules.load_save import save_table_csv
from modules.common import _ensure_prf_metrics, _filter_geanno_fixed_config,\
                         _normalise_hint_column, _species_to_pretty, _subset_geanno_mesculenta_any


def plot_evidence_species_by_hints_plus_geanno(
    df_bench: pd.DataFrame,
    df_geanno: pd.DataFrame,
    out_dir: Path,
    dpi: int = 300
) -> Tuple[Path, pd.DataFrame]:
    """
    Three-panel line plot (Precision / Recall / F1-score).
    X = species; Lines = evidence-based tools; line dash = hint type (genus/order/far);
    plus an extra black line for GeAnno (M. esculenta, PCA) across species.

    Returns: (figure_path, aggregated_dataframe_used)
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    d = df_bench.copy()
    d["tool_l"] = d["tool"].astype(str).str.lower().str.strip()
    d["hint_l"] = _normalise_hint_column(d)
    d["species_pretty"] = _species_to_pretty(d["species"])

    allowed_hints = {"genus", "order", "far"}
    is_ev = (
        d["tool_l"].isin({"genemarkep", "genemarketp", "gemoma"}) |
        (d["tool_l"].eq("augustus") & d["hint_l"].notna() & ~d["hint_l"].eq("abinitio"))
    )
    ev = d[is_ev & d["hint_l"].isin(allowed_hints)].copy()
    if ev.empty:
        raise RuntimeError("No evidence-based rows with hints in {'genus','order','far'} found in df_bench.")

    ev["tool_pretty"] = ev["tool_l"].map({
        "genemarkep":  "GeneMark-EP+",
        "genemarketp": "GeneMark-ETP",
        "gemoma":      "GeMoMa",
        "augustus":    "AUGUSTUS (hints)",
    }).fillna(ev["tool"])

    ev_agg = (
        ev.groupby(["species", "species_pretty", "tool_pretty", "hint_l"], as_index=False)
          [["precision", "recall", "f1"]].mean()
    )

    g = _ensure_prf_metrics(df_geanno.copy())
    g = _filter_geanno_fixed_config(g)
    g = _subset_geanno_mesculenta_any(g)
    if g.empty:
        raise RuntimeError("No GeAnno rows for m_esculenta_model_PCA at the fixed config in df_geanno.")

    g["species_pretty"] = _species_to_pretty(g["species"])
    ge_agg = (
        g.groupby(["species", "species_pretty"], as_index=False)[["precision", "recall", "f1"]]
         .mean()
         .assign(tool_pretty="GeAnno (M. esculenta, PCA)")
    )

    preferred = ["A. thaliana", "O. sativa", "G. raimondii", "M. esculenta"]
    species_present = [s for s in preferred if s in set(ev_agg["species_pretty"])] or \
                      list(ev_agg["species_pretty"].drop_duplicates())

    ev_agg["species_pretty"] = pd.Categorical(ev_agg["species_pretty"], categories=species_present, ordered=True)
    ge_agg["species_pretty"] = pd.Categorical(ge_agg["species_pretty"], categories=species_present, ordered=True)

    tool_order = ["GeMoMa", "GeneMark-EP+", "GeneMark-ETP", "AUGUSTUS (hints)"]
    tool_order = [t for t in tool_order if t in set(ev_agg["tool_pretty"])]
    palette = dict(zip(tool_order, sns.color_palette(n_colors=len(tool_order))))

    hint_order = ["genus", "order", "far"]
    dashes_map = {
        "genus": (1, 0),
        "order": (4, 2),
        "far":   (2, 2),
    }

    save_table_csv(
        pd.concat([
            ev_agg.assign(setting="Evidence-based", hint=ev_agg["hint_l"]),
            ge_agg.assign(setting="GeAnno", hint=pd.NA, tool_pretty="GeAnno (M. esculenta, PCA)")
        ], ignore_index=True),
        out_dir / "csv/evidence_species_by_hints_plus_geanno.csv"
    )

    fig, axes = plt.subplots(1, 3, figsize=(14.5, 5.2), sharex=True, sharey=True)
    metrics = [("precision", "Precision"), ("recall", "Recall"), ("f1", "F1-score")]

    for ax, (mkey, mtitle) in zip(axes, metrics):
        for t in tool_order:
            for h in hint_order:
                sub = ev_agg[(ev_agg["tool_pretty"] == t) & (ev_agg["hint_l"] == h)]
                if sub.empty: 
                    continue
                sub = sub.sort_values("species_pretty")
                ax.plot(
                    sub["species_pretty"], sub[mkey],
                    marker="o", linewidth=1.9, color=palette[t],
                    linestyle="-", dashes=dashes_map[h], label=f"{t} [{h}]"
                )

        gg = ge_agg.sort_values("species_pretty")
        if not gg.empty:
            ax.plot(
                gg["species_pretty"], gg[mkey],
                marker="o", linewidth=2.8, color="black", label="GeAnno (M. esculenta, PCA)", zorder=5
            )

        ax.set_title(mtitle, fontsize=14)
        ax.set_ylim(0, 1)
        ax.set_xlabel("Species")
        ax.grid(axis="y", linestyle=":", alpha=0.55)
    axes[0].set_ylabel("Value")

    tool_handles = [Line2D([0],[0], color=palette[t], lw=2.0, label=t) for t in tool_order]
    hint_handles = [Line2D([0],[0], color="black", lw=2.0, dashes=dashes_map[h], label=h) for h in hint_order]
    geanno_handle = Line2D([0],[0], color="black", lw=2.8, label="GeAnno (M. esculenta, PCA)")

    leg1 = fig.legend(tool_handles, [h.get_label() for h in tool_handles],
                      loc="lower center", bbox_to_anchor=(0.5, 0.02),
                      ncol=min(4, len(tool_handles)), frameon=False, title=None, prop={'size': 11})
    leg2 = fig.legend(hint_handles + [geanno_handle],
                      [h.get_label() for h in hint_handles] + [geanno_handle.get_label()],
                      loc="lower center", bbox_to_anchor=(0.5, -0.10),
                      ncol=4, frameon=False, title=None, prop={'size': 11})
    fig.add_artist(leg1)

    fig.suptitle("GeAnno and evidence-based tools by hint type across species", y=0.98, fontsize=16)
    fig.tight_layout(rect=[0.05, 0.12, 1, 0.95])

    fig_path = out_dir / "evidence_species_by_hints_plus_geanno_triple.png"
    fig.savefig(fig_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)

    tidy_out = pd.concat([
        ev_agg.assign(setting="Evidence-based", hint=ev_agg["hint_l"]),
        ge_agg.assign(setting="GeAnno", hint=pd.NA, tool_pretty="GeAnno (M. esculenta, PCA)")
    ], ignore_index=True)
    
    return fig_path, tidy_out