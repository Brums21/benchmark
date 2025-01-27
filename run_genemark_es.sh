#!/bin/bash

SPECIES_FOLDER="../../species"

mkdir -p results/GeneMark-ES; cd results/GeneMark-ES;

for SPECIES in "$SPECIES_FOLDER"/*; do
    if [ -d "$SPECIES" ]; then
        echo "Species being processed: $SPECIES"

        DNA_FILE="$SPECIES/$(basename "$SPECIES")_dna.fa"

        start_time=$(date +%s)

        ../../gmes_linux_64/gmes_petap.pl --sequence $DNA_FILE --ES

        end_time=$(date +%s)
        elapsed_time=$((end_time - start_time))

        echo "Process took $elapsed_time seconds." > "${SPECIES_NAME}_time.txt"
        echo "Elapsed time for $SPECIES_NAME: $elapsed_time seconds."

    fi
done
