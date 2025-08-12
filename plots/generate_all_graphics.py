import argparse
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import glob
import os

try:
    import seaborn as sns
    sns.set_style("whitegrid")
    HAS_SNS = True
except ImportError:
    HAS_SNS = False
    warnings.warn("seaborn not found - heat-maps will fall back to matplotlib.")


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
                hints=parts[4],
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
        for k, v in meta.items():
            df[k] = v
        frames.append(df)
    if not frames:
        raise RuntimeError(f"No csv in {csv_dir}")
    df = pd.concat(frames, ignore_index=True)
    # compute metrics
    df["precision"] = df.tp / (df.tp + df.fp).replace(0, np.nan)
    df["recall"] = df.tp / (df.tp + df.fn).replace(0, np.nan)
    df["f1"] = 2 * df.precision * df.recall / (df.precision + df.recall).replace(0, np.nan)

    df.fillna(0, inplace=True)

    return df

def plot_sensitivity_specificity(df: pd.DataFrame, out_dir: Path, tool_dir: Path, dpi: int):
    filtered = df[(df["mut_rate"] == 0.0) & (df["label"] == "gene_nucleotide")].copy()

    metrics = (
        filtered.groupby("tool")[["sensitivity", "specificity"]]
        .mean()
        .reset_index()
    )

    if metrics["sensitivity"].max() > 1.5:
        metrics["sensitivity"] /= 100.0
    if metrics["specificity"].max() > 1.5:
        metrics["specificity"] /= 100.0

    total_sensitivity = 0
    total_specificity = 0
    count = 0

    for file_name in os.listdir(tool_dir):
        if file_name.endswith(".csv"):
            file_path = tool_dir / file_name
            model_df = pd.read_csv(file_path)

            model_df = model_df[model_df["sensitivity"] > 0]
            model_df = model_df[model_df["specificity"] > 0]

            model_df_gene = model_df[model_df["label"] == "gene_nucleotide"]

            if not model_df_gene.empty:
                total_sensitivity += model_df_gene["sensitivity"].mean()
                total_specificity += model_df_gene["specificity"].mean()
                count += 1

    if count > 0:
        avg_sensitivity = total_sensitivity / count / 100
        avg_specificity = total_specificity / count / 100
        model_metrics = [{"tool": "Model (avg)", "sensitivity": avg_sensitivity, "specificity": avg_specificity}]
    else:
        model_metrics = []

    model_metrics_df = pd.DataFrame(model_metrics)

    metrics = pd.concat([metrics, model_metrics_df], ignore_index=True)

    melted = metrics.melt(id_vars="tool", var_name="Metric", value_name="Score")

    plt.figure(figsize=(12, 6))
    sns.barplot(data=melted, x="tool", y="Score", hue="Metric")
    plt.ylim(0, 1)
    plt.title("Sensitivity and Specificity per Tool (Label = gene_nucleotide, mut_rate = 0.0)")
    plt.ylabel("Score")
    plt.xlabel("Tool")
    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.savefig(out_dir / "sensitivity_specificity_gene_nucleotide_by_tool.png", dpi=dpi)
    plt.close()


def save(fig: plt.Figure, outfile: Path, dpi: int):
    fig.tight_layout()
    fig.savefig(outfile.with_suffix(".png"), dpi=dpi)
    plt.close(fig)

def f1_vs_mutation(df: pd.DataFrame, out_dir: Path, dpi: int):
    data = (
        df.groupby(["species", "tool", "mut_rate"])
        ["f1"].mean()
        .reset_index()
        .sort_values("mut_rate")
    )

    species = sorted(data.species.unique())
    ncols = 2
    nrows = int(np.ceil(len(species) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(6 * ncols, 4 * nrows), sharey=True)
    axes = axes.flatten()

    for ax, sp in zip(axes, species):
        sub = data[data.species == sp]
        for tool, grp in sub.groupby("tool"):
            ax.plot(grp.mut_rate, grp.f1, marker="o", label=tool)
        ax.set_title(sp)
        ax.set_xlabel("mutation rate")
        ax.set_ylabel("F1")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.02))
    save(fig, out_dir / "f1_vs_mutation", dpi)

