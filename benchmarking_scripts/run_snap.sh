#!/bin/bash

SPECIES_FOLDER="../../species"

mkdir -p ../results/SNAP
cd ../results/SNAP || exit 1

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
    DNA_FILE="$SPECIES/${SPECIES_NAME}_dna.fa"

    mkdir -p "$SPECIES_NAME"
    cd "$SPECIES_NAME" || exit 1

    echo "Running SNAP with Arabidopsis thaliana reference species..."
    mkdir -p "arabidopsis_reference"
    cd "arabidopsis_reference" || exit 1

    for MUTATION_RATE in original 0.01 0.04 0.07; do
        mkdir -p "mr_${MUTATION_RATE}"
        cd "mr_${MUTATION_RATE}" || exit 1

        if [ -f "output.gff" ]; then
            echo "Already run for species ${SPECIES_NAME} with mutation rate ${MUTATION_RATE}. Skipping..."
            cd ..
            continue
        fi

        if [ "$MUTATION_RATE" != "original" ]; then
            gto_fasta_mutate -e $MUTATION_RATE < ../../../$DNA_FILE > input.fa
        else
            cp ../../../$DNA_FILE input.fa
        fi

        runTimedCommand "./../../../../../tools/SNAP-master/snap -gff A.thaliana.hmm input.fa > output.gff" \
            "${SPECIES_NAME}_a_thaliana_output.txt" \
            "${SPECIES_NAME}_a_thaliana_time_mem.txt"

        rm input.fa

        cd ..
    
    done

    cd ..

    echo "Running SNAP with rice (Oryza sativa) reference species..."
    mkdir -p "rice_reference"
    cd "rice_reference" || exit 1

    for MUTATION_RATE in original 0.01 0.04 0.07; do
        mkdir -p "mr_${MUTATION_RATE}"
        cd "mr_${MUTATION_RATE}" || exit 1

        if [ "$MUTATION_RATE" != "original" ]; then
            gto_fasta_mutate -e $MUTATION_RATE < ../../../$DNA_FILE > input.fa
        else
            cp ../../../$DNA_FILE input.fa
        fi

        runTimedCommand "./../../../../../tools/SNAP-master/snap -gff O.sativa.hmm input.fa > output.gff" \
            "${SPECIES_NAME}_o_sativa_output.txt" \
            "${SPECIES_NAME}_o_sativa_time_mem.txt"
        
        rm input.fa

        cd ..

    done

    cd ../..
done
