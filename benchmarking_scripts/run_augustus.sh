#!/bin/bash

SPECIES_FOLDER="../../species"
MAPPING_FILE="species_model_augustus.txt"

if [ ! -f "$MAPPING_FILE" ]; then
    echo "Error: Mapping file '${MAPPING_FILE}' not found!"
    exit 1
fi

source "$MAPPING_FILE"

mkdir -p ../results/augustus
cd ../results/augustus || exit 1

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
    local HINTS_FILE="../../../../../hints/${SPECIES_NAME}_${HINTS_TYPE}.fa"

    if [ -f "$HINTS_FILE" ]; then
        echo "Running ProtHint for ${SPECIES_NAME} with hints: $HINTS_TYPE"
        runTimedCommand "./../../../../../tools/gmes_linux_64/ProtHint/bin/prothint.py $DNA_FILE $HINTS_FILE" \
            "${SPECIES_NAME}_${HINTS_TYPE}_prothint_output.txt" "${SPECIES_NAME}_${HINTS_TYPE}_prothint_time_mem.txt"
    fi
}

runAUGUSTUS() {
    local MODE="$1"  # abinitio, genus, order, far
    local SPECIES_NAME="$2"
    local DNA_FILE="$3"
    local AUGUSTUS_MODEL="$4"
    local MUTATION_RATE="$5" # original, 0.01, 0.03, 0.07
    local HINTS_OPTION=""

    mkdir -p "$MODE"
    cd "$MODE" || exit 1

    if [ "$MUTATION_RATE" != "original" ]; then
        #AlcoR simulation -fs 0:0:0:42:$MUTATION_RATE:0:0:../../../$DNA_FILE > input.fa
        gt seqmutate -width 60 -rate $MUTATION_RATE ../../../$DNA_FILE > input.fa

        # remove the temporary files from the genome tools mutation
        rm ${SPECIES_NAME}_dna.fa.des ${SPECIES_NAME}_dna.fa.esq ${SPECIES_NAME}_dna.fa.md5 ${SPECIES_NAME}_dna.fa.ois ${SPECIES_NAME}_dna.fa.sds
    else
        cp ../../../$DNA_FILE input.fa
    fi

    if [ "$MODE" != "abinitio" ]; then
        runProthint "$MODE" "$SPECIES_NAME" "input.fa"
        HINTS_OPTION="--hintsfile=prothint_augustus.gff"
    fi

    echo "Running AUGUSTUS ($MODE) for ${SPECIES_NAME} using model ${AUGUSTUS_MODEL}..."
    runTimedCommand "./../../../../../tools/Augustus-3.5.0/bin/augustus --species=$AUGUSTUS_MODEL $HINTS_OPTION input.fa" \
        "${SPECIES_NAME}_${MODE}_augustus_output.txt" "${SPECIES_NAME}_${MODE}_augustus_time_mem.txt"
    
    rm input.fa
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

    for MUTATION_RATE in original 1 4 7; do
        mkdir -p "mr_${MUTATION_RATE}"
        cd "mr_${MUTATION_RATE}" || exit 1

        runAUGUSTUS "abinitio" "$SPECIES_NAME" "$DNA_FILE" "$AUGUSTUS_MODEL" "$MUTATION_RATE"
        runAUGUSTUS "genus" "$SPECIES_NAME" "$DNA_FILE" "$AUGUSTUS_MODEL" "$MUTATION_RATE"
        runAUGUSTUS "order" "$SPECIES_NAME" "$DNA_FILE" "$AUGUSTUS_MODEL" "$MUTATION_RATE"
        runAUGUSTUS "far" "$SPECIES_NAME" "$DNA_FILE" "$AUGUSTUS_MODEL" "$MUTATION_RATE"

        cd ..

    done
    
    cd ..
done
