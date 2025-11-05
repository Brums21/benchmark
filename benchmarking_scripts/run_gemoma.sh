#!/bin/bash

if [ -z "$BENCHMARK_DIR" ]; then
    echo "Error: BENCHMARK_DIR is not set. Please source the env.sh file first."
    exit 1
fi

SPECIES_FOLDER="${BENCHMARK_DIR}/species/benchmark_species"
REFERENCE_SPECIES_FOLDER="${BENCHMARK_DIR}/species/reference_species"

GEMOMA_REFERENCE="${BENCHMARK_DIR}/config/species_model_gemoma.txt"
RESULTS_FOLDER="${BENCHMARK_DIR}/results/tools/GeMoMa"

if [ ! -f "$GEMOMA_REFERENCE" ]; then
    echo "Error: Mapping file species_model_gemoma.txt in '${GEMOMA_REFERENCE}' not found!"
    exit 1
fi
source "$GEMOMA_REFERENCE"

mkdir -p ${RESULTS_FOLDER}
cd ${RESULTS_FOLDER} || exit 1

runGeMoMa() {
    local HINTS_TYPE="$1"
    local SPECIES_NAME="$2"
    local MODEL_NAME="$3"
    local MUTATION_RATE="$4"

    CURRENT_RESULTS_FOLDER="${RESULTS_FOLDER}/${SPECIES_NAME}/mr_${MUTATION_RATE}"
    CURRENT_DIR="${CURRENT_RESULTS_FOLDER}/${HINTS_TYPE}"
    CURRENT_DIR_METRICS="${CURRENT_DIR}/${SPECIES_NAME}_${HINTS_TYPE}"
    CURRENT_REFERENCE_SPECIES="${REFERENCE_SPECIES_FOLDER}/${MODEL_NAME}/${MODEL_NAME}"

    # verificar se os resultados ainda nao foram executados
    if [ -f "${CURRENT_DIR}/final_annotation.gff" ]; then
        echo "Skipping GeMoMa for ${SPECIES_NAME} with ${HINTS_TYPE} for mutation rate with value ${MUTATION_RATE}..."
        return
    fi

    if [ ! "$MODEL_NAME" = "none" ]; then
        mkdir -p "$HINTS_TYPE"
        cd "$HINTS_TYPE" || exit 1

        echo "Running GeMoMa for ${SPECIES_NAME} with ${HINTS_TYPE} reference model ${MODEL_NAME}..."
        cd ${BENCHMARK_DIR}/tools/GeMoMa/

        /bin/time -f "%e\t%M" \
            ./pipeline.sh mmseqs \
            ${CURRENT_RESULTS_FOLDER}/input.fa \
            ${CURRENT_REFERENCE_SPECIES}_annotation.gff3 \
            ${CURRENT_REFERENCE_SPECIES}_dna.fa \
            10 \
            ${CURRENT_DIR} \
            > "${CURRENT_DIR_METRICS}_output.txt" \
            2> "${CURRENT_DIR_METRICS}_time_mem.txt"

        cd "$(dirname "$CURRENT_DIR")"
        
    fi
}

for SPECIES in "$SPECIES_FOLDER"/*; do
    [ -d "$SPECIES" ] || continue

    SPECIES_NAME=$(basename "$SPECIES")
    echo "Processing species: $SPECIES_NAME"
    DNA_FILE="$SPECIES/${SPECIES_NAME}_dna.fa"

    if [ ! -f "$DNA_FILE" ]; then
        echo "DNA file not found for species: ${SPECIES_NAME}. Skipping..."
        continue
    fi

    mkdir -p "$SPECIES_NAME"
    cd "$SPECIES_NAME" || exit 1

    for HINTS_NAME in far genus order; do

        CURRENT_MODEL=$(eval echo "\$${SPECIES_NAME}_${HINTS_NAME}" | tr -d '[:space:]')

        for MUTATION_RATE in original 0.01 0.04 0.07; do

            mkdir -p "mr_${MUTATION_RATE}"
            cd "mr_${MUTATION_RATE}" || exit 1
            echo "Current mutation rate: ${MUTATION_RATE}"

            if [ "$MUTATION_RATE" != "original" ]; then
                gto_fasta_mutate -e $MUTATION_RATE < $DNA_FILE > input.fa
            else
                cp $DNA_FILE input.fa
            fi

            runGeMoMa "$HINTS_NAME" "$SPECIES_NAME" "$CURRENT_MODEL" "$MUTATION_RATE"

            rm input.fa

            cd ..

        done
    done

    cd ..
done
