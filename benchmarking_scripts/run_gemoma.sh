#!/bin/bash

SPECIES_FOLDER="../../species"
GEMOMA_REFERENCE="species_model_gemoma.txt"

if [ ! -f "$GEMOMA_REFERENCE" ]; then
    echo "Error: Mapping file '${GEMOMA_REFERENCE}' not found!"
    exit 1
fi
source "$GEMOMA_REFERENCE"

mkdir -p ../results/GeMoMa
cd ../results/GeMoMa || exit 1

runGeMoMa() {
    local HINTS_TYPE="$1"
    local SPECIES_NAME="$2"
    local MODEL_NAME="$3"
    local MUTATION_RATE="$4"

    # verificar se os resultados ainda nao foram executados:
    if [ -f "../../../../results/GeMoMa/${SPECIES_NAME}/mr_${MUTATION_RATE}/${HINTS_TYPE}/final_annotation.gff" ]; then
        echo "Skipping GeMoMa for ${SPECIES_NAME} with ${HINTS_TYPE} for mutation rate with value ${MUTATION_RATE}..."
        return
    fi

    if [ ! "$MODEL_NAME" = "none" ]; then
        mkdir -p "$HINTS_TYPE"
        cd "$HINTS_TYPE" || exit 1

        echo "Running GeMoMa for ${SPECIES_NAME} with ${HINTS_TYPE} reference model ${MODEL_NAME}..."
        cd ../../../../../tools/GeMoMa/

        /bin/time -f "%e\t%M" \
            ./pipeline.sh mmseqs ../../results/GeMoMa/${SPECIES_NAME}/mr_${MUTATION_RATE}/input.fa \
            ../../reference_species/${MODEL_NAME}/${MODEL_NAME}_annotation.gff3 \
            ../../reference_species/${MODEL_NAME}/${MODEL_NAME}_dna.fa 10 ../../results/GeMoMa/${SPECIES_NAME}/mr_${MUTATION_RATE}/${HINTS_TYPE} \
            > "../../results/GeMoMa/${SPECIES_NAME}/mr_${MUTATION_RATE}/${HINTS_TYPE}/${SPECIES_NAME}_${HINTS_TYPE}_output.txt" \
            2> "../../results/GeMoMa/${SPECIES_NAME}/mr_${MUTATION_RATE}/${HINTS_TYPE}/${SPECIES_NAME}_${HINTS_TYPE}_time_mem.txt"

        cd ../../results/GeMoMa/${SPECIES_NAME}/mr_${MUTATION_RATE}
        
    fi
}

for SPECIES in "$SPECIES_FOLDER"/*; do
    [ -d "$SPECIES" ] || continue

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
    GENUS_MODEL=$(eval echo "\$${SPECIES_NAME}_genus" | tr -d '[:space:]')
    ORDER_MODEL=$(eval echo "\$${SPECIES_NAME}_order" | tr -d '[:space:]')

    for MUTATION_RATE in original 0.01 0.04 0.07; do

        mkdir -p "mr_${MUTATION_RATE}"
        cd "mr_${MUTATION_RATE}" || exit 1
        echo "Current mutation rate: ${MUTATION_RATE}"

        if [ "$MUTATION_RATE" != "original" ]; then
            #AlcoR simulation -fs 0:0:0:42:$MUTATION_RATE:0:0:../../../$DNA_FILE > input.fa
            gto_fasta_mutate -e $MUTATION_RATE < ../../$DNA_FILE > input.fa
        else
            cp ../../$DNA_FILE input.fa
        fi

        runGeMoMa "far" "$SPECIES_NAME" "$FAR_MODEL" "$MUTATION_RATE"
        runGeMoMa "genus" "$SPECIES_NAME" "$GENUS_MODEL" "$MUTATION_RATE"
        runGeMoMa "order" "$SPECIES_NAME" "$ORDER_MODEL" "$MUTATION_RATE"

        rm input.fa

        cd ..

    done

    cd ..
done
