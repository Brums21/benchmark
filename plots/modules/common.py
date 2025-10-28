import pandas as pd
import numpy as np

from typing import Iterable, List, Optional

GEANNO_WIN = 1500
GEANNO_STEP = 50
GEANNO_THR = 0.8

SPECIES_PRETTY = {
    "arabidopsis_thaliana": "A. thaliana",
    "oryza_sativa": "O. sativa",
    "gossypium_raimondii": "G. raimondii",
    "manihot_esculenta": "M. esculenta",
}

SPECIES_SIZE = {
    "arabidopsis_thaliana": 30210,
    "oryza_sativa":         42962,
    "gossypium_raimondii":  55469,
    "manihot_esculenta":    42691,
}

TOOL_MAP = {
    "a_thaliana_model": "A. thaliana model",
    "a_thaliana_model_PCA": "A. thaliana model (PCA)",
    "o_sativa_model": "O. sativa model",
    "o_sativa_model_PCA": "O. sativa model (PCA)",
    "genemark_model": "GeneMark model",
    "genemark_model_PCA": "GeneMark model (PCA)",
    "m_esculenta_model_PCA": "M. esculenta model (PCA)",
}

TOOL_MAPPING = {
    "genemarkes":   "GeneMark-ES",
    "genemarkep":   "GeneMark-EP+",
    "genemarketp":  "GeneMark-ETP",
    "gemoma":       "GeMoMa",
    "augustus":     "AUGUSTUS",
    "snap":         "SNAP",
}

METRIC_LABELS = {
    "precision": "Precision",
    "recall":    "Recall",
    "f1":        "F1-score",
}

def _subset_geanno_mesculenta_any(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to M. esculenta PCA"""
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

def _map_snap_model(x: str) -> str:
    """ Map SNAP train_species to two instances of SNAP."""
    if not isinstance(x, str): return "Unknown"
    k = x.strip().lower()
    if k in {"arabidopsis_thaliana", "a_thaliana", "arabidopsis"}: return "A. thaliana"
    if k in {"oryza_sativa", "o_sativa", "rice"}:                 return "O. sativa"
    return x

def _filter_geanno_fixed_config(df: pd.DataFrame,
                                win: int = GEANNO_WIN,
                                step: int = GEANNO_STEP,
                                thr: float = GEANNO_THR) -> pd.DataFrame:
    """
    Keep only GeAnno rows at a certain window, step and threshold
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

def _normalise_hint_column(df: pd.DataFrame, src_col: str = "hint") -> pd.Series:
    """ Normalize hint column to lowercase stripped strings."""
    if src_col not in df.columns:
        return pd.Series(pd.NA, index=df.index, name="hint_l")
    s = df[src_col].copy()
    m = s.notna()
    s.loc[m] = s.loc[m].astype(str).str.lower().str.strip()
    return s.rename("hint_l")


def _is_abinitio_aug(df: pd.DataFrame) -> pd.Series:
    """ Return series indicating rows that are AUGUSTUS ab initio"""
    hint_l = df.get("hint_l", _normalise_hint_column(df))
    return (df["tool"].astype(str).str.lower().eq("augustus") & (hint_l.isna() | hint_l.eq("abinitio")))


def _species_to_pretty(s: pd.Series) -> pd.Series:
    """ Map species codes to presentable names."""
    return s.map(SPECIES_PRETTY).fillna(s.astype(str).str.replace("_", " ").str.title())


def _ensure_numeric(df: pd.DataFrame, cols) -> pd.DataFrame:
    """ Ensure specified columns are numeric, and if they aren't, convert them"""
    d = df.copy()
    for c in cols:
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce")
    return d


def _compute_prec_rec_f1(df: pd.DataFrame) -> pd.DataFrame:
    """ Compute precision, recall, f1 from tp, fp, fn columns"""
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


def _ensure_prf_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """ Ensure precision, recall, f1 columns exist and are numeric and in [0,1]"""
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


def _bench_abinitio_slice_for_model(df: pd.DataFrame, model: str) -> pd.DataFrame:
    """ Get AUGUSTUS ab initio + SNAP rows for a given model (arabidopsis or rice) at 0% mut rate"""
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
    """ Get GeAnno rows for specified models, relabelled """
    rows = []
    for key, lab in zip(model_keys, labels):
        sub = geanno_df[geanno_df["tool_pretty"].astype(str).str.contains(key, case=False, regex=False)].copy()
        if sub.empty:
            continue
        sub = sub[["species", "species_pretty", "precision", "recall", "f1"]]
        sub["tool_pretty"] = lab
        rows.append(sub)
    return _concat_nonempty(rows, cols=["species","species_pretty","precision","recall","f1","tool_pretty"])


def _concat_nonempty(dfs: Iterable[pd.DataFrame], cols: Optional[List[str]] = None) -> pd.DataFrame:
    """ Concatenate only non-empty dataframes from an iterable"""
    parts = [x for x in dfs if x is not None and not x.empty]
    if not parts:
        return pd.DataFrame(columns=cols or [])
    return pd.concat(parts, ignore_index=True)

