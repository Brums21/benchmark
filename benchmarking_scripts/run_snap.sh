#!/bin/bash

SPECIES_FOLDER="${BENCHMARK_DIR}/species/benchmark_species"
RESULTS_FOLDER="${BENCHMARK_DIR}/results/tools/SNAP"


mkdir -p ${RESULTS_FOLDER}
cd ${RESULTS_FOLDER} || exit 1

runTimedCommand() {
    local CMD="$1"
    local OUTPUT_FILE="$2"
    local TIME_MEM_FILE="$3"

    (/bin/time -f "%e\t%M" bash -c "$CMD") > "$OUTPUT_FILE" 2> "$TIME_MEM_FILE"
}

for SPECIES in "$SPECIES_FOLDER"/*; do
    [ -d "$SPECIES" ] || continue 

    SPECIES_NAME=$(basename "$SPECIES")
    echo "Processing species: $SPECIES_NAME"
    DNA_FILE="$SPECIES/${SPECIES_NAME}_dna.fa"

    mkdir -p "$SPECIES_NAME"
    cd "$SPECIES_NAME" || exit 1

    declare -A REFS=(
        ["arabidopsis_reference"]="A.thaliana.hmm"
        ["rice_reference"]="O.sativa.hmm"
    )

    for REF_LABEL in "${!REFS[@]}"; do
        HMM_MODEL_FILE=${REFS[$REF_LABEL]}

        echo "Running SNAP with ${REF_LABEL} reference species..."
        mkdir -p "${REF_LABEL}"
        cd "${REF_LABEL}" || exit 1

        for MUTATION_RATE in original 0.01 0.04 0.07; do
            mkdir -p "mr_${MUTATION_RATE}"
            cd "mr_${MUTATION_RATE}" || exit 1

            if [ -f "output.gff" ]; then
                echo "Already run for species ${SPECIES_NAME} with mutation rate ${MUTATION_RATE}. Skipping..."
                cd ..
                continue
            fi

            if [ "$MUTATION_RATE" != "original" ]; then
                gto_fasta_mutate -e $MUTATION_RATE < $DNA_FILE > input.fa
            else
                cp $DNA_FILE input.fa
            fi

            runTimedCommand "${BENCHMARK_DIR}/tools/SNAP-master/snap -gff ${HMM_MODEL_FILE} input.fa > output.gff" \
                "${SPECIES_NAME}_a_thaliana_output.txt" \
                "${SPECIES_NAME}_a_thaliana_time_mem.txt"

            rm input.fa

            cd ..
        
        done

        cd .. 
    done

    cd ..
done
