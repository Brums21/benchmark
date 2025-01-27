#!/bin/bash

SPECIES_FOLDER="../../species"

mkdir -p results/GeneMark-ES; cd results/GeneMark-ES;

for SPECIES in "$SPECIES_FOLDER"/*; do
    if [ -d "$SPECIES" ]; then
        echo "Species being processed: $SPECIES"

        DNA_FILE="$SPECIES/$(basename "$SPECIES")_dna.fa"

        ../../gmes_linux_64/gmes_petap.pl --sequence $DNA_FILE --ES

    fi
done
