#include "catalog.h"
#include "pybind11/chrono.h"
#include "pybind11/operators.h"
#include "pybind11/pybind11.h"
#include "utctime.h"

namespace py = pybind11;

void InitStation(auto &catalog) {

  using Str = std::string;
  using Station = HDD::Catalog::Station;

  py::class_<Station>(catalog, "Station")
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

void InitEvent(auto &catalog) {

  using Event = HDD::Catalog::Event;
  using RelocInfo_t = decltype(Event::relocInfo);
  using Phases_t = decltype(RelocInfo_t::phases);
  using Dd_t = decltype(RelocInfo_t::dd);

  auto event = py::class_<Event>(catalog, "Event")
                   .def(py::init<>())
                   .def(py::init<
                        unsigned, HDD::UTCTime, double, double, double, double,
                        RelocInfo_t>())
                   .def(py::self == py::self)  // NOLINT
                   .def(py::self != py::self)  // NOLINT
                   .def_readwrite("id", &Event::id)
                   .def_readwrite("time", &Event::time)
                   .def_readwrite("latitude", &Event::latitude)
                   .def_readwrite("longitude", &Event::longitude)
                   .def_readwrite("depth", &Event::depth)
                   .def_readwrite("magnitude", &Event::magnitude)
                   .def_readwrite("relocInfo", &Event::relocInfo);

  py::class_<Phases_t>(event, "PHASES_TYPE")
      .def(py::init<>())
      .def(py::init<unsigned, unsigned, double, double, double>())
      .def_readwrite("usedP", &Phases_t::usedP)
      .def_readwrite("usedS", &Phases_t::usedS)
      .def_readwrite("stationDistMedian", &Phases_t::stationDistMedian)
      .def_readwrite("stationDistMin", &Phases_t::stationDistMin)
      .def_readwrite("stationDistMax", &Phases_t::stationDistMax);

  py::class_<Dd_t>(event, "DD_TYPE")
      .def(py::init<>())
      .def(py::init<
           unsigned, unsigned, unsigned, unsigned, double, double, double,
           double>())
      .def_readwrite("numTTp", &Dd_t::numTTp)
      .def_readwrite("numTTs", &Dd_t::numTTs)
      .def_readwrite("numCCp", &Dd_t::numCCp)
      .def_readwrite("numCCs", &Dd_t::numCCs)
      .def_readwrite("startResidualMedian", &Dd_t::startResidualMedian)
      .def_readwrite("startResidualMAD", &Dd_t::startResidualMAD)
      .def_readwrite("finalResidualMedian", &Dd_t::finalResidualMedian)
      .def_readwrite("finalResidualMAD", &Dd_t::finalResidualMAD);

  py::class_<RelocInfo_t>(event, "RELOC_INFO_TYPE")
      .def(py::init<>())
      .def(py::init<
           bool, double, double, double, double, double, unsigned, Phases_t,
           Dd_t>())
      .def_readwrite("isRelocated", &RelocInfo_t::isRelocated)
      .def_readwrite("startRms", &RelocInfo_t::startRms)
      .def_readwrite("finalRms", &RelocInfo_t::finalRms)
      .def_readwrite("locChange", &RelocInfo_t::locChange)
      .def_readwrite("depthChange", &RelocInfo_t::depthChange)
      .def_readwrite("timeChange", &RelocInfo_t::timeChange)
      .def_readwrite("numNeighbours", &RelocInfo_t::numNeighbours)
      .def_readwrite("phases", &RelocInfo_t::phases)
      .def_readwrite("dd", &RelocInfo_t::dd);
}

void InitCatalog(py::module_ &m) {

  auto catalog = py::class_<HDD::Catalog>(m, "Catalog").def(py::init<>());

  auto phase =
      py::class_<HDD::Catalog::Phase>(catalog, "Phase").def(py::init<>());

  auto type = py::enum_<HDD::Catalog::Phase::Type>(phase, "Type")
                  .value("P", HDD::Catalog::Phase::Type::P)
                  .value("S", HDD::Catalog::Phase::Type::S);

  InitStation(catalog);
  InitEvent(catalog);
}