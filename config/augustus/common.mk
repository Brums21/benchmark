# Definitions common to all Makefiles
# This file is included from other Makefiles in the augustus project.
AUGVERSION = 3.4.0

# set ZIPINPUT to false if you do not require input gzipped input genome files,
# get compilation errors about the boost iostreams library or
# the required libraries libboost-iostreams-dev and lib1g-dev are not available
ZIPINPUT = true

MYSQL = false

# set COMPGENEPRED to false if you do not require the comparative gene prediction mode (CGP) or
# the required libraries
# libgsl-dev, libboost-all-dev, libsuitesparse-dev, liblpsolve55-dev, libmysql++-dev and libsqlite3-dev
# are not available
COMPGENEPRED = true

# set these paths to the correct locations if you have installed the corresponding packages in non-default locations:
INCLUDE_PATH_ZLIB        := -I/${BENCHMARK_DIR}/libs/zlib1g-dev/usr/include
LIBRARY_PATH_ZLIB        := -L/${BENCHMARK_DIR}/libs/zlib1g-dev/usr/include/lib/x86_64-linux-gnu -Wl,-rpath,${BENCHMARK_DIR}/libs/zlib1g-dev/usr/lib/x86_64-linux-gnu
INCLUDE_PATH_BOOST       := -I/${BENCHMARK_DIR}/libs/boost/boost_install/include
LIBRARY_PATH_BOOST       := -L/${BENCHMARK_DIR}/libs/boost/boost_install/lib -Wl,-rpath,${BENCHMARK_DIR}/libs/boost/boost_install/lib
INCLUDE_PATH_LPSOLVE     := -I/${BENCHMARK_DIR}/libs/liblpsolve55-dev/usr/include/lpsolve
LIBRARY_PATH_LPSOLVE     := -L/${BENCHMARK_DIR}/libs/liblpsolve55-dev/usr/lib -Wl,-rpath,${BENCHMARK_DIR}/libs/liblpsolve55-dev/usr/lib
INCLUDE_PATH_SUITESPARSE := -I/${BENCHMARK_DIR}/libs/suitesparse/suitesparse_install/include
LIBRARY_PATH_SUITESPARSE := -L/${BENCHMARK_DIR}/libs/suitesparse/suitesparse_install/lib -Wl,-rpath,${BENCHMARK_DIR}/libs/suitesparse/suitesparse_install/lib
INCLUDE_PATH_GSL         := -I/${BENCHMARK_DIR}/libs/libgsl-dev/usr/include
LIBRARY_PATH_GSL         := -L/${BENCHMARK_DIR}/libs/libgsl-dev/usr/lib/x86_64-linux-gnu -Wl,-rpath,${BENCHMARK_DIR}/libs/libgsl-dev/usr/lib/x86_64-linux-gnu
INCLUDE_PATH_MYSQL       := -I/${BENCHMARK_DIR}/libs/mysql/mysql_install/usr/include -I/${BENCHMARK_DIR}/libs/mysql/mysql_install/usr/include/mysql
LIBRARY_PATH_MYSQL       := -L/${BENCHMARK_DIR}/libs/mysql/mysql_install/usr/lib/x86_64-linux-gnu -Wl,-rpath,${BENCHMARK_DIR}/libs/mysql/mysql_install/usr/lib/x86_64-linux-gnu
INCLUDE_PATH_SQLITE      := -I/${BENCHMARK_DIR}/libs/libsqlite3-dev/usr/include
LIBRARY_PATH_SQLITE      := -L/${BENCHMARK_DIR}/libs/libsqlite3-dev/usr/lib -Wl,-rpath,${BENCHMARK_DIR}/libs/libsqlite3-dev/usr/lib
INCLUDE_PATH_BAMTOOLS    := -I/${BENCHMARK_DIR}/libs/libbamtools-dev/usr/include/bamtools
LIBRARY_PATH_BAMTOOLS    := -L/${BENCHMARK_DIR}/libs/libbamtools-dev/usr/lib -Wl,-rpath,${BENCHMARK_DIR}/libs/libbamtools-dev/usr/lib
INCLUDE_PATH_HTSLIB      := -I/${BENCHMARK_DIR}/ibs/htslib/htslib_install/include/htslib
LIBRARY_PATH_HTSLIB      := -L/${BENCHMARK_DIR}/libs/htslib/htslib_install/lib -Wl,-rpath,${BENCHMARK_DIR}/libs/htslib/htslib_install/lib
INCLUDE_PATH_SEQLIB      := -I/${BENCHMARK_DIR}/libs/SeqLib -I/${BENCHMARK_DIR}/libs/SeqLib/htslib
LIBRARY_PATH_SEQLIB      := -I/${BENCHMARK_DIR}/libs/SeqLib/build  -Wl,-rpath,-I/${BENCHMARK_DIR}/libs/SeqLib/build

# alternatively add paths with header files to INCLS and paths with library files to LDFLAGS

ifeq ($(shell uname -s), Darwin)
	# path for default homebrew installation of lp_solve
	INCLUDE_PATH_LPSOLVE = -I/usr/local/opt/lp_solve/include
	# path for default homebrew installation of mysql and mysql++
	INCLUDE_PATH_MYSQL = -I/usr/local/opt/mysql/include/mysql -I/usr/local/opt/mysql++/include/mysql
	# path for default homebrew installation of bamtools
	INCLUDE_PATH_BAMTOOLS = -I/usr/local/opt/bamtools/include/bamtools
	# path for default homebrew installation of htslib
	INCLUDE_PATH_HTSLIB = -I/usr/local/opt/htslib/include/htslib
endif
