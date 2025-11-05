#!/bin/bash

if [ -z "$BENCHMARK_DIR" ]; then
    echo "Error: BENCHMARK_DIR is not set. Please source the env.sh file first."
    exit 1
fi

ENV_FILE="${BENCHMARK_DIR}/env.sh"

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

update_env_var() {
    local var_name=$1
    local var_value=$2
    local env_file=$3

    local line="export ${var_name}=${var_value}"

    [ -f "${env_file}" ] || touch "${env_file}"

    if grep -q "^export ${var_name}=" "${env_file}" 2>/dev/null; then
        sed -i "s|^export ${var_name}=.*|${line}|" "${env_file}"
    else
        echo "${line}" >> "${env_file}"
    fi
}

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

mkdir -p ${BENCHMARK_DIR}/libs/

# GeMoMa
wget https://mmseqs.com/latest/mmseqs-linux-sse2.tar.gz -O ${BENCHMARK_DIR}/libs/mmseqs-linux-sse2.tar.gz
tar xvfz ${BENCHMARK_DIR}/libs/mmseqs-linux-sse2.tar.gz -C ${BENCHMARK_DIR}/libs/
rm ${BENCHMARK_DIR}/libs/mmseqs-linux-sse2.tar.gz
update_env_path "mmseqs/bin/" "libs/mmseqs/bin/" "${ENV_FILE}"

#AUGUSTUS

# SQLite, GSL, LPsolve, BamTools, samtools
packages=(libsqlite3-dev libgsl-dev liblpsolve55-dev libbamtools-dev samtools)

for package in ${packages[@]}; do

    command -v $package >/dev/null 2>&1 || { 
        echo "$package is required but not installed. Installing..."

        apt-get download $package
        deb_file=$(ls ${package}_*.deb | head -n1)
        dpkg -x "$deb_file" "${BENCHMARK_DIR}/libs/${package}/"
        rm -f "$deb_file"

    }
done

#Zlib
mkdir -p ${BENCHMARK_DIR}/libs/zlib/zlib_build
cd ${BENCHMARK_DIR}/libs/zlib/zlib_build
wget -O zlib-1.2.11.tar.gz https://zlib.net/fossils/zlib-1.2.11.tar.gz
tar xzf zlib-1.2.11.tar.gz
cd ${BENCHMARK_DIR}/libs/zlib/zlib_build/zlib-1.2.11
./configure --prefix=${BENCHMARK_DIR}/libs/zlib/zlib_install
make
make install

if grep -q "^export ZLIB_INCLUDE=" "${ENV_FILE}" 2>/dev/null; then
    sed -i "s|^export ZLIB_INCLUDE=.*|export ZLIB_INCLUDE=\${BENCHMARK_DIR}/libs/zlib/zlib_install/include|" "${ENV_FILE}"
else
    echo 'export ZLIB_INCLUDE=${BENCHMARK_DIR}/libs/zlib/zlib_install/include' >> "${ENV_FILE}"
fi

if grep -q "^export ZLIB_LIBRARY_PATH=" "${ENV_FILE}" 2>/dev/null; then
    sed -i "s|^export ZLIB_LIBRARY_PATH=.*|export ZLIB_LIBRARY_PATH=\${BENCHMARK_DIR}/libs/zlib/zlib_install/lib|" "${ENV_FILE}"
else
    echo 'export ZLIB_LIBRARY_PATH=${BENCHMARK_DIR}/libs/zlib/zlib_install/lib' >> "${ENV_FILE}"
fi


source ${ENV_FILE}

# Boost
mkdir -p ${BENCHMARK_DIR}/libs/boost/boost_build
cd ${BENCHMARK_DIR}/libs/boost/boost_build
wget -O boost_1_76_0.tar.gz https://archives.boost.io/release/1.76.0/source/boost_1_76_0.tar.gz
tar xzf boost_1_76_0.tar.gz
cd  ${BENCHMARK_DIR}/libs/boost/boost_build/boost_1_76_0
./bootstrap.sh --prefix=${BENCHMARK_DIR}/libs/boost/boost_install --with-libraries=all
./b2 install --prefix=${BENCHMARK_DIR}/libs/boost/boost_install


# MySQL
mkdir ${BENCHMARK_DIR}/libs/mysql
cd ${BENCHMARK_DIR}/libs/mysql

wget        libmysql++3v5_3.2.5-1build1_amd64.deb http://de.archive.ubuntu.com/ubuntu/pool/universe/m/mysql++/libmysql++3v5_3.2.5-1build1_amd64.deb
dpkg-deb -x libmysql++3v5_3.2.5-1build1_amd64.deb ${BENCHMARK_DIR}/libs/mysql/mysql_install

