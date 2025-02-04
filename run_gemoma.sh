#!/bin/bash

SPECIES_FOLDER="../../species"

GEMOMA_REFERENCE="species_model_gemoma_same_genus.txt"
if [ ! -f "$GEMOMA_REFERENCE" ]; then
    echo "Error: Mapping file '${GEMOMA_REFERENCE}' not found!"
    exit 1
fi
source "$GEMOMA_REFERENCE"

mkdir -p results/GeMoMa
cd results/GeMoMa || exit

# Executar GeneMark-EP+ para todas as espécies
for SPECIES in "$SPECIES_FOLDER"/*; do
    if [ -d "$SPECIES" ]; then

        SPECIES_NAME=$(basename "$SPECIES")
        echo "Processing species: $SPECIES_NAME"
        DNA_FILE="$SPECIES/${SPECIES_NAME}_dna.fa"

        if [ ! -f "$DNA_FILE" ]; then
            echo "DNA file not found for species: ${SPECIES_NAME}. Skipping..."
            continue
        fi

        mkdir -p "$SPECIES_NAME"
        cd "$SPECIES_NAME" || exit 1

        FAR_MODEL=$(eval echo "\$${SPECIES_NAME}_far" | tr -d '[:space:]')
        if [ ! "$FAR_MODEL" = "none" ]; then
            mkdir -p "far"
            cd "far" || exit 1

                start_time=$(date +%s)

                ./../../../../GeMoMa/pipeline.sh mmseqs ../../${DNA_FILE} ../../../../reference_species/${FAR_MODEL}/${FAR_MODEL}_annotation.gff3 ../../../../reference_species/${FAR_MODEL}/${FAR_MODEL}_dna.fa 10 .
            
                end_time=$(date +%s)
                elapsed_time=$((end_time - start_time))

                echo "Process took $elapsed_time seconds." > "${SPECIES_NAME}_far_time.txt"
                echo "Elapsed time for ${SPECIES_NAME}_far: $elapsed_time seconds."
            
            cd ..
        fi

        GENUS_MODEL=$(eval echo "\$${SPECIES_NAME}_genus" | tr -d '[:space:]')
        if [ ! "$GENUS_MODEL" = "none" ]; then
            mkdir -p "far"
            cd "far" || exit 1

                start_time=$(date +%s)

                ./../../../../GeMoMa/pipeline.sh mmseqs ../../${DNA_FILE} ../../../../reference_species/${GENUS_MODEL}/${GENUS_MODEL}_annotation.gff3 ../../../../reference_species/${GENUS_MODEL}/${GENUS_MODEL}_dna.fa 10 .
                            
                end_time=$(date +%s)
                elapsed_time=$((end_time - start_time))

                echo "Process took $elapsed_time seconds." > "${SPECIES_NAME}_genus_time.txt"
                echo "Elapsed time for ${SPECIES_NAME}_genus: $elapsed_time seconds."

            cd ..
        fi

        ORDER_MODEL=$(eval echo "\$${SPECIES_NAME}_order" | tr -d '[:space:]')
        if [ ! "$ORDER_MODEL" = "none" ]; then
            mkdir -p "far"
            cd "far" || exit 1

                start_time=$(date +%s)

                ./../../../../GeMoMa/pipeline.sh mmseqs ../../${DNA_FILE} ../../../../reference_species/${ORDER_MODEL}/${ORDER_MODEL}_annotation.gff3 ../../../../reference_species/${ORDER_MODEL}/${ORDER_MODEL}_dna.fa 10 .
            
                end_time=$(date +%s)
                elapsed_time=$((end_time - start_time))

                echo "Process took $elapsed_time seconds." > "${SPECIES_NAME}_order_time.txt"
                echo "Elapsed time for ${SPECIES_NAME}_order: $elapsed_time seconds."
            
            cd ..
        fi

        cd ..

    fi

done