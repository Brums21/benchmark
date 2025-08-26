#!/bin/bash

BENCHMARK_DIR="$HOME/benchmark"

mkdir -p ${BENCHMARK_DIR}/tools
cd ${BENCHMARK_DIR}/tools || exit 1

# GeneMark-ETP
echo -e "\n\nGeneMark-ETP ------------------------------------------------------"
if [ ! -d "GeneMark-ETP" ]; then
    echo "Installing GeneMark-ETP..."
    wget https://github.com/gatech-genemark/GeneMark-ETP/releases/download/etp-v1.02-preprint/GeneMark-ETP.tar.gz -O GeneMark-ETP.tar.gz
    tar -xvzf GeneMark-ETP.tar.gz
    rm GeneMark-ETP.tar.gz
else
    echo "GeneMark-ETP is already installed. Skipping..."
fi

# GeneMark-ES and GeneMark-EP+ -> see README.md

# AUGUSTUS
echo -e "\n\nAUGUSTUS ------------------------------------------------------"
if [ ! -d "Augustus-3.5.0" ]; then
    echo "Instaling AUGUSTUS..."
    wget https://github.com/Gaius-Augustus/Augustus/archive/refs/tags/v3.5.0.tar.gz -O Augustus-3.5.0.tar.gz
    tar -xvzf Augustus-3.5.0.tar.gz
    rm Augustus-3.5.0.tar.gz

    # make augustus
    cd Augustus-3.5.0
    make augustus
    cd ..
else
    echo "AUGUSTUS is already installed. Skipping..."
fi

# Seqping
echo -e "\n\nSeqping ------------------------------------------------------"
if [ ! -d "seqping_0.1.45.1" ]; then
    echo "Installing Seqping..."
    wget https://sourceforge.net/projects/seqping/files/latest/download -O Seqping_0.1.45.1.tar.gz
    tar -xvzf Seqping_0.1.45.1.tar.gz
    rm Seqping_0.1.45.1.tar.gz
else
    echo "Seqping is already installed. Skipping..."
fi

# SNAP
echo -e "\n\nSNAP ------------------------------------------------------"
if [ ! -d "SNAP-master" ]; then
    echo "Instaling SNAP..."
    wget https://github.com/KorfLab/SNAP/archive/refs/heads/master.zip -O SNAP.zip
    unzip SNAP.zip
    rm SNAP.zip
else
    echo "SNAP is already installed. Skipping..."
fi

# GeMoMa
echo -e "\n\nGeMoMa ------------------------------------------------------"
if [ ! -d "GeMoMa" ]; then
    echo "Installing GeMoMa..."
    wget http://www.jstacs.de/download.php?which=GeMoMa -O GeMoMa.zip
    mkdir GeMoMa
    mv GeMoMa.zip GeMoMa/
    cd GeMoMa
    unzip GeMoMa.zip
    rm GeMoMa.zip
    cd ..
else 
    echo "GeMoMa is already installed. Skipping..."
fi 

cd ${BENCHMARK_DIR}

echo -e "\n\nFinished installing all tools"

