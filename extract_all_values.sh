#!/bin/bash

getAugustusResults() {
    for SPECIES in results/augustus/*; do
        
        SPECIES_NAME=$(basename "$SPECIES")

        # buscar o valor numérico do MR
        for MR in "$SPECIES"/*; do

            MR_NAME=$(basename "$MR")
            MR_NUMBER="${MR_NAME:3}"

            for HINTS_TYPE in "$MR"/*; do

                HINTS_TYPE_NAME=$(basename "$HINTS_TYPE")

                if [ ! -f "${HINTS_TYPE}/augustus.gtf" ]; then
                    echo "GTF file not found in ${HINTS_TYPE}. Skipping..."
                    continue
                fi

                #buscar time and ram consumption
                TIME_MEM=$(tail -n 2 "${HINTS_TYPE}/${SPECIES_NAME}_${HINTS_TYPE_NAME}_augustus_time_mem.txt" | grep -v '^$' | tail -n 1)
                
                read -r TIME MEM <<< "$TIME_MEM"

                TIME=$(echo "$TIME" | tr -d '[:space:]')
                MEM=$(echo "$MEM" | tr -d '[:space:]')
                cp "${HINTS_TYPE}/augustus.gtf" "aggregate_results/augustus_${SPECIES_NAME}_${MR_NUMBER}_${HINTS_TYPE_NAME}_${TIME}_${MEM}.gtf"
            done
        done
    done
}

getGenemarkEPpResults() {
    for SPECIES in results/GeneMark-EPp/*; do
        
        SPECIES_NAME=$(basename "$SPECIES")

        # buscar o valor numérico do MR
        for MR in "$SPECIES"/*; do

            MR_NAME=$(basename "$MR")
            MR_NUMBER="${MR_NAME:3}"

            for HINTS_TYPE in "$MR"/*; do

                HINTS_TYPE_NAME=$(basename "$HINTS_TYPE")

                if [ ! -f "${HINTS_TYPE}/genemark.gtf" ]; then
                    echo "GTF file not found in ${HINTS_TYPE}. Skipping..."
                    continue
                fi

                TIME_MEM=$(tail -n 2 "${HINTS_TYPE}/${SPECIES_NAME}_${HINTS_TYPE_NAME}_genemark_time_mem.txt" | grep -v '^$' | tail -n 1)
                
                read -r TIME MEM <<< "$TIME_MEM"

                TIME=$(echo "$TIME" | tr -d '[:space:]')
                MEM=$(echo "$MEM" | tr -d '[:space:]')

                cp ${HINTS_TYPE}/genemark.gtf aggregate_results/genemarkep_${SPECIES_NAME}_${MR_NUMBER}_${HINTS_TYPE_NAME}_${TIME}_${MEM}.gtf
            done
        done
    done
}

getGenemarkESResults() {
    for SPECIES in results/GeneMark-ES/*; do
        
        SPECIES_NAME=$(basename "$SPECIES")

        for MR in "$SPECIES"/*; do

            MR_NAME=$(basename "$MR")
            MR_NUMBER="${MR_NAME:3}"

            if [ ! -f "${MR}/genemark.gtf" ]; then
                echo "GTF file not found in ${MR}. Skipping..."
                continue
            fi

            TIME_MEM=$(tail -n 2 "${MR}/${SPECIES_NAME}_genemark_time_mem.txt" | grep -v '^$' | tail -n 1)
            
            read -r TIME MEM <<< "$TIME_MEM"

            TIME=$(echo "$TIME" | tr -d '[:space:]')
            MEM=$(echo "$MEM" | tr -d '[:space:]')

            cp ${MR}/genemark.gtf aggregate_results/genemarkes_${SPECIES_NAME}_${MR_NUMBER}_${TIME}_${MEM}.gtf
        done
    done
}

getGenemarkETPResults() {
    for SPECIES in results/GeneMark-ETP/*; do
        
        SPECIES_NAME=$(basename "$SPECIES")

        for MR in "$SPECIES"/*; do

            MR_NAME=$(basename "$MR")
            MR_NUMBER="${MR_NAME:3}"

            for HINTS_TYPE in "$MR"/*; do

                HINTS_TYPE_NAME=$(basename "$HINTS_TYPE")

                if [ ! -f "${HINTS_TYPE}/genemark.gtf" ]; then
                    echo "GTF file not found in ${HINTS_TYPE}. Skipping..."
                    continue
                fi

                TIME_MEM=$(tail -n 2 "${HINTS_TYPE}/${SPECIES_NAME}_${HINTS_TYPE_NAME}_genemark_time_mem.txt" | grep -v '^$' | tail -n 1)
                
                read -r TIME MEM <<< "$TIME_MEM"

                TIME=$(echo "$TIME" | tr -d '[:space:]')
                MEM=$(echo "$MEM" | tr -d '[:space:]')

                cp ${HINTS_TYPE}/genemark.gtf aggregate_results/genemarketp_${SPECIES_NAME}_${MR_NUMBER}_${HINTS_TYPE_NAME}_${TIME}_${MEM}.gtf
            done
        done
    done
}

getGeMoMaResults() {
    for SPECIES in results/GeMoMa/*; do
        
        SPECIES_NAME=$(basename "$SPECIES")

        for MR in "$SPECIES"/*; do

            MR_NAME=$(basename "$MR")
            MR_NUMBER="${MR_NAME:3}"

            for HINTS_TYPE in "$MR"/*; do

                HINTS_TYPE_NAME=$(basename "$HINTS_TYPE")

                if [ ! -f "${HINTS_TYPE}/final_annotation.gff" ]; then
                    echo "GFF file not found in ${HINTS_TYPE}. Skipping..."
                    continue
                fi

                TIME_MEM=$(tail -n 2 "${HINTS_TYPE}/${SPECIES_NAME}_${HINTS_TYPE_NAME}_time_mem.txt" | grep -v '^$' | tail -n 1)
                
                read -r TIME MEM <<< "$TIME_MEM"

                TIME=$(echo "$TIME" | tr -d '[:space:]')
                MEM=$(echo "$MEM" | tr -d '[:space:]')

                cp ${HINTS_TYPE}/final_annotation.gff aggregate_results/gemoma_${SPECIES_NAME}_${MR_NUMBER}_${HINTS_TYPE_NAME}_${TIME}_${MEM}.gff
            done
        done
    done
}

getSNAPResults() {
    for SPECIES in results/SNAP/*; do
        
        SPECIES_NAME=$(basename "$SPECIES")

        for REFERENCE_TYPE in "$SPECIES"/*; do

            REFERENCE_TYPE_NAME=$(basename "$REFERENCE_TYPE")
            REFERENCE_TYPE_SPECIES="${REFERENCE_TYPE_NAME:0:-10}"

            for MR in "$REFERENCE_TYPE"/*; do

                MR_NAME=$(basename "$MR")
                MR_NUMBER="${MR_NAME:3}"

                if [ ! -f "${MR}/output.gff" ]; then
                    echo "GFF file not found in ${MR}. Skipping..."
                    continue
                fi

                REFERENCE_SPECIES_EXT=""
                if [ "$REFERENCE_TYPE_SPECIES" == "rice" ]; then
                    REFERENCE_SPECIES_EXT="o_sativa"
                elif [ "$REFERENCE_TYPE_SPECIES" == "arabidopsis" ]; then
                    REFERENCE_SPECIES_EXT="a_thaliana"
                else
                    echo "Can't recognise the reference species ${REFERENCE_TYPE_SPECIES} as a model used in the SNAP results. Skipping..."
                    continue
                fi

                TIME_MEM=$(tail -n 2 "${MR}/${SPECIES_NAME}_${REFERENCE_SPECIES_EXT}_time_mem.txt" | grep -v '^$' | tail -n 1)
                
                read -r TIME MEM <<< "$TIME_MEM"

                TIME=$(echo "$TIME" | tr -d '[:space:]')
                MEM=$(echo "$MEM" | tr -d '[:space:]')

                cp ${MR}/output.gff aggregate_results/snap_${SPECIES_NAME}_${MR_NUMBER}_${REFERENCE_TYPE_SPECIES}_${TIME}_${MEM}.gff

            done
        done
    done
}

convert_and_merge() {
    local BASENAME="$1"
    local MODE="$2"

    merged_gff3="merged.gff3"
    > "$merged_gff3"
    echo "##gff-version 3" >> "$merged_gff3"

    echo "Merging cleaned files for $BASENAME ($MODE mode)..."

    for file in ./aggregate_results/${BASENAME}_cleaned_*; do
        if [[ -f "$file" ]]; then
            echo "Processing $file"

            case "$MODE" in
                "snap")
                    SNAP_ExonEtermEinitEsngl_gff_to_gff3.pl "$file" > "snap.gff3"
                    agat_convert_sp_gxf2gxf.pl -g "snap.gff3" -o "temp.gff3"
                    ;;
                *)
                    agat_convert_sp_gxf2gxf.pl -g "$file" -o "temp.gff3"
                    ;;
            esac

            gt gff3 -sort -tidy -o "temp_sorted.gff3" "temp.gff3"
            tail -n +2 "temp_sorted.gff3" >> "$merged_gff3"

            rm "$file" temp.gff3 temp_sorted.gff3
            [ "$MODE" = "snap" ] && rm -f snap.gff3
        fi
    done

    echo "Final sorting and ID assignment for $BASENAME"
    gt gff3 -force -tidy -sort -addids -o "./formatted_results/${BASENAME}.gff3" "$merged_gff3"
    rm "$merged_gff3"
    rm -f ./formatted_results/*.log *.log
}

process_file() {
    local FILE="$1"
    local MODE="$2"
    local EXT="${FILE##*.}"
    local BASENAME=$(basename "$FILE" ."$EXT")

    echo "Processing $BASENAME with mode: $MODE"
    python ./modify_output.py "$FILE"
    convert_and_merge "$BASENAME" "$MODE"
}

## 1a fase -----------------------------------------------
#mkdir -p "aggregate_results"
##
### aggregate results
#for TOOL in results/*; do
#
#    TOOL_NAME=$(basename "$TOOL")
#
#    echo "Parsing ${TOOL_NAME} results..."
#
#    if [ "$TOOL_NAME" == "augustus" ]; then
#        getAugustusResults
#    elif [ "$TOOL_NAME" == "GeneMark-EPp" ]; then
#        getGenemarkEPpResults
#    elif [ "$TOOL_NAME" == "GeneMark-ES" ]; then
#        getGenemarkESResults
#    elif [ "$TOOL_NAME" == "GeneMark-ETP" ]; then
#        getGenemarkETPResults
#    elif [ "$TOOL_NAME" == "GeMoMa" ]; then
#        getGeMoMaResults
#    elif [ "$TOOL_NAME" == "SNAP" ]; then
#        getSNAPResults
#    fi
#
#done
#
## 2a fase ----------------------------------------------
#mkdir -p "formatted_results"

#echo "Starting annotation formatting..."
#
## Uncomment to process other modes
#
#for FILE in ./aggregate_results/genemarkes*; do process_file "$FILE" "default"; done
#for FILE in ./aggregate_results/genemarketp*; do process_file "$FILE" "default"; done
#for FILE in ./aggregate_results/genemarkep*; do process_file "$FILE" "default"; done
#for FILE in ./aggregate_results/augustus*; do process_file "$FILE" "default"; done
#for FILE in ./aggregate_results/gemoma*; do process_file "$FILE" "default"; done
#for FILE in ./aggregate_results/snap*; do process_file "$FILE" "snap"; done
#
#echo "Finished formatting all annotations."
#
#rm -r aggregate_results/

mkdir -p ./final_results

for FILE in ./formatted_results/augustus_*; do
    FILE_NAME=$(basename "$FILE")
    SPECIES_NAME=$(echo "$FILE_NAME" | cut -d'_' -f2,3)

    # check if files exists
    if [ ! -f "./species/${SPECIES_NAME}/${SPECIES_NAME}_annotation.gff3" ]; then
        echo "GFF3 file not found for ${SPECIES_NAME}. Skipping..."
        continue
    fi
    if [ ! -f "$FILE" ]; then
        echo "File not found: $FILE. Skipping..."
        continue
    fi
    
    if [ -f "./final_results/${FILE_NAME%.*}.csv" ]; then
        echo "CSV result already exists. Skipping..."
        continue
    fi

    ./obtain_metrics ./species/${SPECIES_NAME}/${SPECIES_NAME}_annotation.gff3 ${FILE} --threads 6
done

#rm -r formatted_results/