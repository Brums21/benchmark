#!/bin/bash

BENCHMARK_DIR="$HOME/benchmark"

RESULTS_DIR="${BENCHMARK_DIR}/results"
RESULTS_TOOL_DIR="${RESULTS_DIR}/tools"
COMPILED_RESULTS_DIR="${RESULTS_DIR}/compiled"
AGGREGATED_RESULTS="${COMPILED_RESULTS_DIR}/aggregated"
FORMATTED_RESULTS="${COMPILED_RESULTS_DIR}/formatted"

mkdir -p ${AGGREGATED_RESULTS}
mkdir -p ${FORMATTED_RESULTS}

OBTAIN_METRICS_BIN="${BENCHMARK_DIR}/metrics/obtain_metrics"
OBTAIN_METRICS_SRC="${OBTAIN_METRICS_BIN}.cpp"

getAugustusResults() {
    for SPECIES in ${RESULTS_TOOL_DIR}/augustus/*; do
        
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
                cp "${HINTS_TYPE}/augustus.gtf" "${AGGREGATED_RESULTS}/augustus_${SPECIES_NAME}_${MR_NUMBER}_${HINTS_TYPE_NAME}_${TIME}_${MEM}.gtf"
            done
        done
    done
}

getGenemarkEPpResults() {
    for SPECIES in ${RESULTS_TOOL_DIR}/GeneMark-EPp/*; do
        
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

                cp ${HINTS_TYPE}/genemark.gtf ${AGGREGATED_RESULTS}/genemarkep_${SPECIES_NAME}_${MR_NUMBER}_${HINTS_TYPE_NAME}_${TIME}_${MEM}.gtf
            done
        done
    done
}

getGenemarkESResults() {
    for SPECIES in ${RESULTS_TOOL_DIR}/GeneMark-ES/*; do
        
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

            cp ${MR}/genemark.gtf ${AGGREGATED_RESULTS}/genemarkes_${SPECIES_NAME}_${MR_NUMBER}_${TIME}_${MEM}.gtf
        done
    done
}

getGenemarkETPResults() {
    for SPECIES in ${RESULTS_TOOL_DIR}/GeneMark-ETP/*; do
        
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

                cp ${HINTS_TYPE}/genemark.gtf ${AGGREGATED_RESULTS}/genemarketp_${SPECIES_NAME}_${MR_NUMBER}_${HINTS_TYPE_NAME}_${TIME}_${MEM}.gtf
            done
        done
    done
}

getGeMoMaResults() {
    for SPECIES in ${RESULTS_TOOL_DIR}/GeMoMa/*; do
        
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

                cp ${HINTS_TYPE}/final_annotation.gff ${AGGREGATED_RESULTS}/gemoma_${SPECIES_NAME}_${MR_NUMBER}_${HINTS_TYPE_NAME}_${TIME}_${MEM}.gff
            done
        done
    done
}

getSNAPResults() {
    for SPECIES in ${RESULTS_TOOL_DIR}/SNAP/*; do
        
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

                REFERENCE_SPECIES_EXT="a_thaliana"

                TIME_MEM=$(tail -n 2 "${MR}/${SPECIES_NAME}_${REFERENCE_SPECIES_EXT}_time_mem.txt" | grep -v '^$' | tail -n 1)
                
                read -r TIME MEM <<< "$TIME_MEM"

                TIME=$(echo "$TIME" | tr -d '[:space:]')
                MEM=$(echo "$MEM" | tr -d '[:space:]')

                cp ${MR}/output.gff ${AGGREGATED_RESULTS}/snap_${SPECIES_NAME}_${MR_NUMBER}_${REFERENCE_TYPE_SPECIES}_${TIME}_${MEM}.gff

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

    for file in ${AGGREGATED_RESULTS}/${BASENAME}_cleaned_*; do
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
    gt gff3 -force -tidy -sort -addids -o "${FORMATTED_RESULTS}/${BASENAME}.gff3" "$merged_gff3"
    rm "$merged_gff3"
    rm -f ${FORMATTED_RESULTS}/*.log *.log
}

process_file() {
    local FILE="$1"
    local MODE="$2"
    local EXT="${FILE##*.}"
    local BASENAME=$(basename "$FILE" ."$EXT")

    echo "Processing $BASENAME with mode: $MODE"
    python3 ${BENCHMARK_DIR}/metrics/modify_output.py "$FILE"
    convert_and_merge "$BASENAME" "$MODE"
}

# 1a fase -----------------------------------------------
mkdir -p "${FORMATTED_RESULTS}"

# aggregate results
#for TOOL in ${RESULTS_TOOL_DIR}/*; do
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

# 2a fase ----------------------------------------------
#mkdir -p "${FORMATTED_RESULTS}"
#echo "Starting annotation formatting..."
#
#for pattern in genemarkes* genemarketp* genemarkep* augustus* gemoma* snap*; do
#    mode="default"
#    [[ $pattern == snap* ]] && mode="snap"
#
#    for FILE in "${AGGREGATED_RESULTS}"/$pattern; do
#        process_file "$FILE" "$mode"
#    done
#done

echo "Finished formatting all annotations."

mkdir -p ${COMPILED_RESULTS_DIR}

for FILE in ${FORMATTED_RESULTS}/*; do
    FILE_NAME=$(basename "$FILE")
    PRINT_AUC=""

    if [[ "$FILE_NAME" == augustus_* ]]; then
        PRINT_AUC="--print_auc"
    fi

    SPECIES_NAME=$(echo "$FILE_NAME" | cut -d'_' -f2,3)

    SPECIES_FOLDER="${BENCHMARK_DIR}/species/benchmark_species/${SPECIES_NAME}"

    # check if files exists
    if [ ! -f "${SPECIES_FOLDER}/${SPECIES_NAME}_annotation.gff3" ]; then
        echo "GFF3 file not found for ${SPECIES_NAME}. Skipping..."
        continue
    fi
    if [ ! -f "$FILE" ]; then
        echo "File not found: $FILE. Skipping..."
        continue
    fi
    
    if [ -f "${COMPILED_RESULTS_DIR}/${FILE_NAME%.*}.csv" ]; then
        echo "CSV result already exists. Skipping..."
        continue
    fi

    if [[ ! -x "${OBTAIN_METRICS_BIN}" ]]; then

        echo "Metrics executable not found, building from source..."
        if [[ -f "${OBTAIN_METRICS_SRC}" ]]; then
            g++ "$METRICS_SRC" -o "${OBTAIN_METRICS_BIN}"
            echo "Metrics executable compiled successfully."
        else
            echo "Error: Source file $METRICS_SRC not found."
            exit 1
        fi
    fi

    ${OBTAIN_METRICS_BIN} ${SPECIES_FOLDER}/${SPECIES_NAME}_annotation.gff3 ${FILE} --output_folder ${COMPILED_RESULTS_DIR} --threads 20 ${PRINT_AUC}
done

# extrair os do GeAnno
TMP_DIR="./tmp_metrics"
mkdir -p "$TMP_DIR"

RESULTS_GEANNO="${BENCHMARK_DIR}/results/GeAnno"
AUC_OUT="${RESULTS_GEANNO}/auc_csv/"

rm -rf ${RESULTS_GEANNO}/*

mkdir -p "${AUC_OUT}"

for MR in ${RESULTS_TOOL_DIR}/GeAnno/*; do
  [ -d "$MR" ] || continue
  MUT_RATE=${MR##*/}

  for MODEL_DIR in "$MR"/*; do
    [ -d "$MODEL_DIR" ] || continue
    MODEL_NAME=${MODEL_DIR##*/}

    for SPECIES_DIR in "$MODEL_DIR"/*; do
      [ -d "$SPECIES_DIR" ] || continue
      SPECIES_NAME=${SPECIES_DIR##*/}

      REF_GFF="${BENCHMARK_DIR}/species/benchmark_species/${SPECIES_NAME}/${SPECIES_NAME}_annotation.gff3"
      OUTPUT_DIR="$SPECIES_DIR/output"
      [ -d "$OUTPUT_DIR" ] || { echo "No ouput in $SPECIES_DIR"; continue; }

      for GFF in "$OUTPUT_DIR"/*.gff3; do
        [ -f "$GFF" ] || continue

        FILE_NAME=$(basename "$GFF")
        BASE="${FILE_NAME%.gff3}"

        IFS='_' read -r PART0 PART1 PART2 PART3 PART4 <<< "$BASE"
        WINDOW="$PART1"
        STEP="$PART2"
        THRESHOLD="$PART3"

        echo "Processing $FILE_NAME: window=$WINDOW, step=$STEP, threshold=$THRESHOLD"

        TIME_FILE="$SPECIES_DIR/time_mem/time_${WINDOW}_${STEP}.txt"
        TIME=""; MEM=""
        if [ -f "$TIME_FILE" ]; then
          TIME_MEM_LINE=$(grep -v '^[[:space:]]*$' "$TIME_FILE" | tail -n 1 || true)
          if [ -n "${TIME_MEM_LINE:-}" ]; then
            read -r TIME MEM <<< "$TIME_MEM_LINE"
          fi
        else
          echo "No time file file for ${WINDOW}_${STEP} in $SPECIES_DIR (time/mem will be empty)"
        fi

        ${OBTAIN_METRICS_BIN} "$REF_GFF" "$GFF" --output_folder "$TMP_DIR"

        METRICS_FILE="$TMP_DIR/${BASE}.csv"
        if [ ! -f "$METRICS_FILE" ]; then
          echo "No metrics file created for $BASE"
          continue
        fi

        METRICS_HEADER=$(head -n 1 "$METRICS_FILE" | tr -d '\r')
        METRICS_VALUES=$(tail -n 1 "$METRICS_FILE" | tr -d '\r')

        CSV_FILE="${RESULTS_GEANNO}/${MODEL_NAME}_${SPECIES_NAME}.csv"
        if [ ! -f "$CSV_FILE" ]; then
          echo "species,model,mutation_rate,window,step,threshold,time,mem,${METRICS_HEADER}" > "$CSV_FILE"
        fi

        echo "${SPECIES_NAME},${MODEL_NAME},${MUT_RATE},${WINDOW},${STEP},${THRESHOLD},${TIME},${MEM},${METRICS_VALUES}" >> "$CSV_FILE"

        # tratar de AUC-ROC
        if [[ "$WINDOW" == "1500" && "$STEP" == "50" && "$THRESHOLD" == "0.8" ]]; then
            
            ${OBTAIN_METRICS_BIN} "$REF_GFF" "$GFF" --output_folder "$TMP_DIR" --print_auc

            AUC_FILE="$TMP_DIR/${BASE}_auc.csv"
            if [ ! -f "$AUC_FILE" ]; then
                echo "WARN: não encontrei ${AUC_FILE}"
                continue
            fi

            if [ ! -f "$AUC_OUT/geanno_auc.csv" ]; then
                echo "species,model,mutation_rate,window,step,threshold,auc_roc,auc_prc" > "$AUC_OUT/geanno_auc.csv"
            fi

            AUC_VALUES=$(tail -n 1 "$AUC_FILE" | tr -d '\r')
            AUC_ROC=$(echo "$AUC_VALUES" | cut -d',' -f1)
            AUC_PRC=$(echo "$AUC_VALUES" | cut -d',' -f2)

            echo "${SPECIES_NAME},${MODEL_NAME},0,1500,50,0.8,${AUC_ROC},${AUC_PRC}" >> "$AUC_OUT/geanno_auc.csv"

        fi

        echo "Processed $FILE_NAME - $CSV_FILE"
      done
    done
  done
done

rm -rf $TMP_DIR
