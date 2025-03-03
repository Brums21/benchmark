#!/bin/bash

# Notas: para correr GeneMark-EP+, a ferramenta ProtHint Ã© necessÃ¡ria, e vem incluida na pasta do gmes_linux_64.
# O script hints_generator.sh gera sequÃªncias de proteÃ­nas para diferentes nÃ­veis taxonÃ´micos (gÃªnero, ordem, etc.).
# Mais informaÃ§Ãµes podem ser encontradas nos comentÃ¡rios do script.

SPECIES_FOLDER="../../species"

if [ ! -d "../hints" ]; then
    echo "Generating all hints to be used as input."
    cd ..
    ./hints_generator.sh
    cd benchmarking_scripts/
else
    echo "Hints already generated. Skipping..."
fi

mkdir -p ../results/GeneMark-EPp
cd ../results/GeneMark-EPp || exit 1

runTimedCommand() {
    local CMD="$1"
    local OUTPUT_FILE="$2"
    local TIME_MEM_FILE="$3"

    (/usr/bin/time -f "%e\t%M" bash -c "$CMD") > "$OUTPUT_FILE" 2> "$TIME_MEM_FILE"
}

runGeneMarkEPp() {
    local HINTS_TYPE="$1"
    local SPECIES_NAME="$2"
    local MUTATION_RATE="$3"
    local HINTS_FILE="../../../../hints/${SPECIES_NAME}_${HINTS_TYPE}.fa"

    if [ -f "$HINTS_FILE" ]; then
        mkdir -p "$HINTS_TYPE"
        cd "$HINTS_TYPE" || exit 1

        echo "Running ProtHint for $SPECIES_NAME with $HINTS_TYPE hints..."
        runTimedCommand "../../../../../tools/gmes_linux_64/ProtHint/bin/prothint.py --geneMarkGtf ../../../../../results/GeneMark-ES/${SPECIES_NAME}/mr_${MUTATION_RATE}/genemark.gtf ../input.fa ../${HINTS_FILE}" \
            "${SPECIES_NAME}_${HINTS_TYPE}_prothint_output.txt" \
            "${SPECIES_NAME}_${HINTS_TYPE}_prothint_time_mem.txt"

        echo "Running GeneMark-EP+ for $SPECIES_NAME with $HINTS_TYPE hints..."
        runTimedCommand "../../../../../tools/gmes_linux_64/gmes_petap.pl --EP prothint.gff --evidence evidence.gff --seq ../input.fa --cores 10" \
            "${SPECIES_NAME}_${HINTS_TYPE}_genemark_output.txt" \
            "${SPECIES_NAME}_${HINTS_TYPE}_genemark_time_mem.txt"

        cd ..
    else
        echo "Hints file for ${SPECIES_NAME}_${HINTS_TYPE} not found. Skipping..."
    fi
}

for SPECIES in "$SPECIES_FOLDER"/*; do
    [ -d "$SPECIES" ] || continue 

    SPECIES_NAME=$(basename "$SPECIES")
    echo "Processing species: $SPECIES_NAME"
    DNA_FILE="$SPECIES/${SPECIES_NAME}_dna.fa"

    if [ ! -f "$DNA_FILE" ]; then
        echo "DNA file not found for species: $SPECIES_NAME. Skipping..."
        continue
    fi

    mkdir -p "$SPECIES_NAME"
    cd "$SPECIES_NAME" || exit 1

    for MUTATION_RATE in original 0.01 0.04 0.07; do
        mkdir -p "mr_${MUTATION_RATE}"
        cd "mr_${MUTATION_RATE}" || exit 1

        if [ "$MUTATION_RATE" != "original" ]; then
            #AlcoR simulation -fs 0:0:0:42:$MUTATION_RATE:0:0:../../../$DNA_FILE > input.fa
            gto_fasta_mutate -e $MUTATION_RATE < ../../$DNA_FILE > input.fa
        else
            cp ../../$DNA_FILE input.fa
        fi

        runGeneMarkEPp "genus" "$SPECIES_NAME" "$MUTATION_RATE"
        runGeneMarkEPp "order" "$SPECIES_NAME" "$MUTATION_RATE"
        runGeneMarkEPp "far" "$SPECIES_NAME" "$MUTATION_RATE"

        rm input.fa

        cd ..

    done

    cd ..
    
done

cd ../..
