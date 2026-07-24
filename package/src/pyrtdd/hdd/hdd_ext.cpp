#include "pybind11/pybind11.h"

namespace py = pybind11;

void InitConfig(py::module_ &);
void InitCatalog(py::module_ &);
void InitTtt(py::module_ &);
void InitHomogeneous(py::module_ &);
void InitNLLGrid(py::module_ &);
void InitUtcTime(py::module &);
void InitTrace(py::module_ &m);
void InitProxy(py::module_ &m);
void InitDd(py::module_ &m);
void InitLogger(py::module_ &m);

PYBIND11_MODULE(hdd_ext, m) {  // NOLINT
  InitCatalog(m);
  InitTtt(m);
  InitHomogeneous(m);
  InitNLLGrid(m);
  InitUtcTime(m);
  InitTrace(m);
  InitProxy(m);
  InitDd(m);
  InitLogger(m);
}
