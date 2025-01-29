#!/bin/bash

SPECIES_FOLDER="../../species"

mkdir -p results/GeneMark-ES; cd results/GeneMark-ES;

for SPECIES in "$SPECIES_FOLDER"/*; do
    if [ -d "$SPECIES" ]; then
        echo "Species being processed: $SPECIES"

        mkdir -p $SPECIES; cd $SPECIES;

        DNA_FILE="$SPECIES/$(basename "$SPECIES")_dna.fa"

        start_time=$(date +%s)

        ../../../gmes_linux_64/gmes_petap.pl --sequence $DNA_FILE --ES --cores 8

        end_time=$(date +%s)
        elapsed_time=$((end_time - start_time))

        echo "Process took $elapsed_time seconds." > "../../../${SPECIES}_time.txt"
        echo "Elapsed time for $SPECIES: $elapsed_time seconds."

        cd ..
    fi
done
