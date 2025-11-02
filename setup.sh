#!/bin/bash

BENCHMARK_DIR=$(pwd)
LIBS_DIR="${BENCHMARK_DIR}/libs"
ENV_FILE="${BENCHMARK_DIR}/env.sh"

mkdir -p "${LIBS_DIR}"

if ! grep -q "^export BENCHMARK_DIR=" "${ENV_FILE}" 2>/dev/null; then
    echo "export BENCHMARK_DIR=${BENCHMARK_DIR}" >> "${ENV_FILE}"
fi

source ${ENV_FILE}

update_env_path() {
    local tool_name=$1
    local tool_path=$2
    local env_file=$3

    local line="export PATH=\$BENCHMARK_DIR/${tool_path}:\$PATH"

    if grep -q "^export PATH=.*${tool_name}" "${env_file}" 2>/dev/null; then
        sed -i "s|^export PATH=.*${tool_name}.*|${line}|" "${env_file}"
    else
        echo "${line}" >> "${env_file}"
    fi
}

# Check if unzip and gzip are installed
command -v gzip >/dev/null 2>&1 || { 
    echo "Gzip is required but not installed. Installing..."

    apt-get download gzip && mv gzip_*.deb gzip.deb
    dpkg -x gzip.deb ${BENCHMARK_DIR}/libs/gzip/
    rm gzip.deb
    update_env_path "gzip/usr/bin/" "libs/gzip/usr/bin/" "${ENV_FILE}"
}

command -v unzip >/dev/null 2>&1 || { 
    echo "Unzip is required but not installed. Installing..."

    apt-get download unzip && mv unzip_*.deb unzip.deb

    mkdir -p ${BENCHMARK_DIR}/libs/unzip/
    dpkg -x unzip.deb ${BENCHMARK_DIR}/libs/unzip/
    rm unzip.deb
    update_env_path "unzip/usr/bin/" "libs/unzip/usr/bin/" "${ENV_FILE}"
}

command -v make >/dev/null 2>&1 || { 
    echo "Make is required but not installed. Installing..."

    apt-get download make && mv make_*.deb make.deb

    mkdir -p ${BENCHMARK_DIR}/libs/make/
    dpkg -x make.deb ${BENCHMARK_DIR}/libs/make/
    rm make.deb
    update_env_path "make/usr/bin/" "libs/make/usr/bin/" "${ENV_FILE}"
}

command -v cmake >/dev/null 2>&1 || { 
    echo "cmake is required but not installed. Installing..."

    cd ${BENCHMARK_DIR}/libs/
    wget https://github.com/Kitware/CMake/releases/download/v3.28.3/cmake-3.28.3-linux-x86_64.tar.gz
    tar -xzf cmake-3.28.3-linux-x86_64.tar.gz

    update_env_path "cmake-3.28.3-linux-x86_64/bin" "libs/cmake-3.28.3-linux-x86_64/bin" "${ENV_FILE}"
}

source ${ENV_FILE}

cd "${BENCHMARK_DIR}/setup"

chmod +rwx *.sh

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
