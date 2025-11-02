#!/bin/bash
# This script downloads the DNA sequences and annotation from the first chromossome of 4 species

if [ -z "$BENCHMARK_DIR" ]; then
    echo "Error: BENCHMARK_DIR is not set. Please source the env.sh file first."
    exit 1
fi

ENV_FILE="${BENCHMARK_DIR}/env.sh"
source ${ENV_FILE}

SPECIES_FOLDER="${BENCHMARK_DIR}/species/benchmark_species"
REFERENCES_FOLDER="${BENCHMARK_DIR}/species/reference_species"


echo "Making species folder and entering it..."
mkdir ${SPECIES_FOLDER}
cd ${SPECIES_FOLDER}

# well annotated species

# Arabidopsis thaliana ---------------------------------------------------------------------------------
echo "Arabidopsis thaliana"
mkdir arabidopsis_thaliana
cd arabidopsis_thaliana

echo "Downloading DNA sequence..."
if [ ! -f "arabidopsis_thaliana_dna.fa" ]; then
    wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/fasta/arabidopsis_thaliana/dna/Arabidopsis_thaliana.TAIR10.dna.chromosome.1.fa.gz -O arabidopsis_thaliana_dna.fa.gz
    gunzip arabidopsis_thaliana_dna.fa.gz
else
    echo "A. thaliana sequence already downloaded. Skipping..."
fi

echo "Downloading annotation..."
if [ ! -f "arabidopsis_thaliana_annotation.gff3" ]; then
    wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/gff3/arabidopsis_thaliana/Arabidopsis_thaliana.TAIR10.60.chromosome.1.gff3.gz -O arabidopsis_thaliana_annotation.gff3.gz
    gunzip arabidopsis_thaliana_annotation.gff3.gz
else
    echo "A. thaliana annotation already downloaded. Skipping..."
fi
cd ..
echo "A. thaliana downloaded."


# Oryza sativa -------------------------------------------------------------------------------------
echo "Oryza sativa"
mkdir oryza_sativa
cd oryza_sativa

echo "Downloading DNA sequence..."
if [ ! -f "oryza_sativa_dna.fa" ]; then
    wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/fasta/oryza_sativa/dna/Oryza_sativa.IRGSP-1.0.dna.chromosome.1.fa.gz -O oryza_sativa_dna.fa.gz
    gunzip oryza_sativa_dna.fa.gz
else
    echo "O. sativa sequence already downloaded. Skipping..."
fi

echo "Downloading annotation..."
if [ ! -f "oryza_sativa_annotation.gff3" ]; then
    wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/gff3/oryza_sativa/Oryza_sativa.IRGSP-1.0.60.chromosome.1.gff3.gz -O oryza_sativa_annotation.gff3.gz
    gunzip oryza_sativa_annotation.gff3.gz
else
    echo "O. sativa annotation already downloaded. Skipping..."
fi
cd ..
echo "O. sativa downloaded."


# 'Unusual' species

# Gossypium raimondii - cotton ------------------------------------------------------------------------
echo "Gossypium raimondii"
mkdir gossypium_raimondii
cd gossypium_raimondii

echo "Downloading DNA sequence..."
if [ ! -f "gossypium_raimondii_dna.fa" ]; then
    wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/fasta/gossypium_raimondii/dna/Gossypium_raimondii.Graimondii2_0_v6.dna.chromosome.1.fa.gz -O gossypium_raimondii_dna.fa.gz
    gunzip gossypium_raimondii_dna.fa.gz
else
    echo "Gossypium raimondii sequence already downloaded. Skipping..."
fi

echo "Downloading annotation..."
if [ ! -f "gossypium_raimondii_annotation.gff3" ]; then
    wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/gff3/gossypium_raimondii/Gossypium_raimondii.Graimondii2_0_v6.60.chromosome.1.gff3.gz -O gossypium_raimondii_annotation.gff3.gz
    gunzip gossypium_raimondii_annotation.gff3.gz
else
    echo "Gossypium raimondii sequence already downloaded. Skipping..."
fi
cd ..
echo "G. raimondii downloaded."


# Manihot esculenta - cassava ------------------------------------------------------------------------
echo "Manihot esculenta"
mkdir manihot_esculenta
cd manihot_esculenta

echo "Downloading DNA sequence..."
if [ ! -f "manihot_esculenta_dna.fa" ]; then
    wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/fasta/manihot_esculenta/dna/Manihot_esculenta.M.esculenta_v8.dna.primary_assembly.CM004387.2.fa.gz -O manihot_esculenta_dna.fa.gz
    gunzip manihot_esculenta_dna.fa.gz
else
    echo "Manihot esculenta sequence already downloaded. Skipping..."
fi

echo "Downloading annotation..."
if [ ! -f "manihot_esculenta_annotation.gff3" ]; then
    wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/gff3/manihot_esculenta/Manihot_esculenta.M.esculenta_v8.60.primary_assembly.CM004387.2.gff3.gz -O manihot_esculenta_annotation.gff3.gz
    gunzip manihot_esculenta_annotation.gff3.gz
else
    echo "Manihot esculenta sequence already downloaded. Skipping..."
fi
cd ..
echo "M. esculenta downloaded."

cd ..


echo "Downloading now reference species to be used in tools that need evidence"
echo "Making reference_species folder and entering it..."

