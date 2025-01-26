# benchmark

## Script to download tools

The file `get_tools.sh` allows to download all tools, except for GeneMark-ES and GeneMark-EP+, which should be downloaded from [here](http://topaz.gatech.edu/GeneMark/license_download.cgi). The option considered for this benchmarking test is `GeneMark-ES/ET/EP+ ver 4.72_lic` for the LINUX 64 OS. Be careful to download both the software and the license key, placing the last one in the same directory as the software folder.

### Steps to setup the GeneMark-ES and GeneMark-EP+ tools:

1. Download the software and license key using the `wget [copied software link]` command. 

2. Unzip the software using the `tar -xvzf gmes_linux_64.tar.gz`

3. Remove the compressed folder: `rm gmes_linux_64.tar.gz`

4. Get the license key, copying the link from the download: `wget [copied license link]`

5. Unzip the license key: `gunzip gm_key_64.gz`

6. Place the license key in the root folder of the software: `mv gm_key_64 gmes_linux_64/`