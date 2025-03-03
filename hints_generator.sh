#!/bin/bash

mkdir -p hints/temp
cd hints/temp || exit 1

# 1o - fazer download de todas as sequencias de proteinas a serem usadas 

# Arabidopsis lyrata
echo "Downloading protein fasta sequence for A. lyrata..."
if [ ! -f "arabidopsis_lyrata_pep.fa" ]; then
    wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/fasta/arabidopsis_lyrata/pep/Arabidopsis_lyrata.v.1.0.pep.all.fa.gz -O arabidopsis_lyrata_pep.fa.gz
    gunzip arabidopsis_lyrata_pep.fa.gz
else
    echo "A. lyrata protein sequence already downloaded. Skipping..."
fi

# Arabidopsis halleri
echo "Downloading protein fasta sequence for A. halleu..."
if [ ! -f "arabidopsis_halleri_pep.fa" ]; then
    wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/fasta/arabidopsis_halleri/pep/Arabidopsis_halleri.Ahal2.2.pep.all.fa.gz -O arabidopsis_halleri_pep.fa.gz
    gunzip arabidopsis_halleri_pep.fa.gz
else
    echo "A. halleri sequence already downloaded. Skipping..."
fi

# Eutrema salsugineum
echo "Downloading protein fasta sequence for E. salsugineum..."
if [ ! -f "eutrema_salsugineum_pep.fa" ]; then
    wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/fasta/eutrema_salsugineum/pep/Eutrema_salsugineum.Eutsalg1_0.pep.all.fa.gz -O eutrema_salsugineum_pep.fa.gz
    gunzip eutrema_salsugineum_pep.fa.gz
else
    echo "E. salsugineum sequence already downloaded. Skipping..."
fi

# Brassica napus
echo "Downloading protein fasta sequence for B. napus..."
if [ ! -f "brassica_napus_pep.fa" ]; then
    wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/fasta/brassica_napus/pep/Brassica_napus.AST_PRJEB5043_v1.pep.all.fa.gz -O brassica_napus_pep.fa.gz
    gunzip brassica_napus_pep.fa.gz
else
    echo "B. napus sequence already downloaded. Skipping..."
fi

# Oryza nivara
echo "Downloading protein fasta sequence for O. nivara..."
if [ ! -f "oryza_nivara_pep.fa" ]; then
    wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/fasta/oryza_nivara/pep/Oryza_nivara.Oryza_nivara_v1.0.pep.all.fa.gz -O oryza_nivara_pep.fa.gz
    gunzip oryza_nivara_pep.fa.gz
else
    echo "A. nivara sequence already downloaded. Skipping..."
fi

# Oryza barthii
echo "Downloading protein fasta sequence for O. barthii..."
if [ ! -f "oryza_barthii_pep.fa" ]; then
    wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/fasta/oryza_barthii/pep/Oryza_barthii.O.barthii_v1.pep.all.fa.gz -O oryza_barthii_pep.fa.gz
    gunzip oryza_barthii_pep.fa.gz
else
    echo "O. barthii sequence already downloaded. Skipping..."
fi

# Zea Mays
echo "Downloading protein fasta sequence for Z. mays..."
if [ ! -f "zea_mays_pep.fa" ]; then
    wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/fasta/zea_mays/pep/Zea_mays.Zm-B73-REFERENCE-NAM-5.0.pep.all.fa.gz -O zea_mays_pep.fa.gz
    gunzip zea_mays_pep.fa.gz
else
    echo "Z. mays sequence already downloaded. Skipping..."
fi

# H. vulgare
echo "Downloading protein fasta sequence for H. vulgare..."
if [ ! -f "hordeum_vulgare_pep.fa" ]; then
    wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/fasta/hordeum_vulgare/pep/Hordeum_vulgare.MorexV3_pseudomolecules_assembly.pep.all.fa.gz -O hordeum_vulgare_pep.fa.gz
    gunzip hordeum_vulgare_pep.fa.gz
else
    echo "H. vulgare sequence already downloaded. Skipping..."
fi

# C. capsularis
echo "Downloading protein fasta sequence for C. capsularis..."
if [ ! -f "corchorus_capsularis_pep.fa" ]; then
    wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/fasta/corchorus_capsularis/pep/Corchorus_capsularis.CCACVL1_1.0.pep.all.fa.gz -O corchorus_capsularis_pep.fa.gz
    gunzip corchorus_capsularis_pep.fa.gz
else
    echo "C. capsularis sequence already downloaded. Skipping..."
fi

# T. cacao
echo "Downloading protein fasta sequence for T. cacao..."
if [ ! -f "theobroma_cacao_pep.fa" ]; then
    wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-60/fasta/theobroma_cacao/pep/Theobroma_cacao.Theobroma_cacao_20110822.pep.all.fa.gz -O theobroma_cacao_pep.fa.gz
    gunzip theobroma_cacao_pep.fa.gz
else
    echo "T. cacao sequence already downloaded. Skipping..."
fi

# 2o - organizar sets para servir como inputs 

# 2o - organizar sets para servir como inputs 

# A. thaliana including same genus
cat arabidopsis_lyrata_pep.fa arabidopsis_halleri_pep.fa > ../arabidopsis_thaliana_genus.fa

# A. thaliana including same order
cat eutrema_salsugineum_pep.fa brassica_napus_pep.fa > ../arabidopsis_thaliana_order.fa

# A. thaliana no order
cat zea_mays_pep.fa hordeum_vulgare_pep.fa > ../arabidopsis_thaliana_far.fa

# O. sativa including same genus
cat oryza_nivara_pep.fa oryza_barthii_pep.fa > ../oryza_sativa_genus.fa

# O. sativa including same order
cat zea_mays_pep.fa hordeum_vulgare_pep.fa > ../oryza_sativa_order.fa

# O. sativa no order
cat eutrema_salsugineum_pep.fa brassica_napus_pep.fa > ../oryza_sativa_far.fa

# G. raimondii including same order
cat corchorus_capsularis_pep.fa theobroma_cacao_pep.fa > ../gossypium_raimondii_order.fa

# G. raimondii no order
cat zea_mays_pep.fa hordeum_vulgare_pep.fa > ../gossypium_raimondii_far.fa

# M. esculenta no order
cat zea_mays_pep.fa hordeum_vulgare_pep.fa > ../manihot_esculenta_far.fa

# 3o - Eliminar ficheiros temporários e manter apenas as combinações
cd ..
rm -r temp/