mkdir -p ${REFERENCES_FOLDER}
cd ${REFERENCES_FOLDER} || exit 1

# Arabidopsis lyrata ------------------------------------------------------------------------
echo "Arabidopsis lyrata"
mkdir arabidopsis_lyrata
cd arabidopsis_lyrata

echo "Downloading DNA sequence..."
if [ ! -f "arabidopsis_lyrata_dna.fa" ]; then
    wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/fasta/arabidopsis_lyrata/dna/Arabidopsis_lyrata.v.1.0.dna.toplevel.fa.gz -O arabidopsis_lyrata_dna.fa.gz
    gunzip arabidopsis_lyrata_dna.fa.gz
else
    echo "Manihot esculenta sequence already downloaded. Skipping..."
fi

echo "Downloading annotation..."
if [ ! -f "arabidopsis_lyrata_annotation.gff3" ]; then
    wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/gff3/arabidopsis_lyrata/Arabidopsis_lyrata.v.1.0.60.gff3.gz -O arabidopsis_lyrata_annotation.gff3.gz
    gunzip arabidopsis_lyrata_annotation.gff3.gz
else
    echo "Arabidopsis lyrata sequence already downloaded. Skipping..."
fi
cd ..
echo "A. lyrata downloaded."


# Oryza nivara ------------------------------------------------------------------------
echo "Oryza nivara"
mkdir oryza_nivara
cd oryza_nivara

echo "Downloading DNA sequence..."
if [ ! -f "oryza_nivara_dna.fa" ]; then
    wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/fasta/oryza_nivara/dna/Oryza_nivara.Oryza_nivara_v1.0.dna.toplevel.fa.gz -O oryza_nivara_dna.fa.gz
    gunzip oryza_nivara_dna.fa.gz
else
    echo "Oryza nivara sequence already downloaded. Skipping..."
fi

echo "Downloading annotation..."
if [ ! -f "oryza_nivara_annotation.gff3" ]; then
    wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/gff3/oryza_nivara/Oryza_nivara.Oryza_nivara_v1.0.60.gff3.gz -O oryza_nivara_annotation.gff3.gz
    gunzip oryza_nivara_annotation.gff3.gz
else
    echo "Oryza nivara sequence already downloaded. Skipping..."
fi
cd ..
echo "O. nivara downloaded."


# Brassica napus ------------------------------------------------------------------------
echo "Brassica napus"
mkdir brassica_napus
cd brassica_napus

echo "Downloading DNA sequence..."
if [ ! -f "brassica_napus_dna.fa" ]; then
    wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/fasta/brassica_napus/dna/Brassica_napus.AST_PRJEB5043_v1.dna.toplevel.fa.gz -O brassica_napus_dna.fa.gz
    gunzip brassica_napus_dna.fa.gz
else
    echo "Brassica napus sequence already downloaded. Skipping..."
fi

echo "Downloading annotation..."
if [ ! -f "brassica_napus_annotation.gff3" ]; then
    wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/gff3/brassica_napus/Brassica_napus.AST_PRJEB5043_v1.60.gff3.gz -O brassica_napus_annotation.gff3.gz
    gunzip brassica_napus_annotation.gff3.gz
else
    echo "Brassica napus sequence already downloaded. Skipping..."
fi
cd ..
echo "B. napus downloaded."


# Zea mays ------------------------------------------------------------------------
echo "Zea mays"
mkdir zea_mays
cd zea_mays

echo "Downloading DNA sequence..."
if [ ! -f "zea_mays_dna.fa" ]; then
    wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/fasta/zea_mays/dna/Zea_mays.Zm-B73-REFERENCE-NAM-5.0.dna.toplevel.fa.gz -O zea_mays_dna.fa.gz
    gunzip zea_mays_dna.fa.gz
else
    echo "Zea mays sequence already downloaded. Skipping..."
fi

echo "Downloading annotation..."
if [ ! -f "zea_mays_annotation.gff3" ]; then
    wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/gff3/zea_mays/Zea_mays.Zm-B73-REFERENCE-NAM-5.0.60.gff3.gz -O zea_mays_annotation.gff3.gz
    gunzip zea_mays_annotation.gff3.gz
else
    echo "Zea mays sequence already downloaded. Skipping..."
fi
cd ..
echo "Z. mays downloaded."


# Zea mays ------------------------------------------------------------------------
echo "Corchorus capsularis"
mkdir corchorus_capsularis
cd corchorus_capsularis

echo "Downloading DNA sequence..."
if [ ! -f "corchorus_capsularis_dna.fa" ]; then
    wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/fasta/corchorus_capsularis/dna/Corchorus_capsularis.CCACVL1_1.0.dna.toplevel.fa.gz -O corchorus_capsularis_dna.fa.gz
    gunzip corchorus_capsularis_dna.fa.gz
else
    echo "Corchorus capsularis sequence already downloaded. Skipping..."
fi

echo "Downloading annotation..."
if [ ! -f "corchorus_capsularis_annotation.gff3" ]; then
    wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/gff3/corchorus_capsularis/Corchorus_capsularis.CCACVL1_1.0.60.gff3.gz -O corchorus_capsularis_annotation.gff3.gz
    gunzip corchorus_capsularis_annotation.gff3.gz
else
    echo "Corchorus capsularis sequence already downloaded. Skipping..."
fi
cd ..
echo "C. capsularis downloaded."

echo "Finished getting DNA and annotations for all species"