wget        libmysql++-dev_3.2.5-1build1_amd64.deb http://de.archive.ubuntu.com/ubuntu/pool/universe/m/mysql++/libmysql++-dev_3.2.5-1build1_amd64.deb
dpkg-deb -x libmysql++-dev_3.2.5-1build1_amd64.deb ${BENCHMARK_DIR}/libs/mysql/mysql_install

wget        libmysqlclient21_8.0.23-0ubuntu0.20.04.1_amd64.deb http://security.ubuntu.com/ubuntu/pool/main/m/mysql-8.0/libmysqlclient21_8.0.23-0ubuntu0.20.04.1_amd64.deb
dpkg-deb -x libmysqlclient21_8.0.23-0ubuntu0.20.04.1_amd64.deb ${BENCHMARK_DIR}/libs/mysql/mysql_install

wget        libmysqlclient-dev_8.0.23-0ubuntu0.20.04.1_amd64.deb http://security.ubuntu.com/ubuntu/pool/main/m/mysql-8.0/libmysqlclient-dev_8.0.23-0ubuntu0.20.04.1_amd64.deb
dpkg-deb -x libmysqlclient-dev_8.0.23-0ubuntu0.20.04.1_amd64.deb ${BENCHMARK_DIR}/libs/mysql/mysql_install

## SuiteSparse

if [ -f "${BENCHMARK_DIR}/libs/suitesparse/lib/libcolamd.so" ] && [ -f "${BENCHMARK_DIR}/libs/suitesparse/include/colamd.h.so" ]; then
    echo "SuiteSparse already installed. Skipping..."
else
    wget https://github.com/DrTimothyAldenDavis/SuiteSparse/archive/refs/tags/v5.4.0.zip -O ${BENCHMARK_DIR}/libs/SuiteSparse-5.4.0.zip
    unzip ${BENCHMARK_DIR}/libs/SuiteSparse-5.4.0.zip -d ${BENCHMARK_DIR}/libs/
    rm ${BENCHMARK_DIR}/libs/SuiteSparse-5.4.0.zip

    cd ${BENCHMARK_DIR}/libs/SuiteSparse-5.4.0
    make install INSTALL=${BENCHMARK_DIR}/libs/suitesparse
    cd ${BENCHMARK_DIR}/libs/SuiteSparse-5.4.0/COLAMD
    make install INSTALL=${BENCHMARK_DIR}/libs/suitesparse
fi

# SAMtools/HTSlib

# Para SAMTOOLS, adidionar ao PATH
update_env_path "samtools/usr/bin/" "libs/samtools/usr/bin/" "${ENV_FILE}"
source ${ENV_FILE}

if [ -f "${BENCHMARK_DIR}/libs/htslib/htslib_install/include/htslib" ]; then
    echo "HTSlib already installed. Skipping..."
else
    mkdir -p ${BENCHMARK_DIR}/libs/htslib/htslib_build
    cd ${BENCHMARK_DIR}/libs/htslib/htslib_build
    wget -O "htslib.tar.bz2" "https://github.com/samtools/htslib/releases/download/1.22.1/htslib-1.22.1.tar.bz2"

    tar xjf htslib.tar.bz2 
    cd htslib-1.22.1

    ./configure --prefix=${BENCHMARK_DIR}/libs/htslib/htslib_install \
        CPPFLAGS=-I/${BENCHMARK_DIR}/libs/zlib/zlib_install/include \
        LDFLAGS=-L/${BENCHMARK_DIR}/libs/zlib/zlib_install/lib \
        --disable-bz2 \
        --disable-lzma
    make -j"$(nproc)" 
    make install

fi 

if [ -f "${BENCHMARK_DIR}/libs/htslib/htslib_install/include/htslib" ]; then
    echo "HTSlib already installed. Skipping..."
else

    mkdir -p ${BENCHMARK_DIR}/libs/hdf5/hdf5_build
    cd ${BENCHMARK_DIR}/libs/hdf5/hdf5_build
    wget http://www.hdfgroup.org/ftp/HDF5/releases/hdf5-1.10/hdf5-1.10.1/src/hdf5-1.10.1.tar.gz
    tar xzf hdf5-1.10.1.tar.gz
    cd ${BENCHMARK_DIR}/libs/hdf5/hdf5_build/hdf5-1.10.1
    ./configure --enable-cxx --prefix=${BENCHMARK_DIR}/libs/hdf5/hdf5_install \
        --with-zlib="${BENCHMARK_DIR}/libs/zlib/zlib_install/include,${BENCHMARK_DIR}/libs/zlib/zlib_install/lib"
    make
    make install

    update_env_path "hdf5/hdf5_install/bin" "libs/hdf5/hdf5_install/bin" "${ENV_FILE}"
