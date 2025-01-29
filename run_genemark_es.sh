#!/bin/bash

SPECIES_FOLDER="../../species"

mkdir -p results/GeneMark-ES
cd results/GeneMark-ES || exit 1

for SPECIES in "$SPECIES_FOLDER"/*; do
    if [ -d "$SPECIES" ]; then
        SPECIES_NAME=$(basename "$SPECIES")  # Extract species name only
        echo "Species being processed: $SPECIES_NAME"

        mkdir -p "$SPECIES_NAME"
        cd "$SPECIES_NAME" || exit 1

        DNA_FILE="../$SPECIES/${SPECIES_NAME}_dna.fa"

        if [ ! -f "$DNA_FILE" ]; then
            echo "Warning: DNA file $DNA_FILE not found, skipping..."
            cd ..
            continue
        fi

        start_time=$(date +%s)

        ../../../gmes_linux_64/gmes_petap.pl --sequence "$DNA_FILE" --ES --cores 8

        end_time=$(date +%s)
        elapsed_time=$((end_time - start_time))

        echo "Process took $elapsed_time seconds." > "${SPECIES_NAME}_time.txt"
        echo "Elapsed time for $SPECIES_NAME: $elapsed_time seconds."

        cd ..
    fi
done
