#!/bin/bash

BENCHMARK_DIR=$(pwd)

echo "" >> ~/.bashrc
echo "export BENCHMARK_DIR=${BENCHMARK_DIR}" >> ~/.bashrc

# Check if unzip and gzip are installed
command -v gzip >/dev/null 2>&1 || { 
    echo "Gzip is required but not installed. Installing..."

    apt-get download gzip && mv gzip_*.deb gzip.deb
    dpkg -x gzip.deb ${BENCHMARK_DIR}/libs/gzip/
    rm gzip.deb
    echo 'export PATH=${BENCHMARK_DIR}/libs/gzip/usr/bin/:$PATH' >> ~/.bashrc
}

command -v unzip >/dev/null 2>&1 || { 
    echo "Unzip is required but not installed. Installing..."

    apt-get download unzip && mv unzip_*.deb unzip.deb

    mkdir -p ${BENCHMARK_DIR}/libs/unzip/
    dpkg -x unzip.deb ${BENCHMARK_DIR}/libs/unzip/
    rm unzip.deb
    echo 'export PATH=${BENCHMARK_DIR}/libs/unzip/usr/bin/:$PATH' >> ~/.bashrc
}

command -v make >/dev/null 2>&1 || { 
    echo "Make is required but not installed. Installing..."

    apt-get download make && mv make_*.deb make.deb

    mkdir -p ${BENCHMARK_DIR}/libs/make/
    dpkg -x make.deb ${BENCHMARK_DIR}/libs/make/
    rm make.deb
    echo 'export PATH=${BENCHMARK_DIR}/libs/make/usr/bin/:$PATH' >> ~/.bashrc
}

command -v cmake >/dev/null 2>&1 || { 
    echo "cmake is required but not installed. Installing..."

    cd ${BENCHMARK_DIR}/libs/
    wget https://github.com/Kitware/CMake/releases/download/v3.28.3/cmake-3.28.3-linux-x86_64.tar.gz
    tar -xzf cmake-3.28.3-linux-x86_64.tar.gz

    echo 'export PATH=$BENCHMARK_DIR/libs/cmake-3.28.3-linux-x86_64/bin:$PATH' >> ~/.bashrc

}

source ~/.bashrc

cd setup/

# get species 
./get_species_info.sh

# get RNA-seq data and generate config files
./rna_seq_data.sh

# get hints
./hints_generator.sh

# get tools
./get_tools.sh

#install tool's dependencies
./install_dependencies.sh