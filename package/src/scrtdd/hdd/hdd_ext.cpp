#include "pybind11/pybind11.h"

namespace py = pybind11;

void InitConfig(py::module_ &);
void InitCatalog(py::module_ &);
void InitTtt(py::module_ &);
void InitUtcTime(py::module &);
void InitObspyWaveformProxy(py::module_ &m);
void InitDd(py::module_ &m);

PYBIND11_MODULE(hdd_ext, m) {  // NOLINT
  InitCatalog(m);
  InitTtt(m);
  InitUtcTime(m);
  InitObspyWaveformProxy(m);
  InitDd(m);
}