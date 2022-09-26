#include "pybind11/pybind11.h"

namespace py = pybind11;

void InitConfig(py::module_ &);
void InitCatalog(py::module_ &);
void InitTtt(py::module_ &);
void InitUtcTime(py::module &);

PYBIND11_MODULE(hdd_ext, m) {  // NOLINT
  InitConfig(m);
  InitCatalog(m);
  InitTtt(m);
  InitUtcTime(m);
}