#!/bin/bash

LIB_DIR=${BENCHMARK_DIR}/libs

mkdir -p libs/

packages=(
    build-essential wget git autoconf
    libgsl-dev libboost-all-dev libsuitesparse-dev liblpsolve55-dev
    libsqlite3-dev libmysql++-dev
    libboost-iostreams-dev zlib1g-dev
    libbamtools-dev
    samtools libhts-dev
    cdbfasta diamond-aligner libfile-which-perl libparallel-forkmanager-perl libyaml-perl libdbd-mysql-perl
    python3-biopython
)

for package in ${packages[@]}; do

    command -v $package >/dev/null 2>&1 || { 
        echo "$package is required but not installed. Installing..."

        apt-get download $package && mv $package_*.deb $package.deb
        dpkg -x $package.deb libs/$package/
        rm $package.deb
        echo "export PATH=libs/$package/usr/bin/:\$PATH" >> ~/.bashrc
    }

done