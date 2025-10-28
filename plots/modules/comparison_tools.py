import pandas as pd

from pathlib import Path
from typing import Tuple

from modules.common import GEANNO_STEP, GEANNO_THR, GEANNO_WIN, TOOL_MAP, _compute_prec_rec_f1, \
                    _ensure_numeric, _ensure_prf_metrics, _species_to_pretty

from modules.load_save import save_table_csv

def export_geanno_models_table_csv(
    df_geanno: pd.DataFrame,
    out_dir: Path,
    window: int = GEANNO_WIN,
    step: int = GEANNO_STEP,
    threshold: float = GEANNO_THR,
    mut_rate: float = 0.0,
    decimals: int = 2,
) -> Tuple[Path, pd.DataFrame]:
    """ Precision/Recall/F1-score table for GeAnno models """

    out_dir.mkdir(parents=True, exist_ok=True)
    d = df_geanno.copy()

    d = _ensure_numeric(d, ["window","step","threshold","mut_rate","tp","fp","fn",
                            "precision","recall","f1"])
    sel = (
        (d.get("window", window) == window) &
        (d.get("step", step) == step) &
        (d.get("threshold", threshold) == threshold) &
        (d.get("mut_rate", mut_rate).fillna(0) == mut_rate)
    )
    d = d[sel].copy()
    if d.empty:
        raise RuntimeError("No GeAnno rows at the requested fixed operating point.")

    if {"tp","fp","fn"}.issubset(d.columns):
        d = _compute_prec_rec_f1(d)
    else:
        d = _ensure_prf_metrics(d)

    d["species_pretty"] = _species_to_pretty(d["species"])
    if "tool_pretty" not in d.columns:
        d["tool_pretty"] = d["tool"].map(TOOL_MAP).fillna(d["tool"].astype(str))

    tp = d["tool_pretty"].astype(str)
    d["is_pca"] = tp.str.contains("(PCA)", case=False, regex=False)
    d["model_base"] = tp.str.replace(" (PCA)", "", regex=False).str.strip()

    model_order = [
        "A. thaliana model",
        "O. sativa model",
        "GeneMark model",
        "M. esculenta model",
    ]
    d = d[d["model_base"].isin(model_order)].copy()

    agg = (
        d.groupby(["species_pretty","model_base","is_pca"], as_index=False)
         .agg(precision=("precision","mean"),
              recall=("recall","mean"),
              f1=("f1","mean"))
    )

    for m in ("precision","recall","f1"):
        agg[m] = (agg[m] * 100.0).round(decimals)

    def _col_name(model_base: str, is_pca: bool) -> str:
        if model_base == "M. esculenta model":
            return "M. esculenta model (PCA)"
        return f"{model_base} ({'PCA' if is_pca else 'Non-PCA'})"

    agg["column"] = [_col_name(mb, ip) for mb, ip in zip(agg["model_base"], agg["is_pca"])]

    final_cols = [
        "A. thaliana model (Non-PCA)", "A. thaliana model (PCA)",
        "O. sativa model (Non-PCA)",   "O. sativa model (PCA)",
        "GeneMark model (Non-PCA)",    "GeneMark model (PCA)",
        "M. esculenta model (PCA)",
    ]

    species_order = ["A. thaliana", "G. raimondii", "M. esculenta", "O. sativa"]
    species_present = [s for s in species_order if s in set(agg["species_pretty"])]
    if not species_present:
        species_present = list(agg["species_pretty"].drop_duplicates())

    blocks = []
    for metric, mlabel in (("precision","Precision"), ("recall","Recall"), ("f1","F1-score")):
        piv = (agg.pivot_table(index="species_pretty", columns="column", values=metric, aggfunc="mean")
                 .reindex(index=species_present, columns=final_cols))
        piv.insert(0, "Metric", mlabel)
        piv.insert(1, "Species", piv.index)
        block = piv.reset_index(drop=True)

        avg_vals = {c: round(block[c].mean(skipna=True), decimals) for c in final_cols}
        avg_row = {"Metric": mlabel, "Species": "Avg.", **avg_vals}
        block = pd.concat([block, pd.DataFrame([avg_row])], ignore_index=True)
        blocks.append(block)

    out_df = pd.concat(blocks, ignore_index=True)
    out_df = out_df[["Metric","Species"] + final_cols]

    csv_path = out_dir / f"csv/geanno_models_table_win{window}_step{step}_thr{threshold}_mut{mut_rate}.csv"
    save_table_csv(out_df, csv_path)
    return csv_path, out_df
