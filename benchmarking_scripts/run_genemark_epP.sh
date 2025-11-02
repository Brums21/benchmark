#!/bin/bash

if [ -z "$BENCHMARK_DIR" ]; then
    echo "Error: BENCHMARK_DIR is not set. Please source the env.sh file first."
    exit 1
fi

SPECIES_FOLDER="${BENCHMARK_DIR}/species/benchmark_species"
HINTS_FOLDER="${BENCHMARK_DIR}/species/hints"
RESULTS_FOLDER="${BENCHMARK_DIR}/results/tools/GeneMark-EPp"

if [ ! -d ${HINTS_FOLDER} ]; then
    echo "Generating all hints to be used as input."
    cd ${BENCHMARK_DIR}
    ${BENCHMARK_DIR}/setup/hints_generator.sh
else
    echo "Hints already generated. Skipping..."
fi

mkdir -p ${RESULTS_FOLDER}
cd ${RESULTS_FOLDER} || exit 1

runTimedCommand() {
    local CMD="$1"
    local OUTPUT_FILE="$2"
    local TIME_MEM_FILE="$3"

    (/usr/bin/time -f "%e\t%M" bash -c "$CMD") > "$OUTPUT_FILE" 2> "$TIME_MEM_FILE"
}

runGeneMarkEPp() {
    local HINTS_TYPE="$1"
    local SPECIES_NAME="$2"
    local MUTATION_RATE="$3"
    local HINTS_FILE="${HINTS_FOLDER}/${SPECIES_NAME}_${HINTS_TYPE}.fa"

    if [ -f "$HINTS_FILE" ]; then
        mkdir -p "$HINTS_TYPE"
        cd "$HINTS_TYPE" || exit 1

        if [ -f "genemark.gtf" ]; then
            echo "Genemark-EPp already run for species ${SPECIES_NAME}, with mr ${MUTATION_RATE}, with hint type ${HINT_TYPE}"
            cd ..
            return 
        fi

        echo "Running ProtHint for $SPECIES_NAME with $HINTS_TYPE hints..."
        runTimedCommand "${BENCHMARK_DIR}/tools/GeneMark-ETP/bin/gmes/ProtHint/bin/prothint.py \
            --geneMarkGtf ${BENCHMARK_DIR}/results/tools/GeneMark-ES/${SPECIES_NAME}/mr_${MUTATION_RATE}/genemark.gtf \
            ../input.fa \
            ${HINTS_FILE}" \
            "${SPECIES_NAME}_${HINTS_TYPE}_prothint_output.txt" \
            "${SPECIES_NAME}_${HINTS_TYPE}_prothint_time_mem.txt"

        echo "Running GeneMark-EP+ for $SPECIES_NAME with $HINTS_TYPE hints..."
        runTimedCommand "gmes_petap.pl --EP prothint.gff \
            --evidence evidence.gff \
            --seq ../input.fa \
            --cores 10" \
            "${SPECIES_NAME}_${HINTS_TYPE}_genemark_output.txt" \
            "${SPECIES_NAME}_${HINTS_TYPE}_genemark_time_mem.txt"

        cd ..
    else
        echo "Hints file for ${SPECIES_NAME}_${HINTS_TYPE} not found. Skipping..."
    fi
}

for SPECIES in "$SPECIES_FOLDER"/*; do
    [ -d "$SPECIES" ] || continue 

    SPECIES_NAME=$(basename "$SPECIES")
    echo "Processing species: $SPECIES_NAME"
    DNA_FILE="$SPECIES/${SPECIES_NAME}_dna.fa"

    if [ ! -f "$DNA_FILE" ]; then
        echo "DNA file not found for species: $SPECIES_NAME. Skipping..."
        continue
    fi

    mkdir -p "$SPECIES_NAME"
    cd "$SPECIES_NAME" || exit 1

    for MUTATION_RATE in original 0.01 0.04 0.07; do
        mkdir -p "mr_${MUTATION_RATE}"
        cd "mr_${MUTATION_RATE}" || exit 1

        # Aplicar mutation rate quando nao e original
        if [ "$MUTATION_RATE" != "original" ]; then
            gto_fasta_mutate -e $MUTATION_RATE < $DNA_FILE > input.fa
        else
            cp $DNA_FILE input.fa
        fi

        for HINTS_NAME in genus order far; do
            runGeneMarkEPp "${HINTS_NAME}" "$SPECIES_NAME" "$MUTATION_RATE"
        done
        
        rm input.fa

        cd ..

    done

    cd ..
    
done

