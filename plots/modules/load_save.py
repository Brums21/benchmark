from pathlib import Path
import numpy as np
import pandas as pd

from modules.common import SPECIES_PRETTY, TOOL_MAP

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

        df["precision"] = df["specificity"]

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