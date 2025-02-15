#!/bin/bash

SPECIES_FOLDER="../../species"

mkdir -p results/GeneMark-ETP
cd results/GeneMark-ETP || exit 1

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
    local HINTS_FILE="../../../../species/${SPECIES_NAME}/${SPECIES_NAME}_${HINTS_TYPE}.yaml"

    if [ "$MUTATION_RATE" != "original" ]; then
        AlcoR simulation -fs 0:0:0:42:$MUTATION_RATE:0:0:../../../../$DNA_FILE > input.fa
    else
        cp ../../../../$DNA_FILE input.fa
    fi

    if [ -f "$HINTS_FILE" ]; then
        mkdir -p "$HINTS_TYPE"
        cd "$HINTS_TYPE" || exit 1

        echo "Running GeneMark-ETP for $SPECIES_NAME with $HINTS_TYPE hints..."
        runTimedCommand "../../../../../GeneMark-ETP/bin/gmetp.pl --cores 10 --cfg ../${HINTS_FILE}" \
            "${SPECIES_NAME}_${HINTS_TYPE}_genemark_output.txt" \
            "${SPECIES_NAME}_${HINTS_TYPE}_genemark_time_mem.txt"

        cd ..
    else
        echo "Hints file for ${SPECIES_NAME}_${HINTS_TYPE} not found. Skipping..."
    fi

    rm input.fa
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

        runGeneMarkETP "genus" "$SPECIES_NAME" "$MUTATION_RATE"
        runGeneMarkETP "order" "$SPECIES_NAME" "$MUTATION_RATE"
        runGeneMarkETP "far" "$SPECIES_NAME" "$MUTATION_RATE"

        cd ..
    done
    
    cd ..
done

cd ../..
