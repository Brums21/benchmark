#!/bin/bash

mkdir -p "res_aggr"; cd "res_aggr"

# arabidopsis_thaliana brassica_napus hordeum_vulgare oryza_sativa solanum_lycopersicum

for SPECIES in oryza_sativa solanum_lycopersicum triticum_aestivum zea_mays; do

    # ground truth: old/species_old/arabidopsis_thaliana
    # annotation: old/results_old/GeneMark-ES/arabidopsis_thaliana

    echo "Splitting and cleaning the Genemark output files for ${SPECIES}"

    #clean the chromossome names to respect nomenclature in the annotation ground truth
    python ../modify_output.py ../old/results_old/GeneMark-ES/${SPECIES}/genemark.gtf

    merged_gff3="${SPECIES}_genemark_cleaned_merged.gff3"
    > "$merged_gff3"

    echo "##gff-version 3" >> "$merged_gff3"

    echo "Parsing each split to gff3 and merging it"
    for file in ../old/results_old/GeneMark-ES/${SPECIES}/genemark_cleaned_*.gtf; do
        if [[ -f "$file" ]]; then
            echo "Processing file: $file"

            identifier=$(basename "$file" | sed -E 's/genemark_cleaned_(.*)\.gtf/\1/')

            output_gff3="${SPECIES}_genemark_cleaned_${identifier}.gff3"
            output_gff_sorted="${SPECIES}_genemark_cleaned_${identifier}_sorted.gff3"
            agat_convert_sp_gxf2gxf.pl -g "$file" -o "$output_gff3"
            #gt gtf_to_gff3 -o "${SPECIES}_genemark_cleaned_${identifier}.gff3" -tidy "$file"

            gt gff3 -sort -tidy -o "$output_gff_sorted" "$output_gff3"
        
            tail -n +2 "$output_gff_sorted" >> "$merged_gff3"

            rm "$file" "$output_gff3" "$output_gff_sorted"
            rm -f *.log

        fi
    done
    

    echo "Sorting the annotation file"
    #sort
    gt gff3 -force -tidy -sort -addids -o tmp_annot.gff3 $merged_gff3

    echo "Evaluating metrics"
    gt eval ../old/species_old/${SPECIES}/${SPECIES}_annotation.gff3 tmp_annot.gff3 > results_${SPECIES}.txt

    # remove temporary files
    #rm $merged_gff3 tmp_annot.gff3

done

echo "Finished getting all metrics for all species"
