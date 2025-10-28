#!/bin/bash

mkdir -p ${BENCHMARK_DIR}/libs/

# GeMoMa
wget https://mmseqs.com/latest/mmseqs-linux-sse2.tar.gz -O ${BENCHMARK_DIR}/libs/mmseqs-linux-sse2.tar.gz
tar xvfz ${BENCHMARK_DIR}/libs/mmseqs-linux-sse2.tar.gz -C ${BENCHMARK_DIR}/libs/
rm ${BENCHMARK_DIR}/libs/mmseqs-linux-sse2.tar.gz
echo 'export PATH=${BENCHMARK_DIR}/libs/mmseqs/bin/:$PATH' >> ~/.bashrc

#AUGUSTUS

# SQLite, GSL, LPsolve, zlib, BamTools, samtools
packages=(zlib1g-dev libsqlite3-dev libgsl-dev libsuitesparse-dev liblpsolve55-dev libbamtools-dev samtools)

for package in ${packages[@]}; do

    command -v $package >/dev/null 2>&1 || { 
        echo "$package is required but not installed. Installing..."

        apt-get download $package && mv $package_*.deb $package.deb
        dpkg -x $package.deb ${BENCHMARK_DIR}/libs/$package/
        rm $package.deb
    }
done

#Zlib
echo 'export ZLIB_INCLUDE=${BENCHMARK_DIR}/libs/zlib1g-dev/usr/include' >> ~/.bashrc
echo 'export ZLIB_LIBRARY_PATH=${BENCHMARK_DIR}/libs/zlib1g-dev/usr/lib' >> ~/.bashrc

source ~/.bashrc

# Boost
mkdir -p ${BENCHMARK_DIR}/libs/boost/boost_build
cd ${BENCHMARK_DIR}/libs/boost/boost_build
wget -O boost_1_76_0.tar.gz https://sourceforge.net/projects/boost/files/boost/1.76.0/boost_1_76_0.tar.gz/download
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
git clone https://github.com/DrTimothyAldenDavis/SuiteSparse.git ${BENCHMARK_DIR}/libs/suitesparse
cd ${BENCHMARK_DIR}/libs/suitesparse/SuiteSparse_config

cmake -S . -B build \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
        -DCMAKE_INSTALL_PREFIX=${BENCHMARK_DIR}/libs/suitesparse/suitesparse_install

cmake --build build -j"$(nproc)"
cmake --install build

# SAMtools/HTSlib

# Para SAMTOOLS, adidionar ao PATH
echo 'export PATH=${BENCHMARK_DIR}/libs/samtools/usr/bin/:$PATH' >> ~/.bashrc
source ~/.bashrc

mkdir -p ${BENCHMARK_DIR}/libs/htslib/htslib_build
cd ${BENCHMARK_DIR}/libs/htslib/htslib_build
wget -O "htslib.tar.bz2" "https://github.com/samtools/htslib/releases/download/1.22.1/htslib-1.22.1.tar.bz2"

tar xjf htslib.tar.bz2 
cd htslib-1.22.1

./configure --prefix=${BENCHMARK_DIR}/libs/htslib/htslib_install \
    CPPFLAGS=-I/${BENCHMARK_DIR}/libs/zlib1g-dev/usr/include \
    LDFLAGS=-L/${BENCHMARK_DIR}/libs/zlib1g-dev/usr/lib \
    --disable-bz2 \
    --disable-lzma
make -j"$(nproc)"
make install


mkdir -p ${BENCHMARK_DIR}/libs/hdf5/hdf5_build
cd ${BENCHMARK_DIR}/libs/hdf5/hdf5_build
wget http://www.hdfgroup.org/ftp/HDF5/releases/hdf5-1.10/hdf5-1.10.1/src/hdf5-1.10.1.tar.gz
tar xzf hdf5-1.10.1.tar.gz
cd ${BENCHMARK_DIR}/libs/hdf5/hdf5_build/hdf5-1.10.1
./configure --enable-cxx --prefix=${BENCHMARK_DIR}/libs/hdf5/hdf5_install \
    --with-zlib="${BENCHMARK_DIR}/libs/zlib1g-dev/usr/include,${BENCHMARK_DIR}/libs/zlib1g-dev/usr/lib"
make
make install
export PATH="$PATH:${BENCHMARK_DIR}/libs/hdf5/hdf5_install/bin"

# install sonLib
git clone https://github.com/benedictpaten/sonLib.git ${BENCHMARK_DIR}/libs/sonLib
cd ${BENCHMARK_DIR}/libs/sonLib
export CPPFLAGS="-I/${BENCHMARK_DIR}/libs/zlib1g-dev/usr/include -L/${BENCHMARK_DIR}/libs/zlib1g-dev/usr/lib"
make
unset CPPFLAGS

# install hal
git clone https://github.com/ComparativeGenomicsToolkit/hal.git ${BENCHMARK_DIR}/libs/hal
cd ${BENCHMARK_DIR}/libs/hal
export RANLIB=ranlib
make

echo 'export PATH=${BENCHMARK_DIR}/libs/hdf5/hdf5_install/bin:$PATH' >> ~/.bashrc
echo 'export PATH=${BENCHMARK_DIR}/libs/sonLib/bin/:$PATH' >> ~/.bashrc

