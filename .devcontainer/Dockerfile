FROM registry.gitlab.com/mafanasiev/cpp-template:latest

USER user
WORKDIR /home/user
SHELL ["fish", "-c"]
RUN conda update -n base -c defaults conda \
  && conda create -c conda-forge -n scrtdd python=3.9 scikit-build=0.15.0 pybind11=2.9.2 pytest
