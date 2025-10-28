import warnings
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from pathlib import Path
from typing import Optional

from modules.load_save import save_table_csv
from modules.common import GEANNO_STEP, GEANNO_THR, GEANNO_WIN, _species_to_pretty

def plot_auc_heatmap_stack_geanno_mesc_vs_aug_abinitio(geanno_auc_csv: Path, bench_auc_dir: Path, out_dir: Path, dpi: int = 300) -> Optional[Path]:
    """ Two heatmaps stacked vertically, comparing AUC-ROC and AU-PRC for GeAnno (M. esculenta, PCA) vs AUGUSTUS (ab initio) """
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
    ax1.set_xlabel(""); ax1.set_ylabel(""); ax1.set_title("AUCROC")
    sns.heatmap(piv_prc, ax=ax2, annot=True, fmt=".3f", cmap="viridis", cbar_kws={"shrink": 0.9})
    ax2.set_xlabel(""); ax2.set_ylabel(""); ax2.set_title("AUPRC")

    fig.suptitle("GeAnno (M. esculenta, PCA) and AUGUSTUS (ab initio) AUC comparison", y=0.98, fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.96])

    out_png = out_dir / "auc_abinitio_geanno_mesc_vs_aug_stacked.png"
    fig.savefig(out_png, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return out_png