#!/bin/bash

mkdir -p "res_aggr"; cd "res_aggr"

# arabidopsis_thaliana brassica_napus hordeum_vulgare oryza_sativa solanum_lycopersicum

for SPECIES in triticum_aestivum zea_mays; do

    # ground truth: old/species_old/arabidopsis_thaliana
    # annotation: old/results_old/GeneMark-ES/arabidopsis_thaliana

    #clean the chromossome names to respect nomenclature in the annotation ground truth
    python ../modify_output.py ../old/results_old/GeneMark-ES/${SPECIES}/genemark.gtf

    # parse to gff3
    echo "../old/results_old/GeneMark-ES/${SPECIES}/genemark_cleaned.gtf"
    agat_convert_sp_gxf2gxf.pl -g ../old/results_old/GeneMark-ES/${SPECIES}/genemark_cleaned.gtf -o ${SPECIES}_genemark_cleaned.gff3
    #gt gtf_to_gff3 -o ${SPECIES}_genemark_cleaned.gff3 -tidy ${SPECIES}_genemark_cleaned.gtf

    #sort
    gt gff3 -force -tidy -sort -retainids -checkids -o tmp_annot.gff3 ${SPECIES}_genemark_cleaned.gff3

    gt eval ../old/species_old/${SPECIES}/${SPECIES}_annotation.gff3 tmp_annot.gff3 > results_${SPECIES}.txt

    # remove temporary file
    rm ../old/results_old/GeneMark-ES/${SPECIES}/genemark_cleaned.gtf ${SPECIES}_genemark_cleaned.gff3 tmp_annot.gff3 


done
