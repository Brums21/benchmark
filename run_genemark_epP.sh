#!/bin/bash

# Notas: para correr GeneMark-EP+, a ferramenta ProtHint é necessária, e vem incluida na pasta do gmes_linux_64
# Para este benchmark foram consideradas as proteinas do set 'eucariota', que depois são passadas pela ferramenta  
# ProtHint de modo a obter o input necessário para o GeneMark-EP+

SPECIES_FOLDER="../../species"

mkdir -p results/GeneMark-EPp; cd results/GeneMark-EPp;

# Primeiro devem ser procuradas as evidências das proteinas usando a ferramenta ProtHint

if [ ! -e "Eukaryota.fa" ||  ]; then
    echo "Downloading eukaryotic proteins..."
    wget "https://bioinf.uni-greifswald.de/bioinf/partitioned_odb11/Eukaryota.fa.gz" -O Eukaryota.fa.gz
    gunzip Eukaryota.fa.gz
else
    echo "Protein set is already available. Skipping..."
fi

# Executar GeneMark-EP+ para todas as espécies
for SPECIES in "$SPECIES_FOLDER"/*; do
    if [ -d "$SPECIES" ]; then
        echo "Species being processed: $SPECIES"
        DNA_FILE="$SPECIES/$(basename "$SPECIES")_dna.fa"

        # run prothint for the species
        ../../gmes_linux_64/ProtHint/bin/prothint.py $DNA_FILE Eukaryota.fa

        # run genemark-ep+
        ../../gmes_linux_64/gmes_petap.pl --EP prothint.gff --evidence evidence.gff --seq $DNA_FILE

        rm prothint.gff
        rm evidence.gff

    fi
done
