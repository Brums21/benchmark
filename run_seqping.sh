#!/bin/bash

SPECIES_FOLDER="../../species"

mkdir -p results/seqping
cd results/seqping || exit 1

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

    mkdir -p "$SPECIES_NAME"
    cd "$SPECIES_NAME" || exit 1

    DNA_FILE="../$SPECIES/${SPECIES_NAME}_dna.fa"

    if [ ! -f "$DNA_FILE" ]; then
        echo "Warning: DNA file $DNA_FILE not found, skipping..."
        cd ..
        continue
    fi

    echo "Running GeneMark-ES for $SPECIES_NAME..."

    runTimedCommand "../../../gmes_linux_64/gmes_petap.pl --sequence $DNA_FILE --ES --cores 10" \
        "${SPECIES_NAME}_genemark_output.txt" \
        "${SPECIES_NAME}_genemark_time_mem.txt"

    cd ..
done