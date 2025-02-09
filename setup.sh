#!/bin/bash

# get species 
./get_species_info

# get RNA-seq data and generate config files
./rna_seq_data

# get hints
./hints_generator

# get tools
./get_tools

# get dependencies
./install_dependencies