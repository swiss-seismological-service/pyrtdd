#include "catalog.h"
#include "pybind11/chrono.h"
#include "pybind11/operators.h"
#include "pybind11/pybind11.h"
#include "pybind11/stl.h"
#include "utctime.h"

#include <string>
#include <unordered_map>

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

  py::class_<RelocInfo_t>(event, "RELOC_INFO_TYPE")
      .def(py::init<>())
      .def(py::init<bool, double, double>())
      .def_readwrite("isRelocated", &RelocInfo_t::isRelocated)
      .def_readwrite("startRms", &RelocInfo_t::startRms)
      .def_readwrite("finalRms", &RelocInfo_t::finalRms);
}

void InitPhase(auto &catalog) {

  using Phase = HDD::Catalog::Phase;

  using ProcInfo_t = decltype(Phase::procInfo);
  using RelocInfo_t = decltype(Phase::relocInfo);

  auto phase = py::class_<Phase>(catalog, "Phase")
                   .def(py::init<>())
                   .def(py::self == py::self)  // NOLINT
                   .def(py::self != py::self)  // NOLINT
                   .def_readwrite("eventId", &Phase::eventId)
                   .def_readwrite("stationId", &Phase::stationId)
                   .def_readwrite("time", &Phase::time)
                   .def_readwrite("lowerUncertainty", &Phase::lowerUncertainty)
                   .def_readwrite("upperUncertainty", &Phase::upperUncertainty)
                   .def_readwrite("type", &Phase::type)
                   .def_readwrite("networkCode", &Phase::networkCode)
                   .def_readwrite("stationCode", &Phase::stationCode)
                   .def_readwrite("locationCode", &Phase::locationCode)
                   .def_readwrite("channelCode", &Phase::channelCode)
                   .def_readwrite("procInfo", &Phase::procInfo)
                   .def_readwrite("relocInfo", &Phase::relocInfo);

  py::enum_<Phase::Type>(phase, "Type")
      .value("P", Phase::Type::P)
      .value("S", Phase::Type::S)
      .value("NO", Phase::Type::NO);

  py::enum_<Phase::Source>(phase, "Source")
      .value("CATALOG", Phase::Source::CATALOG)
      .value("RT_EVENT_MANUAL", Phase::Source::RT_EVENT_MANUAL)
      .value("RT_EVENT_AUTOMATIC", Phase::Source::RT_EVENT_AUTOMATIC);

  py::class_<ProcInfo_t>(phase, "PROC_INFO_TYPE")
      .def(py::init<>())
      .def(py::init<Phase::Type, double, Phase::Source>())
      .def_readwrite("type", &ProcInfo_t::type)
      .def_readwrite("classWeight", &ProcInfo_t::classWeight)
      .def_readwrite("source", &ProcInfo_t::source);

  py::class_<RelocInfo_t>(phase, "RELOC_INFO_TYPE")
      .def(py::init<>())
      .def(py::init<bool, double, double, double>())
      .def_readwrite("isRelocated", &RelocInfo_t::isRelocated)
      .def_readwrite("weight", &RelocInfo_t::weight)
      .def_readwrite("startResidual", &RelocInfo_t::startResidual)
      .def_readwrite("finalResidual", &RelocInfo_t::finalResidual);
}

void InitCatalog(py::module_ &m) {

  using Station = HDD::Catalog::Station;
  using Event = HDD::Catalog::Event;
  using Phase = HDD::Catalog::Phase;

  auto catalog = py::class_<HDD::Catalog>(m, "Catalog")
                     .def(py::init<>())
                     .def(
                         py::init<
                             std::string const &, std::string const &,
                             std::string const &, bool>(),
                         py::arg("stationFile"), py::arg("eventFile"),
                         py::arg("phaseFile"),
                         py::arg("loadRelocationInfo") = false)
                     .def("getStations", &HDD::Catalog::getStations)
                     .def("getEvents", &HDD::Catalog::getEvents)
                     .def("getPhases", [](HDD::Catalog const &c) {
                       std::unordered_map<unsigned, std::vector<Phase>> r;
                       for (auto const &p : c.getPhases()) {
                         auto const &[u, _p] = p;
                         r[u].push_back(_p);
                       }
                       return r;
                     })
                     .def("writeToFile", &HDD::Catalog::writeToFile)
                     .def(
                         "extractEvent", &HDD::Catalog::extractEvent,
                         py::arg("eventId"), py::arg("keepEvId"));

  InitStation(catalog);
  InitEvent(catalog);
  InitPhase(catalog);
}
