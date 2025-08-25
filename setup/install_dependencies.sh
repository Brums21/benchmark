#!/bin/bash

BENCHMARK_DIR=$HOME/benchmark
LIB_DIR=${BENCHMARK_DIR}/libs

mkdir -p ${LIB_DIR}

#instalar gzip -> zlib1g-dev
mkdir -p ${LIB_DIR}/zlib/zlib_build
cd ${LIB_DIR}/zlib/zlib_build
wget -O zlib-1.2.11.tar.gz https://sourceforge.net/projects/libpng/files/zlib/1.2.11/zlib-1.2.11.tar.gz/download
tar xzf zlib-1.2.11.tar.gz
cd ${LIB_DIR}/zlib/zlib_build/zlib-1.2.11
./configure --prefix=${LIB_DIR}/zlib/zlib_install
make
make install

#TODO: adicionar isto a bashrc
echo 'export ZLIB_INCLUDE=${LIB_DIR}/zlib/zlib_install/include' >> ~/.bashrc
echo 'export ZLIB_LIBRARY_PATH=${LIB_DIR}/zlib/zlib_install/lib' >> ~/.bashrc

#instalar boost -> libboost-iostreams-dev e libbost-all-dev
mkdir -p ${LIB_DIR}/boost/boost_build
cd ${LIB_DIR}/boost/boost_build
wget -O boost_1_76_0.tar.gz https://sourceforge.net/projects/boost/files/boost/1.76.0/boost_1_76_0.tar.gz/download
tar xzf boost_1_76_0.tar.gz
cd ${LIB_DIR}/boost/boost_build/boost_1_76_0
./bootstrap.sh --prefix=${LIB_DIR}/boost/boost_install --with-libraries=all
./b2 install --prefix=${LIB_DIR}/boost/boost_install

#instalar mysql

cd ${LIB_DIR}
# libmysql++3v5:
wget        libmysql++3v5_3.2.5-1build1_amd64.deb http://de.archive.ubuntu.com/ubuntu/pool/universe/m/mysql++/libmysql++3v5_3.2.5-1build1_amd64.deb
dpkg-deb -x libmysql++3v5_3.2.5-1build1_amd64.deb ${LIB_DIR}/mysql/mysql_install
# libmysql++-dev:
wget        libmysql++-dev_3.2.5-1build1_amd64.deb http://de.archive.ubuntu.com/ubuntu/pool/universe/m/mysql++/libmysql++-dev_3.2.5-1build1_amd64.deb
dpkg-deb -x libmysql++-dev_3.2.5-1build1_amd64.deb ${LIB_DIR}/mysql/mysql_install
# libmysqlclient21:
wget        libmysqlclient21_8.0.23-0ubuntu0.20.04.1_amd64.deb http://security.ubuntu.com/ubuntu/pool/main/m/mysql-8.0/libmysqlclient21_8.0.23-0ubuntu0.20.04.1_amd64.deb
dpkg-deb -x libmysqlclient21_8.0.23-0ubuntu0.20.04.1_amd64.deb ${LIB_DIR}/mysql/mysql_install
# libmysqlclient-dev:
wget        libmysqlclient-dev_8.0.23-0ubuntu0.20.04.1_amd64.deb http://security.ubuntu.com/ubuntu/pool/main/m/mysql-8.0/libmysqlclient-dev_8.0.23-0ubuntu0.20.04.1_amd64.deb
dpkg-deb -x libmysqlclient-dev_8.0.23-0ubuntu0.20.04.1_amd64.deb ${LIB_DIR}/mysql/mysql_install

#instalar sqlite
mkdir -p ${LIB_DIR}/sqlite3
cd ${LIB_DIR}/sqlite3
wget sqlite-autoconf-3350500.tar.gz https://www.sqlite.org/2021/sqlite-autoconf-3350500.tar.gz
tar zxf sqlite-autoconf-3350500.tar.gz
cd ${LIB_DIR}/sqlite3/sqlite-autoconf-3350500
./configure --prefix=${LIB_DIR}/sqlite3/sqlite3_install
make
make install

#instalar GSL
mkdir -p ${LIB_DIR}/gsl
cd ${LIB_DIR}/gsl
wget gsl-latest.tar.gz https://mirror.ibcp.fr/pub/gnu/gsl/gsl-latest.tar.gz
tar zxf gsl-latest.tar.gz
cd ${LIB_DIR}/gsl/gsl-2.6/
./configure --prefix=${LIB_DIR}/gsl/gsl_install
make
make install

