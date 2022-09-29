# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ BASIC SETUP ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

FROM debian:testing
USER root
WORKDIR /root

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~~~~ INSTALL USEFUL PACKAGES ~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

RUN apt-get update -y \
    && apt-get upgrade -y \
    && apt-get install -y \
        ccache \
        clang-14 \
        clangd-14 \
        clang-format-14 \
        clang-tidy-14 \
        clang-tools-14 \
        cmake \
        cppcheck \
        doxygen \
        curl \
        fish \
        g++-12 \
        gcc-12 \
        git \
        libclang-14-dev \
        llvm-14-dev \
        ninja-build \
       	openssh-client \
        python3 \
        python3-pip \
        vim \
        rsync \
        software-properties-common \
        sudo \
        unzip \
        wget \
    && apt-get autoremove -y \
    && apt-get clean -y

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~~ INSTALL NVCC (CUDA COMPILER) ~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

RUN wget https://developer.download.nvidia.com/compute/cuda/repos/debian11/x86_64/cuda-keyring_1.0-1_all.deb \
    && dpkg -i cuda-keyring_1.0-1_all.deb \
    && apt-get update \
    && apt-get install -y cuda-minimal-build-11.5 \
    && rm -rf *

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~~ INSTALL INCLUDE-WHAT-YOU-USE ~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

RUN git clone https://github.com/include-what-you-use/include-what-you-use.git --branch clang_14 --depth 1 \
    && mkdir build \
    && cd build \
    && cmake -G "Ninja" -S /root/include-what-you-use \
        -DCMAKE_PREFIX_PATH:PATH=/usr/lib/llvm-14 \
        -DCMAKE_INSTALL_PREFIX:PATH=/opt \
    && cmake --build . --target install \
    && cd \
    && rm -rf *

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~ INSTALL USEFUL PYTHON PACKAGES ~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

RUN pip install cmakelang

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ CREATE A USER ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

RUN adduser --disabled-password --gecos "" --shell /usr/bin/fish user
RUN usermod -aG sudo user
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ INSTALL ANACONDA ~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

USER user
WORKDIR /home/user

RUN curl -L https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o miniconda.sh \
    && bash ./miniconda.sh -b -p ${HOME}/.miniconda \
    && rm -f ./miniconda.sh \
    && fish -c "set -U fish_user_paths $fish_user_paths $HOME/.miniconda/bin" \
    && fish -c "conda init fish" \
    && fish -c "conda update -n base -c defaults conda" \
    && fish -c "conda install -n base --yes conda-libmamba-solver" \
    && fish -c "conda config --set experimental_solver libmamba"

SHELL ["fish", "-c"]
ENV CPM_SOURCE_CACHE=/home/user/.cpm_cache

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~ CUSTOM ENVIRONMENT ~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

RUN conda update -n base -c defaults conda \
  && conda create -c conda-forge -n scrtdd python=3.9 scikit-build=0.15.0 pybind11=2.9.2 pytest numpy>=1.23.3 obspy>=1.3.0
