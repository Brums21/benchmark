#!/bin/bash

# Notas: para correr GeneMark-EP+, a ferramenta ProtHint é necessária, e vem incluida na pasta do gmes_linux_64
# Para este benchmark foram consideradas as proteinas do set 'eucariota', que depois são passadas pela ferramenta  
# ProtHint de modo a obter o input necessário para o GeneMark-EP+

SPECIES_FOLDER="../../species"

mkdir -p results/GeneMark-EPp
cd results/GeneMark-EPp || exit

# Primeiro devem ser procuradas as evidências das proteínas usando a ferramenta ProtHint

if [ ! -e "Eukaryota.fa" ]; then
    echo "Downloading eukaryotic proteins..."
    wget "https://bioinf.uni-greifswald.de/bioinf/partitioned_odb11/Eukaryota.fa.gz" -O Eukaryota.fa.gz
    gunzip Eukaryota.fa.gz
else
    echo "Protein set is already available. Skipping download..."
fi

# Executar GeneMark-EP+ para todas as espécies
for SPECIES in "$SPECIES_FOLDER"/*; do
    if [ -d "$SPECIES" ]; then
        SPECIES_NAME=$(basename "$SPECIES")
        echo "Processing species: $SPECIES_NAME"
        DNA_FILE="$SPECIES/${SPECIES_NAME}_dna.fa"

        if [ ! -e "$DNA_FILE" ]; then
            echo "DNA file not found for species: $SPECIES_NAME. Skipping..."
            continue
        fi

        start_time=$(date +%s)

        echo "Running ProtHint for $SPECIES_NAME..."
        ../../gmes_linux_64/ProtHint/bin/prothint.py "$DNA_FILE" Eukaryota.fa

        echo "Running GeneMark-EP+ for $SPECIES_NAME..."
        ../../gmes_linux_64/gmes_petap.pl --EP prothint.gff --evidence evidence.gff --seq "$DNA_FILE"

        end_time=$(date +%s)
        elapsed_time=$((end_time - start_time))

        echo "Process took $elapsed_time seconds." > "${SPECIES_NAME}_time.txt"
        echo "Elapsed time for $SPECIES_NAME: $elapsed_time seconds."

        rm prothint.gff evidence.gff
    fi
done
