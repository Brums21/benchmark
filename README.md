# benchmark

## Script to download tools

The file `get_tools.sh` allows to download all tools, except for GeneMark-ES and GeneMark-EP+, which should be downloaded from [here](http://topaz.gatech.edu/GeneMark/license_download.cgi). The option considered for this benchmarking test is `GeneMark-ES/ET/EP+ ver 4.72_lic` for the LINUX 64 OS. Be careful to download both the software and the license key, placing the last one in the same directory as the software folder.

### Steps to install the GeneMark-ES and GeneMark-EP+ tools:

1. Download the software and license key using the command:

    ```wget [copied software link]```.

2. Unzip the software using the command: 

    ```tar -xvzf gmes_linux_64.tar.gz```

3. Remove the compressed folder: 

    ```rm gmes_linux_64.tar.gz```

4. Get the license key, copying the link from the download: 

    ```wget [copied license link]```

5. Unzip the license key: 

    ```gunzip gm_key_64.gz```

6. Place the license key in the home folder: 

    ```cp gm_key ~/.gm_key```

In order to run GeneMark, some constraints had to be solved, namely the Perl modules necessary for its installation. We used the conva environment to solve these issues, and then configured GeneMark to accept the Perl path in the conda environment to run the tests. 

The following commands have been performed for this aspect:

1. Install miniconda:

```wget https://conda.io/miniconda.html```

2. Run the installer:

```bash Miniconda3-latest-Linux-x86_64.sh```

3. Configure miniconda path:

```export PATH=~/miniconda3/bin:$PATH```

4. Reload the shell:

```export PATH=~/miniconda3/bin:$PATH```

5. Activate conda:

```conda init```

6. Install the following perl dependencies:

```
   YAML
   Hash::Merge
   Parallel::ForkManager
   MCE::Mutex
   Thread::Queue
   threads
   Math::Utils
```

