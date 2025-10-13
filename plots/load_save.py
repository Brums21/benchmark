from pathlib import Path
import numpy as np
import pandas as pd

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


def parse_filename(fname: str):
    stem = Path(fname).stem
    parts = stem.split("_")
    if len(parts) < 6:
        raise ValueError(f"Filename {fname} has <6 tokens - cannot parse.")
    
    if parts[0] == "augustus":
        if parts[4] == "abinitio":
            return dict(
                tool=parts[0],
                species="_".join(parts[1:3]),
                mut_rate=float(parts[3]) if parts[3] != "original" else 0.0, 
                time_sec=float(parts[5]),
                ram_mb=int(parts[6]),
            )
        else:
            return dict(
                tool=parts[0],
                species="_".join(parts[1:3]),
                mut_rate=float(parts[3]) if parts[3] != "original" else 0.0, 
                hint=parts[4],
                time_sec=float(parts[5]),
                ram_mb=int(parts[6]),
            )
    
    if parts[0] == "gemoma":
        return dict(
            tool=parts[0],
            species="_".join(parts[1:3]),
            mut_rate=float(parts[3]) if parts[3] != "original" else 0.0, 
            hint=parts[4],
            time_sec=float(parts[5]),
            ram_mb=int(parts[6]),
        )
    
    if parts[0] == "genemarkep":
        return dict(
            tool=parts[0],
            species="_".join(parts[1:3]),
            mut_rate=float(parts[3]) if parts[3] != "original" else 0.0, 
            hint=parts[4],
            time_sec=float(parts[5]),
            ram_mb=int(parts[6]),
        )
    
    if parts[0] == "genemarkes":
        return dict(
            tool=parts[0],
            species="_".join(parts[1:3]),
            mut_rate=float(parts[3]) if parts[3] != "original" else 0.0, 
            time_sec=float(parts[4]),
            ram_mb=int(parts[5]),
        )
    
    if parts[0] == "genemarketp":
        return dict(
            tool=parts[0],
            species="_".join(parts[1:3]),
            mut_rate=float(parts[3]) if parts[3] != "original" else 0.0, 
            hint=parts[4],
            time_sec=float(parts[5]),
            ram_mb=int(parts[6]),
        )
    
    if parts[0] == "snap":
        return dict(
            tool=parts[0],
            species="_".join(parts[1:3]),
            mut_rate=float(parts[3]) if parts[3] != "original" else 0.0, 
            train_species=parts[4],
            time_sec=float(parts[5]),
            ram_mb=int(parts[6]),
        )

def load_results(csv_dir: Path) -> pd.DataFrame:
    frames = []
    for fp in csv_dir.glob("*.csv"):
        meta = parse_filename(fp.name)
        df = pd.read_csv(fp)

        if "label" not in df.columns:
            continue
        df["label"] = df["label"].astype(str).str.strip().str.lower()
        df = df[df["label"] == "gene_nucleotide"]
        if df.empty:
            continue

        for k, v in meta.items():
            df[k] = v

        # = sensibility
        df["precision"] = df["specificity"]

        # = sensitivity
        df["recall"] = df["sensitivity"]
        df["f1"] = 2 * df.specificity * df.sensitivity / (df.specificity + df.sensitivity).replace(0, np.nan)
        df.fillna(0, inplace=True)
        frames.append(df)

    if not frames:
        raise RuntimeError(f"No gene_nucleotide rows found in {csv_dir}")
    dataset = pd.concat(frames, ignore_index=True)

    
    for col in ["recall", "precision", "f1"]:
        if col in dataset.columns:
            dataset[col] = dataset[col] / 100.0

    return dataset

def load_geanno(csv_dir: Path) -> pd.DataFrame:
    frames = []

    for p in csv_dir.glob("*.csv"):
        df = pd.read_csv(p)
        df["__file"] = p.name
        frames.append(df)

    if not frames:
        raise SystemExit("No CSVs found.")
    
    d = pd.concat(frames, ignore_index=True)
    d = d.rename(columns={
        "model": "tool",
        "time": "time_sec",
        "mem": "ram_kb",
        "mutation_rate": "mut_rate",
    })

    d["species_pretty"] = d["species"].map(SPECIES_PRETTY).fillna(
        d["species"].str.replace("_", " ").str.title()
    )

    d["tool_pretty"] = d["tool"].map(TOOL_MAP).fillna(d["tool"])

    return d

def save_table_csv(pd_table: pd.DataFrame, output: str):
    filepath = Path(output)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    pd_table.to_csv(filepath)