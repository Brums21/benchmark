#!/bin/bash

# Create a directory for the tools
mkdir -p dependencies
cd dependencies

# Install BLAST
echo "Installing BLAST..."
wget https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST/ncbi-blast-2.16.0+-x64-linux.tar.gz -O blast.tar.gz
tar -xzf blast.tar.gz
echo "BLAST installed successfully."

# Install CD-HIT
echo "Installing CD-HIT..."
wget https://github.com/weizhongli/cdhit/releases/download/V4.8.1/cd-hit-v4.8.1-2019-0228.tar.gz -O cd-hit.tar.gz
tar -xzf cd-hit.tar.gz
echo "CD-HIT installed successfully."

# Install Exonerate
echo "Installing Exonerate..."
wget http://ftp.ebi.ac.uk/pub/software/vertebrategenomics/exonerate/exonerate-2.2.0.tar.gz -O exonerate.tar.xz
tar -xf exonerate.tar.xz
echo "Exonerate installed successfully."

# Install GlimmerHMM
echo "Installing GlimmerHMM..."
wget https://ccb.jhu.edu/software/glimmerhmm/dl/GlimmerHMM-3.0.4.tar.gz -O glimmerhmm.tar.gz
tar -xzf glimmerhmm.tar.gz
echo "GlimmerHMM installed successfully."

# Install MAKER
echo "Installing MAKER..."
wget http://weatherby.genetics.utah.edu/maker_downloads/53AF/7A0F/1DB0/C1A7F3826EC06B88F0A0515FC93C/maker-2.31.11.tgz -O maker.tar.gz
tar -xzf maker.tar.gz
echo "MAKER installed successfully."

# Install EMBOSS
echo "Installing EMBOSS..."
wget https://sourceforge.net/projects/emboss/files/EMBOSS/6.6.0/EMBOSS-6.6.0.tar.gz -O emboss.tar.gz
tar -xzf emboss.tar.gz
echo "EMBOSS installed successfully."

# Install HMMER
echo "Installing HMMER..."
wget http://eddylab.org/software/hmmer/hmmer-3.4.tar.gz -O hmmer.tar.gz
tar -xzf hmmer.tar.gz
echo "HMMER installed successfully."

# Install RepeatMasker
echo "Installing RepeatMasker..."
wget https://www.repeatmasker.org/RepeatMasker/RepeatMasker-4.1.7-p1.tar.gz -O repeatmasker.tar.gz
tar -xzf repeatmasker.tar.gz
echo "RepeatMasker installed successfully."

# Install NCBI C++ Toolkit
echo "Installing NCBI C++ Toolkit..."
wget https://ftp.ncbi.nih.gov/toolbox/ncbi_tools++/ARCHIVE/2021/Sep_30_2021/ncbi_cxx--25_2_0.tar.gz -O ncbi_toolkit.tar.gz
tar -xzf ncbi_toolkit.tar.gz
echo "NCBI C++ Toolkit installed successfully."

# Install Genome Tools
echo "Installinge Genome Tools...."
apt-get install genometools

cd ..

echo "All dependencies installed successfully!"