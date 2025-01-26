#!/bin/bash

echo "Making species folder and entering it"
mkdir species
cd species

# Arabidopsis thaliana ---------------------------------------------------------------------------------
echo "Arabidopsis thaliana"
mkdir arabidopsis_thaliana
cd arabidopsis_thaliana

# Get DNA sequence
wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/fasta/arabidopsis_thaliana/dna/Arabidopsis_thaliana.TAIR10.dna.toplevel.fa.gz -O arabidopsis_thaliana_dna.fa.gz
gunzip arabidopsis_thaliana_dna.fa.gz

# Get annotation
wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/gff3/arabidopsis_thaliana/Arabidopsis_thaliana.TAIR10.60.gff3.gz -O arabidopsis_thaliana_annotation.gff3.gz
gunzip arabidopsis_thaliana_annotation.gff3.gz
cd ..

# Brassica napus ---------------------------------------------------------------------------------
echo "Brassica napus"
mkdir brassica_napus
cd brassica_napus

# Get DNA sequence
wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/fasta/brassica_napus/dna/Brassica_napus.AST_PRJEB5043_v1.dna.toplevel.fa.gz -O brassica_napus_dna.fa.gz
gunzip brassica_napus_dna.fa.gz

# Get annotation
wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/gff3/brassica_napus/Brassica_napus.AST_PRJEB5043_v1.60.gff3.gz -O brassica_napus_annotation.gff3.gz
gunzip brassica_napus_annotation.gff3.gz
cd ..

# Hordeum vulgare ---------------------------------------------------------------------------------
echo "Hordeum vulgare"
mkdir hordeum_vulgare
cd hordeum_vulgare

# Get DNA sequence
wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/fasta/hordeum_vulgare/dna/Hordeum_vulgare.MorexV3_pseudomolecules_assembly.dna.toplevel.fa.gz -O hordeum_vulgare_dna.fa.gz
gunzip hordeum_vulgare_dna.fa.gz

# Get annotation
wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/gff3/hordeum_vulgare/Hordeum_vulgare.MorexV3_pseudomolecules_assembly.60.gff3.gz -O hordeum_vulgare_annotation.gff3.gz
gunzip hordeum_vulgare_annotation.gff3.gz
cd ..


# Oryza sativa ---------------------------------------------------------------------------------
echo "Oryza sativa"
mkdir oryza_sativa
cd oryza_sativa

# Get DNA sequence
wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/fasta/oryza_sativa/dna/Oryza_sativa.IRGSP-1.0.dna.toplevel.fa.gz -O oryza_sativa_dna.fa.gz
gunzip oryza_sativa_dna.fa.gz

# Get annotation
wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/gff3/oryza_sativa/Oryza_sativa.IRGSP-1.0.60.gff3.gz -O oryza_sativa_annotation.gff3.gz
gunzip oryza_sativa_annotation.gff3.gz
cd ..


# Solanum Lycopersicum ---------------------------------------------------------------------------------
echo "Solanum Lycopersicum"
mkdir solanum_lycopersicum
cd solanum_lycopersicum

# Get DNA sequence
wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/fasta/solanum_lycopersicum/dna/Solanum_lycopersicum.SL3.0.dna.toplevel.fa.gz -O solanum_lycopersicum_dna.fa.gz
gunzip solanum_lycopersicum_dna.fa.gz

# Get annotation
wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/gff3/solanum_lycopersicum/Solanum_lycopersicum.SL3.0.60.gff3.gz -O solanum_lycopersicum_annotation.gff3.gz
gunzip solanum_lycopersicum_annotation.gff3.gz
cd ..


# Triticum Aestivum ---------------------------------------------------------------------------------
echo "Triticum Aestivum"
mkdir triticum_aestivum
cd triticum_aestivum

# Get DNA sequence
wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/fasta/triticum_aestivum/dna/Triticum_aestivum.IWGSC.dna.toplevel.fa.gz -O triticum_aestivum_dna.fa.gz
gunzip triticum_aestivum_dna.fa.gz

# Get annotation
wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/gff3/triticum_aestivum/Triticum_aestivum.IWGSC.60.gff3.gz -O triticum_aestivum_annotation.gff3.gz
gunzip triticum_aestivum_annotation.gff3.gz
cd ..


# Zea Mays ---------------------------------------------------------------------------------
echo "Zea Mays"
mkdir zea_mays
cd zea_mays

# Get DNA sequence
wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/fasta/zea_mays/dna/Zea_mays.Zm-B73-REFERENCE-NAM-5.0.dna.toplevel.fa.gz -O zea_mays_dna.fa.gz
gunzip zea_mays_dna.fa.gz

# Get annotation
wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/gff3/zea_mays/Zea_mays.Zm-B73-REFERENCE-NAM-5.0.60.gff3.gz -O zea_mays_annotation.gff3.gz
gunzip zea_mays_annotation.gff3.gz
cd ..

echo "Finished getting DNA and annotations for all species"