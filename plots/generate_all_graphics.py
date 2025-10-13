import argparse
from pathlib import Path
import warnings
import seaborn as sns

from load_save import load_results, load_geanno

from geanno_plots import plot_geanno_vs_abinitio_for_model, plot_geanno_vs_genemark, \
                        plot_geanno_vs_tools_mut_rate, plot_ram_time_all_tools_overall_dots_plus_geanno, \
                        plot_auc_heatmap_stack_geanno_mesc_vs_aug_abinitio

from ab_initio_plots import plot_model_comparison_RAM_time_consumed, plot_model_comparison_zero_mut_ab_initio, \
                            plot_mutation_curves_ab_initio, plot_model_comparison_RAM_time_consumed_ab_initio
        
from comparison_plots import plot_mutation_curves_ab_vs_evidence_macro_simple, plot_ram_time_all_tools_overall_dots

from evidence_plots import plot_model_comparison_RAM_time_consumed_evidence, plot_evidence_zero_mut_collapsed, \
                            plot_mutation_curves_evidence, plot_hint_effect_curves, plot_evidence_zero_mut_collapsed_hints

try:
    sns.set_style("whitegrid")
    HAS_SNS = True
except ImportError:
    HAS_SNS = False
    warnings.warn("seaborn not found - heat-maps will fall back to matplotlib.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_dir", type=Path)
    ap.add_argument("fig_dir", type=Path)
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--results_geanno", type=Path, required=True,
                    help="Path to GeAnno's results")
    ap.add_argument("--geanno_auc_csv", type=Path, required=True,
                help="CSV with GeAnno AUCs (species,model,mutation_rate,window,step,threshold,auc_roc,auc_prc)")

    args = ap.parse_args()

    args.fig_dir.mkdir(parents=True, exist_ok=True)
    df = load_results(args.csv_dir)
    df_geanno = load_geanno(args.results_geanno)

    ab_initio_path = args.fig_dir / "ab_initio"
    evidence_path = args.fig_dir / "evidence"
    comparison_path = args.fig_dir / "comparison"
    geanno_path = args.fig_dir / "geanno"

    ab_initio_path.mkdir(parents=True, exist_ok=True)
    evidence_path.mkdir(parents=True, exist_ok=True)
    comparison_path.mkdir(parents=True, exist_ok=True)
    geanno_path.mkdir(parents=True, exist_ok=True)

    plot_model_comparison_zero_mut_ab_initio(df, ab_initio_path, args.dpi)
    plot_mutation_curves_ab_initio(df, ab_initio_path, args.dpi)
    plot_model_comparison_RAM_time_consumed_ab_initio(df, ab_initio_path, args.dpi)

    plot_evidence_zero_mut_collapsed(df, evidence_path, args.dpi)
    plot_evidence_zero_mut_collapsed_hints(df, evidence_path, args.dpi)
    plot_mutation_curves_evidence(df, evidence_path, args.dpi)
    plot_model_comparison_RAM_time_consumed_evidence(df, evidence_path, args.dpi)
    plot_hint_effect_curves(df, evidence_path, args.dpi)

    plot_mutation_curves_ab_vs_evidence_macro_simple(df, comparison_path, args.dpi)
    plot_ram_time_all_tools_overall_dots(df, comparison_path, args.dpi)

    plot_geanno_vs_abinitio_for_model(df, args.results_geanno, model="arabidopsis", out_dir=geanno_path)
    plot_geanno_vs_abinitio_for_model(df, args.results_geanno, model="rice",        out_dir=geanno_path)
    plot_geanno_vs_genemark(df, args.results_geanno, out_dir=geanno_path)

    plot_geanno_vs_tools_mut_rate(df, df_geanno, out_dir=geanno_path, dpi=args.dpi)
    plot_ram_time_all_tools_overall_dots_plus_geanno(df, df_geanno, out_dir=geanno_path, dpi=args.dpi)

    plot_auc_heatmap_stack_geanno_mesc_vs_aug_abinitio(args.geanno_auc_csv,
        bench_auc_dir=args.csv_dir,
        out_dir=geanno_path,
        dpi=args.dpi
    )

    print("Figures written to", args.fig_dir)

if __name__ == "__main__":
    main()
