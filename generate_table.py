import pandas as pd
from pathlib import Path

EXPERIMENT_FOLDERS = [
    "output_thaliana_a_thaliana"
]

base_dir = Path("./test_model")
tools_dir = Path("./final_results")
geanno_rows = []
external_tool_rows = []

def compute_f1(precision, recall):
    if pd.isna(precision) or pd.isna(recall) or (precision + recall) == 0:
        return None
    return 2 * (precision * recall) / (precision + recall)

for folder in EXPERIMENT_FOLDERS:
    path = base_dir / folder

    for metrics_file in path.glob("output_*_*.csv"):
        if metrics_file.name.endswith("_auc.csv"):
            continue
        if metrics_file.name.endswith("_roc.csv"):
            continue
        if metrics_file.name.endswith("_prc.csv"):
            continue

        parts = metrics_file.stem.split("_")
        window = parts[1]
        step = parts[2]
        config = folder.replace("output_", "")
        tool = "GeAnno"

        df = pd.read_csv(metrics_file)
        df = df[df["label"] == "gene_nucleotide"]
        if df.empty:
            continue

        auc_roc = auc_prc = None
        auc_file = metrics_file.with_name(metrics_file.stem + "_auc.csv")
        if auc_file.exists():
            auc_df = pd.read_csv(auc_file)
            auc_roc = auc_df.iloc[0, 0]
            auc_prc = auc_df.iloc[0, 1]

        row = df.iloc[0]
        precision = row["specificity"]
        recall = row["sensitivity"]
        f1 = compute_f1(precision, recall)

        geanno_rows.append({
            "Tool": tool,
            "Config": config,
            "Window": int(window),
            "Step": int(step),
            "Precision": precision,
            "Recall": recall,
            "F1_score": f1,
            "AUC_ROC": auc_roc,
            "AUC_PRC": auc_prc,
        })

geanno_df = pd.DataFrame(geanno_rows)

best_row = geanno_df.loc[geanno_df["Precision"].idxmax()].copy()
best_row["Tool"] = "GeAnno_max"

geanno_avg = geanno_df.agg({
    "Precision": "mean",
    "Recall": "mean",
    "F1_score": "mean",
    "AUC_ROC": "mean",
    "AUC_PRC": "mean",
}).to_dict()
geanno_avg["Tool"] = "GeAnno"

for tool_csv in tools_dir.glob("*.csv"):
    if tool_csv.name.endswith("_auc.csv") or "original" not in tool_csv.name or "arabidopsis_thaliana" not in tool_csv.name:
        continue

    if "augustus" in tool_csv.name and "abinitio" not in tool_csv.name:
        continue

    if "snap" in tool_csv.name and "rice" in tool_csv.name:
        continue

    tool_name = tool_csv.name.split("_")[0].lower()
    df = pd.read_csv(tool_csv)
    df = df[df["label"] == "gene_nucleotide"]
    if df.empty:
        continue

    auc_file = tool_csv.with_name(tool_csv.stem + "_auc.csv")
    auc_roc = auc_prc = None
    if auc_file.exists():
        auc_df = pd.read_csv(auc_file)
        auc_roc = auc_df.iloc[0, 0]
        auc_prc = auc_df.iloc[0, 1]

    row = df.iloc[0]
    precision = row["specificity"]
    recall = row["sensitivity"]
    f1 = compute_f1(precision, recall)

    external_tool_rows.append({
        "Tool": tool_name,
        "Precision": precision,
        "Recall": recall,
        "F1_score": f1,
        "AUC_ROC": auc_roc,
        "AUC_PRC": auc_prc
    })

external_df = pd.DataFrame(external_tool_rows)
external_avg_df = external_df.groupby("Tool").agg({
    "Precision": "mean",
    "Recall": "mean",
    "F1_score": "mean",
    "AUC_ROC": "mean",
    "AUC_PRC": "mean"
}).reset_index()

tools_avg_df = pd.concat([
    external_avg_df,
    pd.DataFrame([geanno_avg]),
    pd.DataFrame([best_row])
], ignore_index=True)

tools_avg_df.to_csv("tools_avg_mut0_thaliana_a_thaliana.csv", index=False)
geanno_df.to_csv("geanno_configs_thaliana_a_thaliana.csv", index=False)

print("Saved to tools_avg_mut0_a_thaliana.csv and geanno_configs_a_thaliana.csv")
