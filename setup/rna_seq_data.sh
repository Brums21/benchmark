#!/bin/bash

SPECIES_DIR="${BENCHMARK_DIR}/species/benchmark_species"
HINTS_DIR="${BENCHMARK_DIR}/species/hints"

declare -A RUN_IDS_MAP=(
    ["arabidopsis_thaliana"]="SRR26130646 SRR26130647 SRR13181660"
    ["gossypium_raimondii"]="SRR29754174 SRR9680570 SRR9680571"
    ["manihot_esculenta"]="SRR32309764 SRR32309765 SRR32309766"
    ["oryza_sativa"]="SRR12147606 SRR12147607 SRR12147608"
)

TEMP_FASTA_DIR=${BENCHMARK_DIR}/data

function generateConfigFile() {
    local HINTS_TYPE="$1"
    local SPECIES="$2"
    shift 2
    local RUN_IDS=("$@")
    local HINTS_FILE="${HINTS_DIR}/${SPECIES}_${HINTS_TYPE}.fa"

    if [ -f "$HINTS_FILE" ]; then
        local PROT_PATH=$(realpath "$HINTS_FILE")

        {
            echo "---"
            echo "species: ${SPECIES}"
            echo "genome_path: $TEMP_FASTA_DIR/input.fa"
            echo "rnaseq_sets: ["
            for ((i = 0; i < ${#RUN_IDS[@]}; i++)); do
                if [ "$i" -lt $((${#RUN_IDS[@]} - 1)) ]; then
                    echo "    ${RUN_IDS[$i]},"
                else
                    echo "    ${RUN_IDS[$i]}"
                fi
            done
            echo "]"
            echo "protdb_path: ${PROT_PATH}"
        } > "${SPECIES_DIR}/${SPECIES}/${SPECIES}_${HINTS_TYPE}.yaml"
    else
        echo "Hint file not found for ${SPECIES}_${HINTS_TYPE}. Skipping..."
    fi
}

for SPECIES in "${!RUN_IDS_MAP[@]}"; do
    echo "Creating GeneMark-ETP YAML file for species: $SPECIES"
    
    IFS=' ' read -r -a RUN_IDS <<< "${RUN_IDS_MAP[$SPECIES]}"
    generateConfigFile "genus" "$SPECIES" "${RUN_IDS[@]}"
    generateConfigFile "order" "$SPECIES" "${RUN_IDS[@]}"
    generateConfigFile "far" "$SPECIES" "${RUN_IDS[@]}"
done
