#!/bin/bash

SPECIES_FOLDER="../../species"

MAPPING_FILE="species_model_augustus.txt"
if [ ! -f "$MAPPING_FILE" ]; then
    echo "Error: Mapping file '${MAPPING_FILE}' not found!"
    exit 1
fi
source "$MAPPING_FILE"

mkdir -p results/Augustus
cd results/Augustus || exit 1

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

        AUGUSTUS_MODEL=$(eval echo "\$$SPECIES_NAME" | tr -d '[:space:]')

        # Running Augustus in ab initio mode
        echo "Running Augustus in ab initio mode using model $AUGUSTUS_MODEL"
        mkdir -p "ab_initio"
        cd ab_initio || exit 1

        start_time=$(date +%s)
        ./../../../../Augustus-3.5.0/bin/augustus --species=${AUGUSTUS_MODEL} ../../${DNA_FILE}
        end_time=$(date +%s)
        elapsed_time=$((end_time - start_time))

        echo "Process took $elapsed_time seconds." > "${SPECIES_NAME}_ab_initio_time.txt"
        echo "Elapsed time for ${SPECIES_NAME} in ab initio mode: $elapsed_time seconds."

        cd ..

        echo "Running augustus in evidence based mode, with protein evidence from ProtHint of the same genus using model ${AUGUSTUS_MODEL}..."
        if [ -f "../../../hints/${SPECIES_NAME}_genus.fa" ]; then
            mkdir -p "genus"
            cd "genus" || exit 1

            HINTS_FILE=$(basename "../../../../../hints/${SPECIES_NAME}_genus.fa")

            echo "Running ProtHint for $SPECIES_NAME with hints of the same genus..."
            ./../../../../gmes_linux_64/ProtHint/bin/prothint.py ../../${DNA_FILE} "$HINTS_FILE"

            start_time=$(date +%s)

            echo "Running Augustus for $SPECIES_NAME with hints from same genus..."
            ./../../../../Augustus-3.5.0/bin/augustus --species="$AUGUSTUS_MODEL" --hintsfile="prothint_augustus.gff" ../../${DNA_FILE}

            end_time=$(date +%s)
            elapsed_time=$((end_time - start_time))

            echo "Process took $elapsed_time seconds." > "${SPECIES_NAME}_genus_time.txt"
            echo "Elapsed time for ${SPECIES_NAME}_genus: $elapsed_time seconds."

            cd ..

        fi
        
        
        echo "Running augustus in evidence based mode, with protein evidence from ProtHint of the same order using model ${AUGUSTUS_MODEL}..."
        if [ -f "../../../hints/${SPECIES_NAME}_order.fa" ]; then
            mkdir -p "order"
            cd "order" || exit 1

            HINTS_FILE=$(basename "../../../../hints/${SPECIES_NAME}_order.fa")

            echo "Running ProtHint for ${SPECIES_NAME} with hints of the same order..."
            ./../../../../gmes_linux_64/ProtHint/bin/prothint.py ../../${DNA_FILE} "$HINTS_FILE"

            start_time=$(date +%s)

            echo "Running Augustus for ${SPECIES_NAME} with hints from same order..."
            ./../../../../Augustus-3.5.0/bin/augustus --species="$AUGUSTUS_MODEL" --hintsfile="prothint_augustus.gff" ../../${DNA_FILE}

            end_time=$(date +%s)
            elapsed_time=$((end_time - start_time))

            echo "Process took $elapsed_time seconds." > "${SPECIES_NAME}_order_time.txt"
            echo "Elapsed time for ${SPECIES_NAME}_order: $elapsed_time seconds."

            cd ..

        fi

        echo "Running augustus in evidence based mode, with protein evidence from ProtHint with no close relatives using model ${AUGUSTUS_MODEL}..."
        if [ -f "../../../hints/${SPECIES_NAME}_far.fa" ]; then
            mkdir -p "far"
            cd "far" || exit 1

            HINTS_FILE=$(basename "../../../../hints/${SPECIES_NAME}_far.fa")

            echo "Running ProtHint for ${SPECIES_NAME} with hints of no close relatives..."
            ./../../../../gmes_linux_64/ProtHint/bin/prothint.py "$DNA_FILE" "$HINTS_FILE"

            start_time=$(date +%s)

            echo "Running Augustus for ${SPECIES_NAME} with hints of no close relatives..."
            ./../../../../Augustus-3.5.0/bin/augustus --species="$AUGUSTUS_MODEL" --hintsfile="prothint_augustus.gff" ../../${DNA_FILE}

            end_time=$(date +%s)
            elapsed_time=$((end_time - start_time))

            echo "Process took $elapsed_time seconds." > "${SPECIES_NAME}_far_time.txt"
            echo "Elapsed time for ${SPECIES_NAME}_far: $elapsed_time seconds."

            cd ..

        fi
        cd ..

    fi
done