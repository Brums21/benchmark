# Benchmark

This repository contains all the code required to reproduce the benchmarking experiments of GeAnno and several established gene prediction and genome annotation tools, including:
- AUGUSTUS
- GeMoMa
- GeneMark-EP+
- GeneMark-ES
- GeneMark-ETP
- SNAP

The repository provides scripts for downloading benchmark datasets and tools, installing dependencies, running the complete benchmarking pipeline, and compiling or visualising the results.

## 

The benchmark evaluates the accuracy and performance of eukaryotic gene predictors and genome annotators using curated four plant genomes.
All tested tools are executed under equivalent conditions to ensure fair comparison across ab initio and evidence-based modes, and denote precision, recall and F1-score metrics taking gene nucleotide overlap values with reference annotations from Ensembl Plants .
GeAnno, the developed tool, is compared directly against these state-of-the-art predictors.

## System Compatibility

We tested this benchmark on a computer with the following specifications:

| Element          | Specification                                                 |
|------------------|---------------------------------------------------------------|
| CPU              | Intel Xeon E7320 @ 2.13 GHz, 16 cores (4 sockets)             |
| RAM              | 256 GB                                                        |
| Operating System | Ubuntu 22.04.4 LTS (Jammy Jellyfish), kernel 6.8.0-60-generic |
| Architecture     | x86_64                                                        |

The benchmark was also tested under Windows Subsystem for Linux (WSL) using the same OS (Ubuntu 22.04).

## Pre-requirements:

Before running the setup, ensure that the following packages are available:

- Python3 (with pip)
- g++ compiler
- Java (version 11)

All other dependencies (Perl modules, C/C++ libraries, binaries, etc.) are automatically downloaded and configured by running:

```bash
./setup/install_dependencies.sh
```

>**Note**: No `sudo` privileges are required. All dependencies are installed locally within `${BENCHMARK_DIR}/libs/`.

## Installation

### Set the benchmark environment variable

Navigate to the root directory of this repository (where this README.md is located) and run:

```bash
echo "export BENCHMARK_DIR=$(pwd)" >> env.sh
source env.sh
```

This command defines an environment variable used by all scripts to locate dependencies, data, and configuration files.
If `BENCHMARK_DIR` is not set, most scripts will fail.

### Install all tools and required packages

By default, the `./setup.sh` script should be able to install all missing dependencies, tools, benchmarking species and other necessary data. This script runs all scripts present in the `setup/` directory.

| Script | Purpose |
|--------|---------|
| get_species_info.sh | Downloads all testing and reference species used across tools. |
| hints_generator.sh | Downloads protein evidence sets (used by AUGUSTUS, GeneMark-EP+, GeneMark-ETP). |
| rna_seq_data.sh | Downloads RNA-seq data (used by GeneMark-ETP). |
| get_tools.sh | Downloads all benchmarked tools into the `tools/` directory. |
| install_dependencies.sh | Installs and configures tool dependencies (BioPerl, mmseqs, Zlib, etc.).|

In order to run the `install_dependencies.sh` script, it is necessary to have all tools installed first (using `get_tools.sh`).

> You only need to grant permission to `setup.sh`. It automatically handles permissions for all scripts under setup/.

## Running the benchmark

All benchmarks are launched through the scripts inside `benchmarking_scripts/`

| Script | Description |
|--------|---------|
| run_all.sh            | Executes all benchmark runs sequentially. |
| run_augustus.sh       | Runs AUGUSTUS experiments (ab initio and evidence-based). |
| run_geanno.sh         | Runs experiments for the GeAnno tool. |
| run_gemoma.sh         | Runs GeMoMa experiments. |
| run_genemark_epP.sh   | Runs GeneMark-EP+ experiments. |
| run_genemark_es.sh    | Runs GeneMark-ES experiments. |
| run_genemark_etp.sh   | Runs GeneMark-ETP experiments. |
| run_snap.sh           | Runs SNAP experiments. |

Example:

```bash
./benchmarking_scripts/run_augustus.sh
```

### Results structure

Results are organised by tool under `results/tools/<tool_name>/`.
Each tool follows its own output naming convention, shown below:

| Tool             | Output File                               |
| :--------------- | :---------------------------------------- |
| **AUGUSTUS**     | `augustus.gtf`                            |
| **GeAnno**       | `output_<window>_<step>_<threshold>.gff3` |
| **GeneMark-ES**  | `genemark.gtf`                            |
| **GeneMark-EP+** | `genemark.gtf`                            |
| **GeneMark-ETP** | `genemark.gtf`                            |
| **GeMoMa**       | `final_annotation.gff`                    |
| **SNAP**         | `output.gff`                              |



#### GeAnno results

```
results/tools/GeAnno/<mutation_rate>/<model>/<species>/output/output_<window_size>_<step_size>_<threshold>.gff3
```

where `model` can either be `a_thaliana_model`, `a_thaliana_model_PCA`, `o_sativa_model`, `o_sativa_model_PCA`, `genemark_model`, `genemark_model_PCA` or `m_esculenta_model_PCA`. Refer to GeAnno's documentation for more information. 

#### GeneMark-ES results

```
results/tools/GeneMark-ES/<species>/mr_<mutation_rate>/genemark.gtf
```

#### SNAP results

```
results/tools/SNAP/<testing_species>/<model_species>/mr_<mutation_rate>/output.gff
```

where `<model_species>` can either be `arabidopsis_reference` or `rice_reference`, corresponding to *A. thaliana* and *O. sativa* SNAP pre-trained models available.


#### AUGUSTUS, GeneMark-EP+, GeneMark-ETP and GeMoMa results

```
results/tools/augustus/<testing_species>/mr_<mutation_rate>/<hints_type>/<output_file>
```

where <hints_type> can be `genus`, `order` or `far` (meaning hints/references from the same genus, same order or no close relation as the species being evaluated were used), or additionally, in the case of AUGUSTUS `abinitio` (meaning it was run without the use of extrinsic evidence). <output_file> is as described in the table above.

## Compiling results

Before computing metrics, outputs are standardised to the GFF3 format.
This is handled automatically by running:

In order to obtain relevant metrics, some adjusting to the outputs of other tools is necessary. We standarize all outputs to GFF3 files by running:

```
./metrics/extract_all_values.sh
```

This script converts tool outputs into GFF3 (via AGAT and GenomeTools), cleans and merges annotations, computes the designated metrics using the compiled binary obtain_metrics, and writes results as CSV files to `results/compiled/`. 

GeAnno's own benchmark metrics are stored separately in:

```
results/GeAnno/
```

## Plotting and Figure Generation

All figures and summary plots used in the paper and dissertation can be regenerated using:

```bash
cd ${BENCHMARK_DIR}/plots

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

python3 generate_all_graphics.py \
        --csv_dir ${BENCHMARK_DIR}/results/compiled/ \
        --fig_dir <output_path_to_place_figures> \
        --results_geanno ${BENCHMARK_DIR}/results/GeAnno \
        --geanno_auc_csv ${BENCHMARK_DIR}/results/GeAnno/auc_csv/geanno_auc.csv

```

