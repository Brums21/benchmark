#!/bin/bash

function generator(){

    local SPECIES="$1"

    QUERY_SPECIES=$(echo "${SPECIES}" | sed 's,\_, ,g')

    SEARCH_TERM="\"$QUERY_SPECIES\"[Organism] AND TRANSCRIPTOMIC[Source] AND RNA-Seq[Strategy] AND cDNA[Selection] AND SINGLE[Layout]"
    MAX_RESULTS=1

    OUTPUT_DIR="species/${SPECIES}/"

    echo "Searching for *${SPECIES}* RNA sequencing datasets..."

    esearch -db sra -query "$SEARCH_TERM" | efetch -format runinfo > sra_metadata.csv

    SHORT_READS=$(awk -F ',' '$1 ~ /^SRR/ && $8 > 0 && $8 < 600 {print $1}' sra_metadata.csv | head -n "$MAX_RESULTS")

    echo "Found the following small RNA sequencing datasets:"
    echo "$SHORT_READS"

    for RUN_ID in $SHORT_READS; do
        echo "Downloading small RNA-seq data for $RUN_ID..."
        fasterq-dump "$RUN_ID" --split-files --outdir "$OUTPUT_DIR"
        echo "Download complete for $RUN_ID"

        # renaming
        if [ -f "$OUTPUT_DIR/${RUN_ID}.fastq" ]; then
            mv "$OUTPUT_DIR/${RUN_ID}.fastq" "$OUTPUT_DIR/${SPECIES}_RNA.fastq"
        fi

    done

    generateConfigFile "genus" "$SPECIES" "${RUN_ID}"
    generateConfigFile "order" "$SPECIES" "${RUN_ID}"
    generateConfigFile "far" "$SPECIES" "${RUN_ID}"

    rm sra_metadata.csv

    echo "All requested RNA-seq data has been downloaded to: $OUTPUT_DIR"

}

function generateConfigFile(){
    local HINTS_TYPE="$1"
    local SPECIES="$2"
    local RUN_ID="$3"
    local HINTS_FILE="hints/${SPECIES}_${HINTS_TYPE}.fa"

    if [ -f "$HINTS_FILE" ]; then

        echo -e "---\n\
species: ${SPECIES}\n\
genome_path: input.fa\n\
rnaseq_sets: [ \n\
    ${RUN_ID}\n\
]\n\
protdb_path: hints/${SPECIES}_far.fa" >> species/${SPECIES}/${SPECIES}_${HINTS_TYPE}.yaml

    else
        echo "Hints file for ${SPECIES_NAME}_${HINTS_TYPE} not found. Skipping..."
    fi
}

for SPECIES in "species"/*; do
    [ -d "$SPECIES" ] || continue 

    SPECIES_NAME=$(basename "$SPECIES")
    echo "Getting RNA data for species: $SPECIES_NAME"

    generator $SPECIES_NAME

done