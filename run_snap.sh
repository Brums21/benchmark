#!/bin/bash

SPECIES_FOLDER="../../species"

mkdir -p results/SNAP
cd results/SNAP || exit 1

for SPECIES in "$SPECIES_FOLDER"/*; do
    if [ -d "$SPECIES" ]; then
        SPECIES_NAME=$(basename "$SPECIES")
        echo "Processing species: $SPECIES_NAME"
        DNA_FILE="$SPECIES/${SPECIES_NAME}_dna.fa"

        mkdir -p "$SPECIES_NAME"
        cd "$SPECIES_NAME" || exit 1

        echo "Running SNAP with arabidopsis thaliana reference species..."
        mkdir -p "arabidopsis_reference"
        cd "arabidopsis_reference" || exit 1

        start_time=$(date +%s)
        ./../../../../SNAP-master/snap A.thaliana.hmm ../../${DNA_FILE}
        end_time=$(date +%s)
        elapsed_time=$((end_time - start_time))

        echo "Process took $elapsed_time seconds." > "${SPECIES_NAME}_a_thaliana_time.txt"
        echo "Elapsed time for ${SPECIES_NAME} in ab initio mode: $elapsed_time seconds."

        cd ..


        echo "Running SNAP with rice (oryza sativa) reference species..."

        mkdir -p "rice_reference"
        cd "rice_reference" || exit 1

        start_time=$(date +%s)
        ./../../../../SNAP-master/snap O.sativa.hmm ../../${DNA_FILE}
        end_time=$(date +%s)
        elapsed_time=$((end_time - start_time))

        echo "Process took $elapsed_time seconds." > "${SPECIES_NAME}_o_sativa_time.txt"
        echo "Elapsed time for ${SPECIES_NAME} in ab initio mode: $elapsed_time seconds."

        cd ..

    fi
done