def precision_vs_mutation(df: pd.DataFrame, out_dir: Path, dpi: int):
    data = (
        df.groupby(["species", "tool", "mut_rate"])
        ["precision"].mean()
        .reset_index()
        .sort_values("mut_rate")
    )

    species = sorted(data.species.unique())
    ncols = 2
    nrows = int(np.ceil(len(species) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(6 * ncols, 4 * nrows), sharey=True)
    axes = axes.flatten()

    for ax, sp in zip(axes, species):
        sub = data[data.species == sp]
        for tool, grp in sub.groupby("tool"):
            ax.plot(grp.mut_rate, grp.precision, marker="o", label=tool)
        ax.set_title(sp)
        ax.set_xlabel("mutation rate")
        ax.set_ylabel("Precision")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.02))
    save(fig, out_dir / "precision_vs_mutation", dpi)

def recall_vs_mutation(df: pd.DataFrame, out_dir: Path, dpi: int):
    data = (
        df.groupby(["species", "tool", "mut_rate"])
        ["recall"].mean()
        .reset_index()
        .sort_values("mut_rate")
    )

    species = sorted(data.species.unique())
    ncols = 2
    nrows = int(np.ceil(len(species) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(6 * ncols, 4 * nrows), sharey=True)
    axes = axes.flatten()

    for ax, sp in zip(axes, species):
        sub = data[data.species == sp]
        for tool, grp in sub.groupby("tool"):
            ax.plot(grp.mut_rate, grp.recall, marker="o", label=tool)
        ax.set_title(sp)
        ax.set_xlabel("mutation rate")
        ax.set_ylabel("Recall")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.02))
    save(fig, out_dir / "recall_vs_mutation", dpi)

def overall_tool_performance(df: pd.DataFrame, out_dir: Path, dpi: int):
    metrics = ["precision", "recall", "f1"]
    
    grouped = df.groupby("tool")[metrics].mean()

    fig, ax = plt.subplots(figsize=(1.5 * len(grouped), 6))
    tools = grouped.index
    idx = np.arange(len(tools))
    width = 0.2

    for i, metric in enumerate(metrics):
        ax.bar(idx + i * width, grouped[metric], width, label=metric)

    ax.set_xticks(idx + width)
    ax.set_xticklabels(tools, rotation=45, ha="right")
    ax.set_ylabel("Score")
    ax.set_title("Overall Precision, Recall, and F1-Score per Tool")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(out_dir / "overall_tool_metrics.png", dpi=dpi)
    plt.close(fig)

def hint_effect(df: pd.DataFrame, out_dir: Path, dpi: int):
    hints = ["genus", "order", "far"]
    data = (
        df[df.hint.isin(hints)]
        .groupby(["tool", "hint"])["f1"].mean()
        .unstack("hint")[hints]  # ensure order
        .sort_values(hints[0], ascending=False)
    )
    fig, ax = plt.subplots(figsize=(0.6 * len(data) + 4, 4))
    idx = np.arange(len(data))
    width = 0.25
    for i, h in enumerate(hints):
        ax.bar(idx + i * width, data[h], width, label=h)
    ax.set_xticks(idx + width)
    ax.set_xticklabels(data.index, rotation=45, ha="right")
    ax.set_ylabel("F1 (mean across species & mut-rates)")
    ax.set_title("Effect of evidence depth - within each tool")
    ax.legend(frameon=False)
    save(fig, out_dir / "hint_effect", dpi)


def metric_heatmaps_by_hint(df: pd.DataFrame, out_dir: Path, dpi: int):
    metrics = ["precision", "recall", "f1"]
    hint_types = ["genus", "order", "far"]

    tools_keep = df.loc[df.hint != "abinitio", "tool"].unique()

    for i, hint in enumerate(hint_types):
        
        fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(24, 6), sharey=True)
        
        for j, metric in enumerate(metrics):
            ax = axes[j]
            subset = df[(df.hint == hint) & (df.tool.isin(tools_keep))]
            tbl = (
                subset.groupby(["species", "tool"])[metric]
                .mean()
                .unstack("tool")
            )
            
            title = f"{metric.capitalize()}"
            
            sns.heatmap(tbl, annot=True, fmt=".2f", cmap="YlGnBu", ax=ax, cbar=j == 0 and i == 0)
            ax.set_title(title)
            ax.set_xlabel("Tool")
            ax.set_ylabel("Species")
            
        plt.tight_layout()
        fig.suptitle(f"Metric Heatmaps for {hint} hints", fontsize=20, y=1.02)
        fig.savefig(out_dir / f"heatmap_{hint}.png", dpi=dpi, bbox_inches="tight")
        plt.close(fig)
        

