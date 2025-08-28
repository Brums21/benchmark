#!/bin/bash

TEMP_FASTA_DIR="${BENCHMARK_DIR}/temp_data"
SPECIES_FOLDER="${BENCHMARK_DIR}/species/benchmark_species"
RESULTS_FOLDER="${BENCHMARK_DIR}/results/tools/GeneMark-ETP"

mkdir -p ${TEMP_FASTA_DIR}

mkdir -p ${RESULTS_FOLDER}
cd ${RESULTS_FOLDER} || exit 1

runTimedCommand() {
    local CMD="$1"
    local OUTPUT_FILE="$2"
    local TIME_MEM_FILE="$3"

    (/bin/time -f "%e\t%M" bash -c "$CMD") > "$OUTPUT_FILE" 2> "$TIME_MEM_FILE"
}

runGeneMarkETP() {
    local HINTS_TYPE="$1"
    local SPECIES_NAME="$2"
    local MUTATION_RATE="$3"
    local HINTS_FILE="${SPECIES_FOLDER}/${SPECIES_NAME}/${SPECIES_NAME}_${HINTS_TYPE}.yaml"

    DNA_FILE="${SPECIES_FOLDER}/${SPECIES_NAME}/${SPECIES_NAME}_dna.fa"
    if [ ! -f "$DNA_FILE" ]; then
        echo "DNA file not found for species: ${SPECIES_NAME}. Skipping..."
        return 1
    fi

    if [ -f "$HINTS_FILE" ]; then
        mkdir -p "$HINTS_TYPE"
        cd "$HINTS_TYPE" || exit 1

        if [ -f "genemark.gtf" ]; then
            echo "Genemark was already run for this species (${SPECIES_NAME}), hint type (${HINTS_TYPE}) and mutation rate (${MUTATION_RATE}). Skipping..."
            cd ..
            return 1
        fi

        if [ "$MUTATION_RATE" != "original" ]; then
            gto_fasta_mutate -e $MUTATION_RATE < $DNA_FILE > ${TEMP_FASTA_DIR}/input.fa
        else
            cp $DNA_FILE ${TEMP_FASTA_DIR}/input.fa
        fi

        echo "Running GeneMark-ETP for $SPECIES_NAME with $HINTS_TYPE hints..."
        runTimedCommand "${BENCHMARK_DIR}/tools/GeneMark-ETP-main/bin/gmetp.pl --cores 10 --cfg ${HINTS_FILE}" \
            "${SPECIES_NAME}_${HINTS_TYPE}_genemark_output.txt" \
            "${SPECIES_NAME}_${HINTS_TYPE}_genemark_time_mem.txt"

        # Eliminar ficheiros temporarios e pesados do Genemark para poupar armazenamento
        rm -r data/
        rm -r rnaseq/

        cd ..
    else
        echo "Hints file for ${SPECIES_NAME}_${HINTS_TYPE} not found. Skipping..."
    fi
}

for SPECIES in "$SPECIES_FOLDER"/*; do
    [ -d "$SPECIES" ] || continue 

    SPECIES_NAME=$(basename "$SPECIES")
    echo "Processing species: $SPECIES_NAME"
    
    mkdir -p "$SPECIES_NAME"
    cd "$SPECIES_NAME" || exit 1

    for MUTATION_RATE in original 0.01 0.04 0.07; do
        mkdir -p "mr_${MUTATION_RATE}"
        cd "mr_${MUTATION_RATE}" || exit 1

        for HINT_TYPE in genus order far; do
            runGeneMarkETP "${HINT_TYPE}" "${SPECIES_NAME}" "${MUTATION_RATE}"
        done 

        cd ..
    done
    
    cd ..
done

rm -r ${TEMP_FASTA_DIR}

cd ${BENCHMARK_DIR}
