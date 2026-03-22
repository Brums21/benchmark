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

command -v python3 >/dev/null 2>&1 || { 
    echo "Python3 is required but not installed. Please install it first."
    echo "You can refer to: https://www.python.org/downloads/source/"
    exit 1
}

command -v pip >/dev/null 2>&1 || { 
    echo "pip is required but not installed. Please install it first."
    echo "You can refer to: https://pip.pypa.io/en/stable/installation/"
    exit 1
}

command -v getorf >/dev/null 2>&1 || { 
    echo "emboss is required but not installed. You can install it with: "  
    echo "sudo apt-get install emboss"
    exit 1
}

command -v gcc >/dev/null 2>&1 || command -v g++ >/dev/null 2>&1 || { 
    echo "gcc and g++ are required but not installed. You can install them with: "  
    echo "sudo apt-get install build-essential"
    exit 1
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

# Install GeneMark-ETP
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