fi

# install sonLib
if [ -d "${BENCHMARK_DIR}/libs/sonLib/bin" ]; then
    echo "sonLib already installed. Skipping..."
else
    git clone https://github.com/benedictpaten/sonLib.git ${BENCHMARK_DIR}/libs/sonLib
    cd ${BENCHMARK_DIR}/libs/sonLib
    export CPPFLAGS="-I/${BENCHMARK_DIR}/libs/zlib/zlib_install/include -L/${BENCHMARK_DIR}/libs/zlib/zlib_install/lib"
    make
    unset CPPFLAGS

    update_env_path "sonLib/bin/" "libs/sonLib/bin/" "${ENV_FILE}"
fi

# install hal
if [ -d "${BENCHMARK_DIR}/libs/hal/bin" ]; then
    echo "hal already installed. Skipping..."
else
    git clone https://github.com/ComparativeGenomicsToolkit/hal.git ${BENCHMARK_DIR}/libs/hal
    cd ${BENCHMARK_DIR}/libs/hal
    export RANLIB=ranlib
    make

    update_env_path "hdf5/hdf5_install/bin" "libs/hdf5/hdf5_install/bin" "${ENV_FILE}"
fi

# SeqLib
if [ -d "${BENCHMARK_DIR}/libs/SeqLib/build/bin" ]; then
    echo "SeqLib already installed. Skipping..."
else
    wget https://github.com/walaj/SeqLib/archive/refs/tags/1.2.0.zip -O ${BENCHMARK_DIR}/libs/SeqLib.zip
    unzip ${BENCHMARK_DIR}/libs/SeqLib.zip -d ${BENCHMARK_DIR}/libs/
    
    cd ${BENCHMARK_DIR}/libs/SeqLib
    mkdir build
    cd build
    cmake .. -DHTSLIB_DIR=${BENCHMARK_DIR}/libs/htslib/htslib_install
    make
    make install

    update_env_path "SeqLib/build/bin/" "libs/SeqLib/build/bin/" "${ENV_FILE}"
fi

echo "Finished installing AUGUSTUS dependencies."

if [ ! -d "${BENCHMARK_DIR}/tools/Augustus-3.5.0" ]; then
    echo "Augustus was not downloaded. Please run get_tools.sh first."
else
    update_env_var "AUGUSTUS_CONFIG_PATH" "${BENCHMARK_DIR}/tools/Augustus-3.5.0/config" "${ENV_FILE}"
    source ${ENV_FILE}

    cd ${BENCHMARK_DIR}/tools/Augustus-3.5.0/
    cp ${BENCHMARK_DIR}/config/augustus/common.mk ${BENCHMARK_DIR}/tools/Augustus-3.5.0/common.mk

    make augustus

    update_env_path "Augustus-3.5.0/bin" "/tools/Augustus-3.5.0/bin" "${ENV_FILE}"
fi
# --------------

# Install SNAP
if [ ! -d "${BENCHMARK_DIR}/tools/SNAP-master" ]; then
    echo "SNAP was not downloaded. Please run get_tools.sh first."
else
    update_env_var "ZOE" "${BENCHMARK_DIR}/tools/SNAP-master/Zoe" "${ENV_FILE}"
    source ${ENV_FILE}

    cd ${BENCHMARK_DIR}/tools/SNAP-master/
    make

    update_env_path "SNAP-master/" "tools/SNAP-master/" "${ENV_FILE}"
    source ${ENV_FILE}
fi

# Install GeNeMark-ETP
if [ ! -d "${BENCHMARK_DIR}/tools/GeneMark-ETP" ]; then
    echo "GeneMark-ETP was not downloaded. Please run get_tools.sh first."
