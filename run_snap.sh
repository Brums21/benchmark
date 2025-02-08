#!/bin/bash

SPECIES_FOLDER="../../species"

mkdir -p results/SNAP
cd results/SNAP || exit 1

runTimedCommand() {
    local CMD="$1"
    local OUTPUT_FILE="$2"
    local TIME_MEM_FILE="$3"

    (/usr/bin/time -f "%e\t%M" bash -c "$CMD") > "$OUTPUT_FILE" 2> "$TIME_MEM_FILE"
}

for SPECIES in "$SPECIES_FOLDER"/*; do
    [ -d "$SPECIES" ] || continue 

    SPECIES_NAME=$(basename "$SPECIES")
    echo "Processing species: $SPECIES_NAME"
    DNA_FILE="$SPECIES/${SPECIES_NAME}_dna.fa"

    mkdir -p "$SPECIES_NAME"
    cd "$SPECIES_NAME" || exit 1

    echo "Running SNAP with Arabidopsis thaliana reference species..."
    mkdir -p "arabidopsis_reference"
    cd "arabidopsis_reference" || exit 1

    runTimedCommand "./../../../../SNAP-master/snap A.thaliana.hmm ../../${DNA_FILE}" \
        "${SPECIES_NAME}_a_thaliana_output.txt" \
        "${SPECIES_NAME}_a_thaliana_time_mem.txt"

    cd ..

    echo "Running SNAP with rice (Oryza sativa) reference species..."
    mkdir -p "rice_reference"
    cd "rice_reference" || exit 1

    runTimedCommand "./../../../../SNAP-master/snap O.sativa.hmm ../../${DNA_FILE}" \
        "${SPECIES_NAME}_o_sativa_output.txt" \
        "${SPECIES_NAME}_o_sativa_time_mem.txt"

    cd ..
done
