#!/bin/bash

SPECIES_FOLDER="../../species"
MAPPING_FILE="species_model_augustus.txt"

if [ ! -f "$MAPPING_FILE" ]; then
    echo "Error: Mapping file '${MAPPING_FILE}' not found!"
    exit 1
fi

source "$MAPPING_FILE"

mkdir -p results/Augustus
cd results/Augustus || exit 1

runTimedCommand() {
    local CMD="$1"
    local OUTPUT_FILE="$2"
    local TIME_MEM_FILE="$3"

    (/bin/time -f "%e\t%M" bash -c "$CMD") > "$OUTPUT_FILE" 2> "$TIME_MEM_FILE"
}

runProthint() {
    local HINTS_TYPE="$1"
    local SPECIES_NAME="$2"
    local DNA_FILE="$3"
    local HINTS_FILE="../../../hints/${SPECIES_NAME}_${HINTS_TYPE}.fa"

    if [ -f "$HINTS_FILE" ]; then
        echo "Running ProtHint for ${SPECIES_NAME} with hints: $HINTS_TYPE"
        runTimedCommand "./../../../../gmes_linux_64/ProtHint/bin/prothint.py $DNA_FILE $HINTS_FILE" \
            "${SPECIES_NAME}_${HINTS_TYPE}_prothint_output.txt" "${SPECIES_NAME}_${HINTS_TYPE}_prothint_time_mem.txt"
    fi
}

runAUGUSTUS() {
    local MODE="$1"  # abinitio, genus, order, far
    local SPECIES_NAME="$2"
    local DNA_FILE="$3"
    local AUGUSTUS_MODEL="$4"
    local HINTS_OPTION=""

    mkdir -p "$MODE"
    cd "$MODE" || exit 1

    if [ "$MODE" != "abinitio" ]; then
        runProthint "$MODE" "$SPECIES_NAME" "$DNA_FILE"
        HINTS_OPTION="--hintsfile=prothint_augustus.gff"
    fi

    echo "Running AUGUSTUS ($MODE) for ${SPECIES_NAME} using model ${AUGUSTUS_MODEL}..."
    runTimedCommand "./../../../../Augustus-3.5.0/bin/augustus --species=$AUGUSTUS_MODEL $HINTS_OPTION ../../$DNA_FILE" \
        "${SPECIES_NAME}_${MODE}_augustus_output.txt" "${SPECIES_NAME}_${MODE}_augustus_time_mem.txt"
    cd ..
}

for SPECIES in "$SPECIES_FOLDER"/*; do
    [ -d "$SPECIES" ] || continue

    SPECIES_NAME=$(basename "$SPECIES")
    DNA_FILE="$SPECIES/${SPECIES_NAME}_dna.fa"

    if [ ! -f "$DNA_FILE" ]; then
        echo "DNA file not found for ${SPECIES_NAME}. Skipping..."
        continue
    fi

    echo "Processing species: $SPECIES_NAME"
    mkdir -p "$SPECIES_NAME"
    cd "$SPECIES_NAME" || exit 1

    AUGUSTUS_MODEL=$(eval echo "\$$SPECIES_NAME" | tr -d '[:space:]')

    runAUGUSTUS "abinitio" "$SPECIES_NAME" "$DNA_FILE" "$AUGUSTUS_MODEL"
    runAUGUSTUS "genus" "$SPECIES_NAME" "$DNA_FILE" "$AUGUSTUS_MODEL"
    runAUGUSTUS "order" "$SPECIES_NAME" "$DNA_FILE" "$AUGUSTUS_MODEL"
    runAUGUSTUS "far" "$SPECIES_NAME" "$DNA_FILE" "$AUGUSTUS_MODEL"

    cd ..
done