else
    update_env_path "libs/perl5/bin/" "libs/perl5/bin/" "${ENV_FILE}"

    update_env_var "PERL5LIB" "${BENCHMARK_DIR}/libs/perl5/lib/perl5" "${ENV_FILE}"
    update_env_var "PERL_MM_OPT" '"INSTALL_BASE=${BENCHMARK_DIR}/libs/perl5"' "${ENV_FILE}"

    source ${ENV_FILE}

    cpan App::cpanminus    

    cpanm --local-lib=${BENCHMARK_DIR}/libs/perl5 Cwd
    cpanm --local-lib=${BENCHMARK_DIR}/libs/perl5 Data::Dumper
    cpanm --local-lib=${BENCHMARK_DIR}/libs/perl5 File::Path
    cpanm --local-lib=${BENCHMARK_DIR}/libs/perl5 File::Spec
    cpanm --local-lib=${BENCHMARK_DIR}/libs/perl5 File::Temp
    cpanm --local-lib=${BENCHMARK_DIR}/libs/perl5 FindBin
    cpanm --local-lib=${BENCHMARK_DIR}/libs/perl5 Getopt::Long
    cpanm --local-lib=${BENCHMARK_DIR}/libs/perl5 Hash::Merge
    cpanm --local-lib=${BENCHMARK_DIR}/libs/perl5 List::Util
    cpanm --local-lib=${BENCHMARK_DIR}/libs/perl5 MCE::Mutex
    cpanm --local-lib=${BENCHMARK_DIR}/libs/perl5 Math::Utils
    cpanm --local-lib=${BENCHMARK_DIR}/libs/perl5 Parallel::ForkManager
    cpanm --local-lib=${BENCHMARK_DIR}/libs/perl5 Statistics::LineFit
    cpanm --local-lib=${BENCHMARK_DIR}/libs/perl5 Storable
    cpanm --local-lib=${BENCHMARK_DIR}/libs/perl5 Thread::Queue
    cpanm --local-lib=${BENCHMARK_DIR}/libs/perl5 YAML
    cpanm --local-lib=${BENCHMARK_DIR}/libs/perl5 YAML::XS
    cpanm --local-lib=${BENCHMARK_DIR}/libs/perl5 threads

    update_env_path "GeneMark-ETP/tools/" "tools/GeneMark-ETP/tools/" "${ENV_FILE}"
    update_env_path "GeneMark-ETP/bin/" "tools/GeneMark-ETP/bin/" "${ENV_FILE}"

    # GeneMark-ES e GeneMark-EP+ já estão na pasta tools/, só falta adicionar ao PATH
    update_env_path "GeneMark-ETP/bin/gmes/" "/tools/GeneMark-ETP/bin/gmes/" "${ENV_FILE}"

    source ${ENV_FILE}
fi

# AGAT
command -v agat_convert_sp_gxf2gxf >/dev/null 2>&1 || { 
    echo "AGAT is required but not installed. Installing..."  

    git clone https://github.com/NBISweden/AGAT.git ${BENCHMARK_DIR}/libs/AGAT
    cd ${BENCHMARK_DIR}/libs/AGAT

    cpan install Bio::Perl

    cpanm --local-lib=${BENCHMARK_DIR}/libs/perl5 install Clone Graph::Directed \
                LWP::UserAgent Carp Sort::Naturally \
                File::Share File::ShareDir::Install \
                Moose YAML LWP::Protocol::https \
                Term::ProgressBar

    perl Makefile.PL INSTALL_BASE=${BENCHMARK_DIR}/libs/perl5
    make
    make test
    make install
    
    update_env_path "AGAT/bin/" "libs/AGAT/bin/" "${ENV_FILE}"
    source ${ENV_FILE}
}

#genometools
command -v gt >/dev/null 2>&1 || { 
    echo "GenomeTools is required but not installed. Installing..."  
    wget https://github.com/genometools/genometools/archive/refs/tags/v1.6.6.tar.gz -O ${BENCHMARK_DIR}/libs/genometools.tar.gz
    tar -xvzf ${BENCHMARK_DIR}/libs/genometools.tar.gz -C ${BENCHMARK_DIR}/libs/
    rm ${BENCHMARK_DIR}/libs/genometools.tar.gz

    cd ${BENCHMARK_DIR}/libs/genometools-1.6.6/
    make -j4 cairo=no

    update_env_path "genometools-1.6.6/bin/" "libs/genometools-1.6.6/bin/" "${ENV_FILE}"
    source ${ENV_FILE}
}

# Para converter resultados do SNAP para formato normal
command -v SNAP_ExonEtermEinitEsngl_gff_to_gff3.pl >/dev/null 2>&1 || { 
    echo "SNAP to GFF3 converter is required but not installed. Installing..."  

    git clone https://github.com/EVidenceModeler/EVidenceModeler.git ${BENCHMARK_DIR}/libs/EVM
    update_env_path "EVM/EvmUtils/misc/" "libs/EVM/EvmUtils/misc/" "${ENV_FILE}"

    source ${ENV_FILE}
}

# gto_fasta_mutate
command -v gto_fasta_mutate >/dev/null 2>&1 || { 
    echo "gto_fasta_mutate is required but not installed. Installing..."  

    git clone https://github.com/cobilab/gto.git ${BENCHMARK_DIR}/libs/gto
    update_env_path "gto/bin" "libs/gto/bin" "${ENV_FILE}"

    source ${ENV_FILE}
}
