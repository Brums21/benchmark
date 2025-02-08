#!/bin/bash

function getRNAData(){

    local SPECIES="$1"

    QUERY_SPECIES=$(echo "${SPECIES}" | sed 's,\_, ,g')

    SEARCH_TERM="\"Arabidopsis thaliana\"[Organism] AND TRANSCRIPTOMIC[Source] AND RNA-Seq[Strategy] AND cDNA[Selection] AND SINGLE[Layout]"
    MAX_RESULTS=1

    OUTPUT_DIR="species/${SPECIES}/"

    echo "Searching for *${SPECIES}* small RNA sequencing datasets..."

    esearch -db sra -query "$SEARCH_TERM" | efetch -format runinfo > sra_metadata.csv

    SHORT_READS=$(awk -F ',' '$1 ~ /^SRR/ && $8 > 0 && $8 < 600 {print $1}' sra_metadata.csv | head -n "$MAX_RESULTS")

    echo "Found the following small RNA sequencing datasets:"
    echo "$SHORT_READS"
    echo "$SHORT_READS" >> ${OUTPUT_DIR}/RNA.txt

    for RUN_ID in $SHORT_READS; do
        echo "Downloading small RNA-seq data for $RUN_ID..."
        fasterq-dump "$RUN_ID" --split-files --outdir "$OUTPUT_DIR"
        echo "Download complete for $RUN_ID"

        # renaming
        if [ -f "$OUTPUT_DIR/${RUN_ID}.fastq" ]; then
            mv "$OUTPUT_DIR/${RUN_ID}.fastq" "$OUTPUT_DIR/${SPECIES}_RNA.fastq"
        fi

    done

    rm sra_metadata.csv

    echo "All requested small RNA-seq data has been downloaded to: $OUTPUT_DIR"

}

for SPECIES in "species"/*; do
    [ -d "$SPECIES" ] || continue 

    SPECIES_NAME=$(basename "$SPECIES")
    echo "Getting RNA data for species: $SPECIES_NAME"

    getRNAData $SPECIES_NAME

done