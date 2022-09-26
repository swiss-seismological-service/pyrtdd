#include "catalog.h"
#include "pybind11/operators.h"
#include "pybind11/pybind11.h"

namespace py = pybind11;

void InitStation(auto &m) {

  using Str = std::string;
  using Station = HDD::Catalog::Station;

  py::class_<Station>(m, "Station")
      .def(py::init<>())
      .def(py::init<Str, double, double, double, Str, Str, Str>())
      .def(py::self == py::self)  // NOLINT
      .def(py::self != py::self)  // NOLINT
      .def_readwrite("id", &Station::id)
      .def_readwrite("latitude", &Station::latitude)
      .def_readwrite("longitude", &Station::longitude)
      .def_readwrite("elevation", &Station::elevation)
      .def_readwrite("networkCode", &Station::networkCode)
      .def_readwrite("stationCode", &Station::stationCode)
      .def_readwrite("locationCode", &Station::locationCode);
}

void InitCatalog(py::module_ &m) {

  auto catalog = py::class_<HDD::Catalog>(m, "Catalog").def(py::init<>());

  auto phase =
      py::class_<HDD::Catalog::Phase>(catalog, "Phase").def(py::init<>());

  auto type = py::enum_<HDD::Catalog::Phase::Type>(phase, "Type")
                  .value("P", HDD::Catalog::Phase::Type::P)
                  .value("S", HDD::Catalog::Phase::Type::S);

  InitStation(catalog);
}