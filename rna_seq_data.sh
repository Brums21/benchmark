#!/bin/bash

function generator() {
    local SPECIES="$1"
    QUERY_SPECIES=$(echo "${SPECIES}" | sed 's,_*, ,g')
    SEARCH_TERM="\"$QUERY_SPECIES\"[Organism] AND TRANSCRIPTOMIC[Source] AND RNA-Seq[Strategy] AND cDNA[Selection] AND SINGLE[Layout]"
    MAX_RESULTS=3

    OUTPUT_DIR="species/${SPECIES}/"
    mkdir -p "$OUTPUT_DIR"

    echo "Searching for RNA-Seq datasets for *${SPECIES}*..."
    esearch -db sra -query "$SEARCH_TERM" | efetch -format runinfo > sra_metadata.csv

    SHORT_READS=$(awk -F ',' '
        BEGIN { OFS="\t" }
        NR > 1 && $1 ~ /^SRR/ && $8 >= 100 && $8 <= 600 && $17 >= 50 {
            print $1, $8, $17
        }
    ' sra_metadata.csv | sort -k2,2nr | head -n "$MAX_RESULTS" | cut -f1)

    echo "Selected RNA-seq datasets:"
    echo "$SHORT_READS"

    > "$OUTPUT_DIR/${SPECIES}_RNA.fastq"

    local RUN_ID_ARRAY=()

    for RUN_ID in $SHORT_READS; do
        echo "Downloading $RUN_ID..."
        fastq-dump "$RUN_ID" --split-files --outdir "$OUTPUT_DIR"
        echo "Download complete for $RUN_ID"

        FASTQ_FILE=""
        if [ -f "$OUTPUT_DIR/${RUN_ID}.fastq" ]; then
            FASTQ_FILE="$OUTPUT_DIR/${RUN_ID}.fastq"
        elif [ -f "$OUTPUT_DIR/${RUN_ID}_1.fastq" ]; then
            FASTQ_FILE="$OUTPUT_DIR/${RUN_ID}_1.fastq"
        fi

        if [ -f "$FASTQ_FILE" ]; then
            READ_COUNT=$(grep -c "^+$" "$FASTQ_FILE")
            AVG_LEN=$(awk 'NR % 4 == 2 { total += length($0); count++ } END { if (count>0) print int(total/count); else print 0 }' "$FASTQ_FILE")

            echo "$RUN_ID → Reads: $READ_COUNT | Avg. length: $AVG_LEN bp"

            if [ "$READ_COUNT" -lt 1000000 ] || [ "$AVG_LEN" -lt 50 ]; then
                echo "Skipping $RUN_ID: poor quality (low count or short reads)"
                rm -f "$FASTQ_FILE"
                continue
            fi

            cat "$FASTQ_FILE" >> "$OUTPUT_DIR/${SPECIES}_RNA.fastq"
            rm -f "$FASTQ_FILE"
            RUN_ID_ARRAY+=("$RUN_ID")
        fi
    done

    if [ ${#RUN_ID_ARRAY[@]} -gt 0 ]; then
        generateConfigFile "genus" "$SPECIES" "${RUN_ID_ARRAY[@]}"
        generateConfigFile "order" "$SPECIES" "${RUN_ID_ARRAY[@]}"
        generateConfigFile "far" "$SPECIES" "${RUN_ID_ARRAY[@]}"
    else
        echo "No high-quality datasets found for $SPECIES"
    fi

    rm -f sra_metadata.csv
    echo "RNA-seq download complete - $OUTPUT_DIR"
}

function generateConfigFile() {
    local HINTS_TYPE="$1"
    local SPECIES="$2"
    shift 2
    local RUN_IDS=("$@")
    local HINTS_FILE="hints/${SPECIES}_${HINTS_TYPE}.fa"

    if [ -f "$HINTS_FILE" ]; then
        local GENOME_PATH=$(realpath "species/${SPECIES}/${SPECIES}_dna.fa")
        local PROT_PATH=$(realpath "$HINTS_FILE")

        {
            echo "---"
            echo "species: ${SPECIES}"
            echo "genome_path: ${GENOME_PATH}"
            echo "rnaseq_sets: ["
            for ((i = 0; i < ${#RUN_IDS[@]}; i++)); do
                if [ "$i" -lt $((${#RUN_IDS[@]} - 1)) ]; then
                    echo "    ${RUN_IDS[$i]},"
                else
                    echo "    ${RUN_IDS[$i]}"
                fi
            done
            echo "]"
            echo "protdb_path: ${PROT_PATH}"
        } > "species/${SPECIES}/${SPECIES}_${HINTS_TYPE}.yaml"
    else
        echo "Hint file not found for ${SPECIES}_${HINTS_TYPE}. Skipping..."
    fi
}

for SPECIES in "species"/*; do
    [ -d "$SPECIES" ] || continue 
    SPECIES_NAME=$(basename "$SPECIES")
    echo "Processing species: $SPECIES_NAME"
    generator "$SPECIES_NAME"
done
