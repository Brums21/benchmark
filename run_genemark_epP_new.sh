#!/bin/bash

# Notas: para correr GeneMark-EP+, a ferramenta ProtHint é necessária, e vem incluida na pasta do gmes_linux_64
# De modo a criar differentes tipos de hints, o script hints_generator.sh vai buscar sequencias de proteinas para 
# espécies escolhidas com diferentes graus de género e ordem, quando disponivel. Mais informação no comentário
# do script.

SPECIES_FOLDER="../../species"

# Generate all hints
if [ ! -d "hints" ]; then
    echo "Generating all hints to be used as input."
    ./hints_generator.sh
else
    echo "Hints already generated. Skipping... "
fi

mkdir -p results/GeneMark-EPp
cd results/GeneMark-EPp || exit

# Executar GeneMark-EP+ para todas as espécies
for SPECIES in "$SPECIES_FOLDER"/*; do
    if [ -d "$SPECIES" ]; then

        SPECIES_NAME=$(basename "$SPECIES")
        echo "Processing species: $SPECIES_NAME"
        DNA_FILE="$SPECIES/${SPECIES_NAME}_dna.fa"

        if [ ! -f "$DNA_FILE" ]; then
            echo "DNA file not found for species: $SPECIES_NAME. Skipping..."
            continue
        fi

        mkdir -p "$SPECIES_NAME"
        cd "$SPECIES_NAME" || exit 1

        if [ -f "../../../hints/${SPECIES_NAME}_genus.fa"]; then
            mkdir -p "genus"
            cd "genus" || exit 1

            HINTS_FILE=$(basename "../../../../hints/${SPECIES_NAME}_genus.fa")

            echo "Running ProtHint for $SPECIES_NAME with hints of the same genus..."
            ../../../../gmes_linux_64/ProtHint/bin/prothint.py "$DNA_FILE" "$HINTS_FILE"

            start_time=$(date +%s)

            echo "Running GeneMark-EP+ for $SPECIES_NAME..."
            ../../../gmes_linux_64/gmes_petap.pl --EP prothint.gff --evidence evidence.gff --seq "$DNA_FILE" --cores 10

            end_time=$(date +%s)
            elapsed_time=$((end_time - start_time))

            echo "Process took $elapsed_time seconds." > "${SPECIES_NAME}_genus_time.txt"
            echo "Elapsed time for ${SPECIES_NAME}_genus: $elapsed_time seconds."

            cd ..

        fi

        if [ -f "../../../hints/${SPECIES_NAME}_order.fa"]; then
            mkdir -p "order"
            cd "order" || exit 1

            HINTS_FILE=$(basename "../../../../hints/${SPECIES_NAME}_order.fa")

            echo "Running ProtHint for $SPECIES_NAME with hints of the same order..."
            ../../../../gmes_linux_64/ProtHint/bin/prothint.py "$DNA_FILE" "$HINTS_FILE"

            start_time=$(date +%s)

            echo "Running GeneMark-EP+ for $SPECIES_NAME..."
            ../../../gmes_linux_64/gmes_petap.pl --EP prothint.gff --evidence evidence.gff --seq "$DNA_FILE" --cores 10

            end_time=$(date +%s)
            elapsed_time=$((end_time - start_time))

            echo "Process took $elapsed_time seconds." > "${SPECIES_NAME}_order_time.txt"
            echo "Elapsed time for ${SPECIES_NAME}_order: $elapsed_time seconds."

            cd ..

        fi

        if [ -f "../../../hints/${SPECIES_NAME}_far.fa"]; then
   
            mkdir -p "far"
            cd "far" || exit 1

            HINTS_FILE=$(basename "../../../../hints/${SPECIES_NAME}_far.fa")

            echo "Running ProtHint for $SPECIES_NAME with hints from species that are far..."
            ../../../../gmes_linux_64/ProtHint/bin/prothint.py "$DNA_FILE" "$HINTS_FILE"

            start_time=$(date +%s)

            echo "Running GeneMark-EP+ for $SPECIES_NAME..."
            ../../../gmes_linux_64/gmes_petap.pl --EP prothint.gff --evidence evidence.gff --seq "$DNA_FILE" --cores 10

            end_time=$(date +%s)
            elapsed_time=$((end_time - start_time))

            echo "Process took $elapsed_time seconds." > "${SPECIES_NAME}_far_time.txt"
            echo "Elapsed time for ${SPECIES_NAME}_far: $elapsed_time seconds."

            cd ..

        fi

        cd ..

    fi
done

cd ../..