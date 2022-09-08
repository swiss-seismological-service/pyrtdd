#include "pybind11/pybind11.h"

namespace py = pybind11;

void InitConfig(py::module_ &);
void InitCatalog(py::module_ &);

PYBIND11_MODULE(hdd_ext, m) {  // NOLINT
  InitConfig(m);
  InitCatalog(m);
}