#instalar LPSolve
mkdir -p ${LIB_DIR}/lpsolve
cd ${LIB_DIR}/lpsolve
wget -O lp_solve_5.5.2.11_source.tar.gz https://sourceforge.net/projects/lpsolve/files/lpsolve/5.5.2.11/lp_solve_5.5.2.11_source.tar.gz/download
tar zxf lp_solve_5.5.2.11_source.tar.gz
cd ${LIB_DIR}/lpsolve/lpsolve/lp_solve_5.5
chmod +x ./lpsolve55/ccc ./lp_solve/ccc
cd ${LIB_DIR}/lpsolve/lp_solve_5.5/lpsolve55
./ccc
cd ${LIB_DIR}/lpsolve/lp_solve_5.5/lp_solve
./ccc
mkdir -p ${LIB_DIR}/lpsolve/lpsolve_install/include
cp ${LIB_DIR}/lpsolve/lp_solve_5.5/*.h ${LIB_DIR}/lpsolve/lpsolve_install/include/
mkdir -p ${LIB_DIR}/lpsolve/lpsolve_install/lib
cp ${LIB_DIR}/lpsolve/lp_solve_5.5/lpsolve55/bin/ux64/liblpsolve55.* ${LIB_DIR}/lpsolve/lpsolve_install/lib/

#instalar SuiteSparse
git clone https://github.com/DrTimothyAldenDavis/SuiteSparse.git ${LIB_DIR}/suitesparse
cd ${LIB_DIR}/SuiteSparse_config
make install INSTALL=${LIB_DIR}/suitesparse_install
cd ${LIB_DIR}/suitesparse/COLAMD
make install INSTALL=${LIB_DIR}/suitesparse_install

#instalar BamTools
mkdir -p ${LIB_DIR}/bamtools
wget https://github.com/pezmaster31/bamtools/zipball/master -o pezmaster31-bamtools.zip
unzip pezmaster31-bamtools.zip -d ${LIB_DIR}/bamtools
mv ${LIB_DIR}/bamtools/pezmaster31-bamtools-2391b1a/* ${LIB_DIR}/bamtools/

mkdir -p ${LIB_DIR}/bamtools_build
cd ${LIB_DIR}/bamtools_build
cmake \
    -DCMAKE_INSTALL_PREFIX=${LIB_DIR}/bamtools_install \
    -DZLIB_LIBRARY=${LIB_DIR}/zlib/zlib_install/lib/libz.so \
    -DZLIB_INCLUDE_DIR=${LIB_DIR}/zlib/zlib_install/include \
    ${LIB_DIR}/bamtools
make
make install

#instalar HTSlib
git clone https://github.com/samtools/htslib.git ${LIB_DIR}/htslib/htslib_build
cd ${LIB_DIR}/htslib/htslib_build
git submodule update --init --recursive
autoreconf -i
./configure --prefix=${LIB_DIR}/htslib/htslib_install \
    CPPFLAGS=-I/${LIB_DIR}/zlib/zlib_install/include \
    LDFLAGS=-L/${LIB_DIR}/zlib/zlib_install/lib \
    --disable-bz2 \
    --disable-lzma
make
make install

git clone https://github.com/samtools/samtools.git ${LIB_DIR}/samtools/samtools_build
cd ${LIB_DIR}/samtools/samtools_build
autoheader
autoconf -Wno-syntax
./configure \
    --prefix=${LIB_DIR}/samtools/samtools_install \
    --with-htslib=${LIB_DIR}/htslib/htslib_install \
    --without-curses \
    CPPFLAGS=-I/${LIB_DIR}/zlib/zlib_install/include \
    LDFLAGS="-L/${LIB_DIR}/zlib/zlib_install/lib -Wl,-rpath,${LIB_DIR}/zlib/zlib_install/lib -L/${LIB_DIR}/htslib/htslib_install/lib -Wl,-rpath,${LIB_DIR}/htslib/htslib_install/lib"
make
make install

echo 'export PATH="$PATH:${LIB_DIR}/samtools/samtools_install/bin/"'>> ~/.bashrc

#install HAL
mkdir -p ${LIB_DIR}/hdf5/hdf5_build
cd ${LIB_DIR}/hdf5/hdf5_build
wget http://www.hdfgroup.org/ftp/HDF5/releases/hdf5-1.10/hdf5-1.10.1/src/hdf5-1.10.1.tar.gz
tar xzf hdf5-1.10.1.tar.gz
cd ${LIB_DIR}/hdf5/hdf5_build/hdf5-1.10.1
./configure --enable-cxx --prefix=${LIB_DIR}/hdf5/hdf5_install \
    --with-zlib="${LIB_DIR}/zlib/zlib_install/include,${LIB_DIR}/zlib/zlib_install/lib"
make
make install

echo 'export PATH="$PATH:${LIB_DIR}/hdf5/hdf5_install/bin'>> ~/.bashrc

# install sonLib
git clone https://github.com/benedictpaten/sonLib.git ${LIB_DIR}/sonLib
cd ${LIB_DIR}/sonLib
echo 'export CPPFLAGS="-I/${LIB_DIR}/zlib/zlib_install/include -L/${LIB_DIR}/zlib/zlib_install/lib"'>> ~/.bashrc
make
unset CPPFLAGS

# install hal
git clone https://github.com/ComparativeGenomicsToolkit/hal.git ${LIB_DIR}/hal
cd ${LIB_DIR}/hal
echo 'export RANLIB=ranlib'>> ~/.bashrc
make

echo 'export PATH="$PATH:${LIB_DIR}/hdf5/hdf5_install/bin"'>> ~/.bashrc
echo 'export PATH="$PATH:${LIB_DIR}/hal/bin/"'>> ~/.bashrc


#libbz2-dev
mkdir -p libbz2-dev
wget libbz2-dev_1.0.8-6_amd64.deb http://ftp.de.debian.org/debian/pool/main/b/bzip2/libbz2-dev_1.0.8-6_amd64.deb
dpkg-deb -x libbz2-dev_1.0.8-6_amd64.deb ./libbz2-dev

#liblzma
mkdir -p liblzma-dev
wget liblzma-dev_5.2.5-2ubuntu1_amd64.deb http://archive.ubuntu.com/ubuntu/pool/main/x/xz-utils/liblzma-dev_5.2.5-2ubuntu1_amd64.deb
dpkg-deb -x liblzma-dev_5.2.5-2ubuntu1_amd64.deb ./liblzma-dev

rm -r *.deb

git clone --recursive https://github.com/walaj/SeqLib.git ${LIB_DIR}/SeqLib
cd ${LIB_DIR}/SeqLib
./configure
make
make install

