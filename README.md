# Benchmark

This repository contains the code necessary to compile all tests performed for the benchmark of GeAnno and other gene predictors/genome annotators, including:
- AUGUSTUS
- GeMoMa
- GeneMark-EP+
- GeneMark-ES
- GeneMark-ETP
- SNAP

We provide the code used to download the testing sets, download benchmarking tools and their dependencies, perform the tests made, as well as configurations used, and plotting relevant results.

## Compatibility

| Element          | Specification                                                 |
|------------------|---------------------------------------------------------------|
| CPU              | Intel Xeon E7320 @ 2.13 GHz, 16 cores (4 sockets)             |
| RAM              | 256 GB                                                        |
| OS               | Ubuntu 22.04.4 LTS (Jammy Jellyfish), kernel 6.8.0-60-generic |
| Arch.            | x86_64                                                        |

## Pre-requirements:

- Python3 (with pip)
- g++ compiler
- Java (version 11)

All remaining dependencies were downloaded and configured by running the  `./setup/install_dependencies.sh` script. 

## Installation

### Set up environment variable

Navigate to the path where this README.md file is and perform the following steps:

```bash
echo "export BENCHMARK_DIR=$(pwd)" >> env.sh
source env.sh
```

This variable is used to locate scripts, dependencies, and other necessary configurations. Not having this variable set, most scripts will fail, since they are dependent on it.

### Install all tools and required packages

By default, the `./setup.sh` script should be able to install all missing dependencies, tools, benchmarking species and other necessary data. This script runs all scripts present in the `setup/` directory.

We explain what each script does:
    - `get_species_info.sh`: download all testing species (used across all tools) and reference species (used by GeMoMa only).
    - `hints_generator.sh`: download protein evidence sets (used by AUGUSTUS, GeneMark-EP+, and GeneMark-ETP).
    - `rna_seq_data.sh`: downloads necessary RNA seq data (used by GeneMark-ETP).
    - `get_tools.sh`: downloads all benchmarked tools and places them in the `tools/` directory.
    - `install_dependencies.sh`: download and installs all requirements necessary for the downloaded tools to function. 

In order to run the `install_dependencies.sh` script, it is necessary to have all tools installed first (using `get_tools.sh`).

> Note: you need to give permission to the scripts in order to be able to run them with the `chmod +x <script>` command.

## Runing the benchmark