def compare_tools(df: pd.DataFrame, geanno_folder: Path, fig_dir: Path, dpi: int = 300):
    geanno_frames = []
    for fpath in glob.glob(str(geanno_folder / "*.csv")):
        gdf = pd.read_csv(fpath)

        if (gdf["sensitivity"] == 0).all() and (gdf["specificity"] == 0).all():
            continue

        gdf = gdf[gdf['tp'] + gdf['fp'] + gdf['fn'] > 0]  # remove empty rows
        gdf["precision"] = gdf["tp"] / (gdf["tp"] + gdf["fp"]).replace(0, np.nan)
        gdf["recall"] = gdf["tp"] / (gdf["tp"] + gdf["fn"]).replace(0, np.nan)
        gdf["f1"] = 2 * gdf["precision"] * gdf["recall"] / (gdf["precision"] + gdf["recall"]).replace(0, np.nan)
        gdf["tool"] = "GeAnno"
        geanno_frames.append(gdf[["label", "precision", "recall", "f1", "tool"]])

    geanno_df = pd.concat(geanno_frames, ignore_index=True)
    geanno_df = geanno_df.dropna()

    base_df = df[df["mut_rate"] == 0.0].copy()
    base_df = base_df[["label", "precision", "recall", "f1", "tool"]]
    base_df = base_df[~((base_df["precision"] == 0.0) & (base_df["recall"] == 0.0) & (base_df["f1"] == 0.0))]

    all_df = pd.concat([base_df, geanno_df], ignore_index=True)

    melted = all_df.melt(id_vars=["tool", "label"], value_vars=["precision", "recall", "f1"],
                         var_name="Metric", value_name="Score")

    labels = sorted(melted["label"].unique())
    for lbl in labels:
        subset = melted[melted["label"] == lbl]
        plt.figure(figsize=(12, 6))
        sns.barplot(data=subset, x="tool", y="Score", hue="Metric", errorbar=None, dodge=True)
        plt.title(f"Precision, Recall, and F1 by Tool for Label: {lbl}")
        plt.ylabel("Score")
        plt.xlabel("Tool")
        plt.xticks(rotation=45)
        plt.ylim(0, 1)
        plt.tight_layout()
        plt.savefig(fig_dir / f"compare_{lbl}_geanno.png", dpi=dpi)
        plt.close()

    averaged_df = melted.groupby(["tool", "Metric"], as_index=False)["Score"].mean()

    plt.figure(figsize=(20, 8))
    sns.barplot(
        data=averaged_df,
        x="tool", y="Score",
        hue="Metric",
        ci=None,
        dodge=True,
        errorbar=None
    )
    plt.title("Tool Comparison: Average Precision, Recall, and F1-Score Across All Labels")
    plt.ylabel("Average Score")
    plt.xlabel("Tool")
    plt.xticks(rotation=45)
    plt.ylim(0, 1)
    plt.tight_layout()
    plt.legend(title="Metric")
    plt.savefig(fig_dir / "compare_all_tools_metrics_geanno.png", dpi=300)
    plt.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_dir", type=Path)
    ap.add_argument("fig_dir", type=Path)
    ap.add_argument("--dpi", type=int, default=300)
    args = ap.parse_args()

    args.fig_dir.mkdir(parents=True, exist_ok=True)
    df = load_results(args.csv_dir)

    #f1_vs_mutation(df, args.fig_dir, args.dpi)
    #precision_vs_mutation(df, args.fig_dir, args.dpi)
    #recall_vs_mutation(df, args.fig_dir, args.dpi)
    #hint_effect(df, args.fig_dir, args.dpi)

    #metric_heatmaps_by_hint(df, args.fig_dir, dpi=300)

    #overall_tool_performance(df, args.fig_dir, dpi=300)

    tool_csvs = Path("test_model/output/")

    plot_sensitivity_specificity(df, args.fig_dir, tool_csvs, dpi=300)
    
    #compare_tools(df, tool_csvs, args.fig_dir, args.dpi)

    print("Figures written to", args.fig_dir)

if __name__ == "__main__":
    main()
