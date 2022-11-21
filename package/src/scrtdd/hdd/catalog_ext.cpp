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
                   .def_readwrite("isManual", &Phase::isManual)
                   .def_readwrite("procInfo", &Phase::procInfo)
                   .def_readwrite("relocInfo", &Phase::relocInfo);

  py::enum_<Phase::Type>(phase, "Type")
      .value("P", Phase::Type::P)
      .value("S", Phase::Type::S);

  py::enum_<Phase::Source>(phase, "Source")
      .value("CATALOG", Phase::Source::CATALOG)
      .value("RT_EVENT", Phase::Source::RT_EVENT)
      .value("THEORETICAL", Phase::Source::THEORETICAL)
      .value("XCORR", Phase::Source::XCORR);

  py::class_<ProcInfo_t>(phase, "PROC_INFO_TYPE")
      .def(py::init<>())
      .def(py::init<Phase::Type, double, Phase::Source>())
      .def_readwrite("type", &ProcInfo_t::type)
      .def_readwrite("weight", &ProcInfo_t::weight)
      .def_readwrite("source", &ProcInfo_t::source);
}

void InitCatalog(py::module_ &m) {

  using Station = HDD::Catalog::Station;
  using Event = HDD::Catalog::Event;
  using Phase = HDD::Catalog::Phase;

  auto catalog = py::class_<HDD::Catalog>(m, "Catalog")
                     .def(py::init<>())
                     .def(py::init<
                          std::string const &, std::string const &,
                          std::string const &, bool>())
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
                     .def("writeToFile", &HDD::Catalog::writeToFile);

  InitStation(catalog);
  InitEvent(catalog);
  InitPhase(catalog);
}
