# pyrtdd

Python wrappers for the SED's double difference source relocation code [`scrtdd`](https://docs.gempa.de/scrtdd/current/).

# Installation

`pyrtdd` is tested with `gcc-11`, `gcc-12`, and `clang-14`. Before starting the installation process, please ensure that you have one of these compilers, along with [Anaconda](https://www.anaconda.com/products/distribution), installed on your system.

1. Clone this repository, ensuring that `scrtdd` is also pulled as a submodule:

    ```
    git clone --recursive https://gitlab.seismo.ethz.ch/lucasca/pyrtdd.git
    ```

2. Create a `pyrtdd` Anaconda environment using the included `environment.yml` file:

    ```
    conda env create -n pyrtdd -f environment.yml
    ```

3. Activate the `pyrtdd` anaconda enviroment:

    ```
    conda activate pyrtdd
    ```

4. Install `pyrtdd` from source:

    ```
    CC=gcc-11 CXX=g++-11 SKBUILD_CONFIGURE_OPTIONS="-DCMAKE_C_COMPILER:STRING=gcc-11 -DCMAKE_CXX_COMPILER:STRING=g++-11 pip install -v .
    ```
    
# Installation notes

- The build process can take awhile: `pyrtdd` uses the [CPM](https://github.com/cpm-cmake/CPM.cmake) package management system to download Boost, a dependency of `scrtdd`. If you will be building the library a lot, be sure to check out the caching section of the CPM documentation.
- The entire build process is also outlined in the continuous integration (CI) process for this repository, which is described by the `.gitlab-ci.yml` file. The CI builds `pyrtdd` from a Ubuntu 22.04 base image, which can be reconstructed from the `Dockerfile.ci` file.