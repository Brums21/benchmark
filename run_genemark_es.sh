#!/bin/bash

$SPECIES_FOLDER = "./../species"

mkdir results/GeneMark-ES

cd gmes_linux_64
# initialize GeneMark-ES


for SPECIES in "$SPECIES_FOLDER"/*; do
    if [ -d "$SPECIES" ]; then
        echo "Species being processed: $SPECIES"

        DNA_FILE="$SPECIES/$SPECIES_dna.fa"

    fi
done