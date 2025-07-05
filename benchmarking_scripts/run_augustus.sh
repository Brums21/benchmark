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
    local MUTATION_RATE="$4"
    local HINTS_FILE="../../../../../hints/${SPECIES_NAME}_${HINTS_TYPE}.fa"

    if [ -f "$HINTS_FILE" ]; then
        echo "Checking if prothint augustus file already exists in GeneMark-EPp results."
        if [ -f "../../../../../results/GeneMark-EPp/${SPECIES_NAME}/mr_${MUTATION_RATE}/${HINTS_TYPE}/prothint_augustus.gff" ]; then
            echo "Prothint file already exists, no need to compute again."
            cp ../../../../../results/GeneMark-EPp/${SPECIES_NAME}/mr_${MUTATION_RATE}/${HINTS_TYPE}/prothint_augustus.gff .
        else
            echo "Prothint file not found in Genemark results. Running ProtHint for ${SPECIES_NAME} with hints: $HINTS_TYPE"
            runTimedCommand "./../../../../../tools/gmes_linux_64/ProtHint/bin/prothint.py $DNA_FILE $HINTS_FILE" \
            "${SPECIES_NAME}_${HINTS_TYPE}_prothint_output.txt" "${SPECIES_NAME}_${HINTS_TYPE}_prothint_time_mem.txt"
        fi

        return 0
    else
        echo "No hint file for this species and hint type. Skipping..."
        return 1
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
        gto_fasta_mutate -e $MUTATION_RATE < ../../../$DNA_FILE > input.fa
    else
        cp ../../../$DNA_FILE input.fa
    fi

    if [ -f "augustus.gtf" ]; then
        echo "Augustus has already been run for species ${SPECIES_NAME}, in the ${MODE} model and mutation ${MUTATION_RATE}. Skipping..."
        cd ..
        return 
    fi

    if [ "$MODE" != "abinitio" ]; then
        if runProthint "$MODE" "$SPECIES_NAME" "input.fa" "$MUTATION_RATE"; then
            HINTS_OPTION="--hintsfile=prothint_augustus.gff --extrinsicCfgFile=../../../../../benchmark/benchmarking_scripts/extrinsic.cfg"
        else
            cd ..
            return
        fi
    fi

    echo "Running AUGUSTUS ($MODE) for ${SPECIES_NAME} using model ${AUGUSTUS_MODEL}..."
    runTimedCommand "./../../../../../tools/Augustus-3.5.0/bin/augustus --outfile=augustus.gtf --species=$AUGUSTUS_MODEL $HINTS_OPTION input.fa" \
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

    for MUTATION_RATE in original 0.01 0.04 0.07; do
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
