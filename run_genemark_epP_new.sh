#!/bin/bash

# Notas: para correr GeneMark-EP+, a ferramenta ProtHint é necessária, e vem incluida na pasta do gmes_linux_64.
# O script hints_generator.sh gera sequências de proteínas para diferentes níveis taxonômicos (gênero, ordem, etc.).
# Mais informações podem ser encontradas nos comentários do script.

SPECIES_FOLDER="../../species"

if [ ! -d "hints" ]; then
    echo "Generating all hints to be used as input."
    ./hints_generator.sh
else
    echo "Hints already generated. Skipping..."
fi

mkdir -p results/GeneMark-EPp
cd results/GeneMark-EPp || exit 1

runTimedCommand() {
    local CMD="$1"
    local OUTPUT_FILE="$2"
    local TIME_MEM_FILE="$3"

    (/usr/bin/time -f "%e\t%M" bash -c "$CMD") > "$OUTPUT_FILE" 2> "$TIME_MEM_FILE"
}

runGeneMarkEPp() {
    local HINTS_TYPE="$1"
    local SPECIES_NAME="$2"
    local DNA_FILE="$3"
    local HINTS_FILE="../../../hints/${SPECIES_NAME}_${HINTS_TYPE}.fa"

    if [ -f "$HINTS_FILE" ]; then
        mkdir -p "$HINTS_TYPE"
        cd "$HINTS_TYPE" || exit 1

        echo "Running ProtHint for $SPECIES_NAME with $HINTS_TYPE hints..."
        runTimedCommand "../../../../gmes_linux_64/ProtHint/bin/prothint.py $DNA_FILE $HINTS_FILE" \
            "${SPECIES_NAME}_${HINTS_TYPE}_prothint_output.txt" \
            "${SPECIES_NAME}_${HINTS_TYPE}_prothint_time_mem.txt"

        echo "Running GeneMark-EP+ for $SPECIES_NAME with $HINTS_TYPE hints..."
        runTimedCommand "../../../gmes_linux_64/gmes_petap.pl --EP prothint.gff --evidence evidence.gff --seq $DNA_FILE --cores 10" \
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

    runGeneMarkEPp "genus" "$SPECIES_NAME" "$DNA_FILE"
    runGeneMarkEPp "order" "$SPECIES_NAME" "$DNA_FILE"
    runGeneMarkEPp "far" "$SPECIES_NAME" "$DNA_FILE"

    cd ..
done

cd ../..
