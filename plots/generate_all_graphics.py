import argparse
import warnings
import seaborn as sns

from pathlib import Path

from modules.load_save import load_results, load_geanno

from modules.ab_initio_comp import plot_geanno_vs_abinitio_for_model, plot_geanno_vs_genemark

from modules.comparison_tools import export_geanno_models_table_csv

from modules.geanno_plots import export_all_tools_table_csv, export_threshold_curves_and_tripanel, \
                                export_window_step_by_species_mut0

from modules.hints_comp import plot_evidence_species_by_hints_plus_geanno

from modules.mut_rate import export_fixedpoint_species_model, export_tool_by_mutrate_avg_across_species, \
                            export_tool_mutation_drop_csv, plot_geanno_vs_tools_mut_rate, \
                            plot_geanno_vs_tools_mut_rate_per_species

from modules.roc_prc import plot_auc_heatmap_stack_geanno_mesc_vs_aug_abinitio

from modules.time_ram import plot_ram_time_all_tools_by_species_linepairs_plus_geanno, plot_ram_time_all_tools_overall_dots_plus_geanno, \
                            plot_ram_time_summaries_and_plots


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
    geanno_path = args.fig_dir / "geanno"

    geanno_path.mkdir(parents=True, exist_ok=True)

    # GEANNO CONFIGS
    export_threshold_curves_and_tripanel(df_geanno, out_dir=geanno_path, dpi=args.dpi)
    export_window_step_by_species_mut0(df_geanno, out_dir=geanno_path)

    # MODEL TRAINING COMPARISON
    plot_geanno_vs_abinitio_for_model(df, args.results_geanno, model="arabidopsis", out_dir=geanno_path)
    plot_geanno_vs_abinitio_for_model(df, args.results_geanno, model="rice",        out_dir=geanno_path)
    plot_geanno_vs_genemark(df, args.results_geanno, out_dir=geanno_path)

    # COMPARISON WITH EVIDENCE-BASED HINTS
    plot_evidence_species_by_hints_plus_geanno(df, df_geanno, out_dir=geanno_path, dpi=args.dpi)

    # COMPARISON ACROSS DIFFERENT SPECIES
    export_geanno_models_table_csv(df_geanno, out_dir=geanno_path)
    export_all_tools_table_csv(df, df_geanno, out_dir=geanno_path)

    # MUTATION RATES
    plot_geanno_vs_tools_mut_rate_per_species(df, df_geanno, out_dir=geanno_path)
    plot_geanno_vs_tools_mut_rate(df, df_geanno, out_dir=geanno_path, dpi=args.dpi)
    export_fixedpoint_species_model(df_geanno, out_dir=geanno_path)
    export_tool_by_mutrate_avg_across_species(df_geanno, out_dir=geanno_path)
    export_tool_mutation_drop_csv(df, df_geanno, out_dir=geanno_path)

    # TIME AND RAM
    plot_ram_time_summaries_and_plots(df_geanno, out_dir=geanno_path, dpi=args.dpi)
    plot_ram_time_all_tools_overall_dots_plus_geanno(df, df_geanno, out_dir=geanno_path, dpi=args.dpi)
    plot_ram_time_all_tools_by_species_linepairs_plus_geanno(df, df_geanno, out_dir=geanno_path, dpi=args.dpi)
    
    # AUC-ROC AU-PRC - DONE
    plot_auc_heatmap_stack_geanno_mesc_vs_aug_abinitio(args.geanno_auc_csv,
        bench_auc_dir=args.csv_dir,
        out_dir=geanno_path,
        dpi=args.dpi
    )

    print("Figures written to", args.fig_dir)

if __name__ == "__main__":
    main()
