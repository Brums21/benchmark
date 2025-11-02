#!/bin/bash

if [ -z "$BENCHMARK_DIR" ]; then
    echo "Error: BENCHMARK_DIR is not set. Please source the env.sh file first."
    exit 1
fi

ENV_FILE="${BENCHMARK_DIR}/env.sh"
source ${ENV_FILE}

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
else
    echo "AUGUSTUS is already installed. Skipping..."
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

# GeAnno
echo -e "\n\GeAnno ------------------------------------------------------"
if [ ! -d "GeAnno" ]; then
    echo "Installing GeAnno..."
    git clone https://github.com/cobilab/GeAnno.git ${BENCHMARK_DIR}/tools/GeAnno
    cd ${BENCHMARK_DIR}/tools/GeAnno

    echo "export PLANT_DIR=$(pwd)" >> ~/.bashrc
    source ~/.bashrc

    chmod +x ./setup.sh
    ./setup.sh -t

    pip install -r requirements.txt
else 
    echo "GeAnno is already installed. Skipping..."
fi 

cd ${BENCHMARK_DIR}

echo -e "\n\nFinished installing all tools"

