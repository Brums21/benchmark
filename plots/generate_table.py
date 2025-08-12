import pandas as pd
from pathlib import Path

EXPERIMENT_FOLDERS = {
    "output_genemark_XGBoost_1500_50_esculenta": "M. esculenta",
    "output_genemark_XGBoost_1500_50_esculenta_f_eng": "M. esculenta feat_eng",
}

base_dir = Path("../test_model")
tools_dir = Path("./final_results")
geanno_rows = []
external_tool_rows = []

def compute_f1(precision, recall):
    if pd.isna(precision) or pd.isna(recall) or (precision + recall) == 0:
        return None
    return 2 * (precision * recall) / (precision + recall)

for folder in EXPERIMENT_FOLDERS.keys():
    path = base_dir / folder

    for metrics_file in path.glob("output_*_*_*.csv"):
        if metrics_file.name.endswith(("_auc.csv", "_roc.csv", "_prc.csv")):
            continue

        parts = metrics_file.stem.split("_")
        window = parts[1]
        step = parts[2]
        threshold = parts[3]
        config = EXPERIMENT_FOLDERS[folder]
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
            "Threshold": float(threshold),
            "Precision": precision,
            "Recall": recall,
            "F1_score": f1,
            "AUC_ROC": auc_roc,
            "AUC_PRC": auc_prc,
        })

geanno_df = pd.DataFrame(geanno_rows)

"""best_row = geanno_df.loc[geanno_df["Precision"].idxmax()].copy()
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
], ignore_index=True) """

average_list = []
best_list_precision = []
best_list_recall = []
best_list_f1_score = []

for config, group in geanno_df.groupby("Config"):
    avg = group[["Precision", "Recall", "F1_score", "AUC_ROC", "AUC_PRC"]].mean().to_dict()
    avg["Tool"] = "GeAnno_avg"
    avg["Config"] = config
    average_list.append(avg)
    
    best_idx = group["Precision"].idxmax()
    best_row = group.loc[best_idx].copy()
    best_row["Tool"] = "GeAnno_precision_max"
    best_list_precision.append(best_row)

    best_idx = group["Recall"].idxmax()
    best_row = group.loc[best_idx].copy()
    best_row["Tool"] = "GeAnno_recall_max"
    best_list_recall.append(best_row)

    best_idx = group["F1_score"].idxmax()
    best_row = group.loc[best_idx].copy()
    best_row["Tool"] = "GeAnno_F1_score_max"
    best_list_f1_score.append(best_row)

tools_avg_df = pd.concat([
    pd.DataFrame(average_list),
    pd.DataFrame(best_list_precision),
    pd.DataFrame(best_list_recall),
    pd.DataFrame(best_list_f1_score)
], ignore_index=True)

tools_avg_df.to_csv("geanno_average_mean_esculenta.csv", index=False)
geanno_df.to_csv("geanno_config_esculenta.csv", index=False)

print("Done")