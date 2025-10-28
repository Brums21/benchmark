#!/usr/bin/env bash
set -euo pipefail

source ${PLANT_DIR}/.venv/bin/activate

SPECIES_FOLDER="${BENCHMARK_DIR}/species/benchmark_species"

declare -A MODELS_LIST=(
  ["a_thaliana_model"]="models_genic_a_thaliana"
  ["a_thaliana_model_PCA"]="models_genic_a_thaliana_PCA"
  ["genemark_model"]="models_genic_genemark"
  ["genemark_model_PCA"]="models_genic_genemark_PCA"
  ["m_esculenta_model_PCA"]="models_genic_m_esculenta_PCA"
  ["o_sativa_model"]="models_genic_o_sativa"
  ["o_sativa_model_PCA"]="models_genic_o_sativa_PCA"
)

SPECIES_LIST=("arabidopsis_thaliana" "gossypium_raimondii" "manihot_esculenta" "oryza_sativa")

WINDOWS=(1000 1500)
STEPS=(25 50)
THRESHOLDS="0.2,0.3,0.4,0.5,0.6,0.7,0.8"

MUT_RATES=("0" "0.01" "0.04" "0.07")
MAX_JOBS=4

PYTHON_BIN="python3"
GEANNO="src/geanno.py"
RESULTS_ROOT="results/tools/GeAnno"

wait_for_slot() {
  while (( $(jobs -rp | wc -l) >= MAX_JOBS )); do
    wait -n || true
  done
}

mkdir -p "$RESULTS_ROOT"

for MR in "${MUT_RATES[@]}"; do
  MR_DIR="$RESULTS_ROOT/$MR"
  
  mkdir -p "$MR_DIR"

  for MODEL_NAME in "${!MODELS_LIST[@]}"; do

    MODEL="${MODELS_LIST[$MODEL_NAME]}"
    MODEL_DIR="$MR_DIR/$MODEL_NAME"

    mkdir -p "$MODEL_DIR"

    for SPECIES in "${SPECIES_LIST[@]}"; do
      SPEC_DIR="$MODEL_DIR/$SPECIES"
      mkdir -p "$SPEC_DIR"

      if [ "$MR" = "0" ]; then

        for W in "${WINDOWS[@]}"; do
          for S in "${STEPS[@]}"; do

            OUT_DIR="$SPEC_DIR/output"

            mkdir -p "$OUT_DIR" "$FIG_DIR"

            TIME_MEM_FILE="$SPEC_DIR/time_mem/time_${W}_${S}.txt"

            CMD=(
              "$PYTHON_BIN" "$GEANNO"
              -d "${SPECIES_FOLDER}/${SPECIES}/${SPECIES}_dna.fa"
              -m "$MODEL"
              -w "$W"
              -s "$S"
              -t "$THRESHOLDS"
              -o "$OUT_DIR"
            )

            wait_for_slot
            /usr/bin/time -a -f "%e\t%M" -o "$TIME_MEM_FILE" \
              bash -lc "${CMD[*]}" &

          done
        done

      else
        IN_FA="$SPEC_DIR/input.fa"

        if [ ! -f "$IN_FA" ]; then
          mkdir -p "$(dirname "$IN_FA")"
          gto_fasta_mutate -e "$MR" < "${SPECIES_FOLDER}/${SPECIES}/${SPECIES}_dna.fa" > "$IN_FA"
        fi

        OUT_DIR="$SPEC_DIR/output"
        mkdir -p "$OUT_DIR"

        CMD=(
          "$PYTHON_BIN" "$GEANNO"
          -d "$IN_FA"
          -m "$MODEL"
          -w "1500"
          -s "50"
          -t "$THRESHOLDS"
          -o "$OUT_DIR"
        )

        wait_for_slot
        bash -lc "${CMD[*]}" &
      fi
    done
  done
done

wait
echo "All GeAnno runs completed under: $RESULTS_ROOT"