# SeqLib
wget https://github.com/walaj/SeqLib/archive/refs/tags/1.2.0.zip -O ${BENCHMARK_DIR}/libs/SeqLib.zip
unzip ${BENCHMARK_DIR}/libs/SeqLib.zip -d ${BENCHMARK_DIR}/libs/
 
cd ${BENCHMARK_DIR}/libs/SeqLib
mkdir build
cd build
cmake .. -DHTSLIB_DIR=${BENCHMARK_DIR}/libs/htslib/htslib_install
make
make install

echo 'export PATH=${BENCHMARK_DIR}/tools/Augustus-3.5.0/bin:${BENCHMARK_DIR}/tools/Augustus-3.5.0/scripts:$PATH' >> ~/.bashrc
echo 'export AUGUSTUS_CONFIG_PATH=${BENCHMARK_DIR}/tools/Augustus-3.5.0/config' >> ~/.bashrc

source ~/.bashrc

cd ${BENCHMARK_DIR}/tools/Augustus-3.5.0/
cp ${BENCHMARK_DIR}/config/augustus/common.mk ${BENCHMARK_DIR}/tools/Augustus-3.5.0/common.mk

make augustus

# Install SNAP
echo 'export ZOE=${BENCHMARK_DIR}/tools/SNAP-master/Zoe' >> ~/.bashrc
source ~/.bashrc

cd ${BENCHMARK_DIR}/tools/SNAP-master/
make

echo 'export PATH=${BENCHMARK_DIR}/tools/SNAP-master:$PATH' >> ~/.bashrc
source ~/.bashrc

# Install GeNeMark-ETP
cpan App::cpanminus

echo 'export PERL5LIB="$HOME/perl5/lib/perl5${PERL5LIB+:$PERL5LIB}"' >> ~/.bashrc
echo 'export PATH="$HOME/perl5/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

cpanm Cwd
cpanm Data::Dumper
cpanm File::Path
cpanm File::Spec
cpanm File::Temp
cpanm FindBin
cpanm Getopt::Long
cpanm Hash::Merge
cpanm List::Util
cpanm MCE::Mutex
cpanm Math::Utils
cpanm Parallel::ForkManager
cpanm Statistics::LineFit
cpanm Storable
cpanm Thread::Queue
cpanm YAML
cpanm YAML::XS
cpanm threads

echo 'export PATH=${BENCHMARK_DIR}/tools/GeneMark-ETP/tools/:$PATH' >> ~/.bashrc
echo 'export PATH=${BENCHMARK_DIR}/tools/GeneMark-ETP/bin/:$PATH' >> ~/.bashrc

# GeneMark-ES e GeneMark-EP+ já estão na pasta tools/, só falta adicionar ao PATH
echo 'export PATH=${BENCHMARK_DIR}/tools/GeneMark-ETP/bin/gmes/:$PATH' >> ~/.bashrc

source ~/.bashrc


# AGAT
command -v agat_convert_sp_gxf2gxf >/dev/null 2>&1 || { 
    echo "AGAT is required but not installed. Installing..."  

    git clone https://github.com/NBISweden/AGAT.git ${BENCHMARK_DIR}/libs/AGAT
    cd ${BENCHMARK_DIR}/libs/AGAT

    cpanm install BioPerl Clone Graph::Directed\
                LWP::UserAgent Carp Sort::Naturally \
                File::Share File::ShareDir::Install \
                Moose YAML LWP::Protocol::https \
                Term::ProgressBar

    perl Makefile.PL INSTALL_BASE=$HOME/perl5
    make
    make test
    make install
    
    echo 'export PATH=${BENCHMARK_DIR}/libs/AGAT/bin/:$PATH' >> ~/.bashrc
    source ~/.bashrc
}

#genometools
command -v gt >/dev/null 2>&1 || { 
    echo "GenomeTools is required but not installed. Installing..."  
    wget https://github.com/genometools/genometools/archive/refs/tags/v1.6.6.tar.gz -O ${BENCHMARK_DIR}/libs/genometools.tar.gz
    tar -xvzf ${BENCHMARK_DIR}/libs/genometools.tar.gz -C ${BENCHMARK_DIR}/libs/
    rm ${BENCHMARK_DIR}/libs/genometools.tar.gz

    cd ${BENCHMARK_DIR}/libs/genometools-1.6.6/
    make -j4 cairo=no

    echo 'export PATH=${BENCHMARK_DIR}/libs/genometools-1.6.6/bin/:$PATH' >> ~/.bashrc
    source ~/.bashrc
}

# Para converter resultados do SNAP para formato normal
command -v SNAP_ExonEtermEinitEsngl_gff_to_gff3.pl >/dev/null 2>&1 || { 
    echo "SNAP to GFF3 converter is required but not installed. Installing..."  

    git clone git@github.com:EVidenceModeler/EVidenceModeler.git ${BENCHMARK_DIR}/libs/EVM
    echo 'export PATH=${BENCHMARK_DIR}/libs/EVM/EvmUtils/misc/:$PATH' >> ~/.bashrc

    source ~/.bashrc
}