#include "catalog.h"
#include "pybind11/pybind11.h"

namespace py = pybind11;

void InitCatalog(py::module_ &m) {

  auto catalog = py::class_<HDD::Catalog>(m, "Catalog");
  auto phase = py::class_<HDD::Catalog::Phase>(catalog, "Phase");

  auto type = py::enum_<HDD::Catalog::Phase::Type>(phase, "Type")
                  .value("P", HDD::Catalog::Phase::Type::P)
                  .value("S", HDD::Catalog::Phase::Type::S);
}