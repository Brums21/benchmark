#!/bin/bash

SPECIES_FOLDER="../../species"

mkdir -p ../results/GeneMark-ES
cd ../results/GeneMark-ES || exit 1

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

    mkdir -p "$SPECIES_NAME"
    cd "$SPECIES_NAME" || exit 1

    DNA_FILE="../$SPECIES/${SPECIES_NAME}_dna.fa"

    if [ ! -f "$DNA_FILE" ]; then
        echo "Warning: DNA file $DNA_FILE not found, skipping..."
        cd ..
        continue
    fi

    echo "Running GeneMark-ES for $SPECIES_NAME..."

    for MUTATION_RATE in original 0.01 0.04 0.07; do
        mkdir -p "mr_${MUTATION_RATE}"
        cd "mr_${MUTATION_RATE}" || exit 1

        if [ "$MUTATION_RATE" != "original" ]; then
            #AlcoR simulation -fs 0:0:0:42:$MUTATION_RATE:0:0:../../../$DNA_FILE > input.fa
            gto_fasta_mutate -e $MUTATION_RATE < ../../../$DNA_FILE > input.fa
        else
            cp ../$DNA_FILE input.fa
        fi

        runTimedCommand "../../../../tools/gmes_linux_64/gmes_petap.pl --sequence input.fa --ES --cores 10" \
            "${SPECIES_NAME}_genemark_output.txt" \
            "${SPECIES_NAME}_genemark_time_mem.txt"

        rm input.fa

        cd ..

    done

    cd ..
done
