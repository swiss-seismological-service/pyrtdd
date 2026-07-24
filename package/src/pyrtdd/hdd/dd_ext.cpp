#include "catalog.h"
#include "clustering.h"
#include "dd.h"
#include "pybind11/operators.h"
#include "pybind11/pybind11.h"
#include "pybind11/stl.h"
#include "ttt.h"
#include "waveform.h"
#include "xcorrcache.h"

#include <memory>
#include <pybind11/detail/common.h>
#include <string>

namespace py = pybind11;

using StrVec = std::vector<std::string>;

using Wff_t = decltype(HDD::Config::wfFilter);
using XCorr_t = HDD::XcorrOptions::XCorr;

auto operator==(Wff_t const &a, Wff_t const &b) {
  return a.filterStr == b.filterStr && a.extraTraceLen == b.extraTraceLen &&
      a.resampleFreq == b.resampleFreq;
};

auto operator==(XCorr_t const &a, XCorr_t const &b) {
  return a.minCoef == b.minCoef && a.startOffset == b.startOffset &&
      a.endOffset == b.endOffset && a.winScaling == b.winScaling &&
      a.maxDelay == b.maxDelay && a.components == b.components;
};

void InitConfig(py::module_ &m) {

  auto config = py::class_<HDD::Config>(m, "Config");

  config.def(py::init<>())
      .def_readwrite("validPphases", &HDD::Config::validPphases)
      .def_readwrite("validSphases", &HDD::Config::validSphases)
      .def_readwrite(
          "pickUncertaintyClasses", &HDD::Config::pickUncertaintyClasses)
      .def_readwrite("PSTableOnly", &HDD::Config::PSTableOnly)
      .def_readwrite("wfFilter", &HDD::Config::wfFilter);

  py::class_<Wff_t>(config, "WF_FILTER_TYPE")
      .def(py::init<>())
      .def(py::init<std::string, double, double>())
      .def("__eq__", [](Wff_t const &a, Wff_t const &b) { return a == b; })
      .def_readwrite("filterStr", &Wff_t::filterStr)
      .def_readwrite("resampleFreq", &Wff_t::resampleFreq)
      .def_readwrite("extraTraceLen", &Wff_t::extraTraceLen);
}

void InitClusteringOptions(py::module_ &m) {
  using namespace HDD;
  py::class_<ClusteringOptions>(m, "ClusteringOptions")
      .def(py::init<>())
      .def_readwrite(
          "minEvStaToInterEvRatio", &ClusteringOptions::minEvStaToInterEvRatio)
      .def_readwrite("minEvStaDist", &ClusteringOptions::minEvStaDist)
      .def_readwrite("maxEvStaDist", &ClusteringOptions::maxEvStaDist)
      .def_readwrite("minNumNeigh", &ClusteringOptions::minNumNeigh)
      .def_readwrite("maxNumNeigh", &ClusteringOptions::maxNumNeigh)
      .def_readwrite("minNumPhases", &ClusteringOptions::minNumPhases)
      .def_readwrite("maxNumPhases", &ClusteringOptions::maxNumPhases)
      .def_readwrite("maxNeighbourDist", &ClusteringOptions::maxNeighbourDist)
      .def_readwrite("numEllipsoids", &ClusteringOptions::numEllipsoids);
}

void InitXcorrOptions(py::module_ &m) {
  using namespace HDD;

  auto xcorrOptions =
      py::class_<XcorrOptions>(m, "XcorrOptions")
          .def(py::init<>())
          .def_readwrite("enable", &XcorrOptions::enable)
          .def_readwrite("minEvStaDist", &XcorrOptions::minEvStaDist)
          .def_readwrite("maxEvStaDist", &XcorrOptions::maxEvStaDist)
          .def_readwrite("maxInterEvDist", &XcorrOptions::maxInterEvDist)
          .def_readwrite("phase", &XcorrOptions::phase);

  py::class_<XCorr_t>(xcorrOptions, "XCorr")
      .def(py::init<>())
      .def(py::init<double, double, double, double, double, StrVec>())
      .def("__eq__", [](XCorr_t const &a, XCorr_t const &b) { return a == b; })
      .def_readwrite("minCoef", &XCorr_t::minCoef)
      .def_readwrite("startOffset", &XCorr_t::startOffset)
      .def_readwrite("endOffset", &XCorr_t::endOffset)
      .def_readwrite("winScaling", &XCorr_t::winScaling)
      .def_readwrite("maxDelay", &XCorr_t::maxDelay)
      .def_readwrite("components", &XCorr_t::components);
}

void InitSolverOptions(py::module_ &m) {

  using namespace HDD;

  py::class_<SolverOptions>(m, "SolverOptions")
      .def(py::init<>())
      .def_readwrite("type", &SolverOptions::type)
      .def_readwrite("L2normalization", &SolverOptions::L2normalization)
      .def_readwrite("solverIterations", &SolverOptions::solverIterations)
      .def_readwrite("algoIterations", &SolverOptions::algoIterations)
      .def_readwrite(
          "absLocConstraintStart", &SolverOptions::absLocConstraintStart)
      .def_readwrite(
          "absLocConstraintEnd", &SolverOptions::absLocConstraintEnd)
      .def_readwrite("dampingFactorStart", &SolverOptions::dampingFactorStart)
      .def_readwrite("dampingFactorEnd", &SolverOptions::dampingFactorEnd)
      .def_readwrite(
          "downWeightingByResidualStart",
          &SolverOptions::downWeightingByResidualStart)
      .def_readwrite(
          "downWeightingByResidualEnd",
          &SolverOptions::downWeightingByResidualEnd)
      .def_readwrite(
          "usePickUncertainties", &SolverOptions::usePickUncertainties)
      .def_readwrite("xcorrWeightScaler", &SolverOptions::xcorrWeightScaler);
}

void InitXCorrCache(py::module_ &m) {
  using namespace HDD;
  py::class_<XCorrCache>(m, "XCorrCache")
      .def(py::init<>())
      .def("empty", &XCorrCache::empty)
      .def("writeToFile", &XCorrCache::writeToFile)
      .def_static("readFromFile", &XCorrCache::readFromFile);
}

void InitNeighbours(py::module_ &m) {
  using namespace HDD;
  py::class_<Neighbours>(m, "Neighbours")
      .def(py::init<unsigned>())
      .def("referenceId", &Neighbours::referenceId)
      .def("setReferenceId", &Neighbours::setReferenceId)
      .def("amount", &Neighbours::amount)
      .def("ids", &Neighbours::ids)
      .def("stations", &Neighbours::stations)
      .def(
          "toCatalog", &Neighbours::toCatalog, py::arg("catalog"),
          py::arg("includeRefEv") = false)
      // These operate on one cluster (one entry of the list returned by
      // `DD.findClusters`), letting clusters be persisted to disk and
      // reloaded later to avoid recomputing them.
      .def_static(
          "writeToFile",
          py::overload_cast<
              std::unordered_map<unsigned, Neighbours> const &,
              Catalog const &, std::string const &>(&Neighbours::writeToFile))
      .def_static("readFromFile", &Neighbours::readFromFile);
}

void InitDd(py::module_ &m) {

  using namespace HDD;

  py::class_<DD>(m, "DD")
      // `HDD::DD` takes exclusive ownership (`unique_ptr`) of the
      // travel-time-table and waveform-proxy, matching how `ttt`/`wf` are
      // bound (unique_ptr-holder types): passing a Python object here moves
      // the underlying C++ instance into `DD` and leaves the Python object
      // empty, exactly like `std::move`-ing it away in C++ would.
      .def(
          py::init<
              Catalog const &, Config const &,
              std::unique_ptr<TravelTimeTable>, std::unique_ptr<Waveform::Proxy>>(),
          py::arg("catalog"), py::arg("cfg"), py::arg("ttt"), py::arg("wf"))
      // `wf`-less overload: cross-correlation isn't possible without
      // waveform data anyway, so this just saves having to spell out
      // `NoWaveformProxy()` at every call site that doesn't need it.
      .def(
          py::init([](Catalog const &catalog, Config const &cfg,
                      std::unique_ptr<TravelTimeTable> ttt) {
            return new DD(
                catalog, cfg, std::move(ttt),
                std::make_unique<Waveform::NoWaveformProxy>());
          }),
          py::arg("catalog"), py::arg("cfg"), py::arg("ttt"))
      .def("getCatalog", &DD::getCatalog)
      .def(
          "enableCatalogWaveformDiskCache",
          &DD::enableCatalogWaveformDiskCache, py::arg("cacheDir"),
          py::arg("diskTraceMinLen") = 10.)
      .def(
          "disableCatalogWaveformDiskCache",
          &DD::disableCatalogWaveformDiskCache)
      .def("unloadWaveforms", &DD::unloadWaveforms)
      .def("findClusters", &DD::findClusters)
      // `clustOpt` is dropped here: `DD::relocateMultiEvents` only consults it
      // to auto-compute `clusters` when the list passed in is empty, and
      // every documented workflow always calls `findClusters(clustOpt)`
      // first and passes its non-empty result in, at which point `clustOpt`
      // is never touched again. A default-constructed `ClusteringOptions()`
      // is passed through internally so that (rarely used, undocumented)
      // empty-`clusters` auto-clustering still works, just with default
      // options -- callers who want custom options for that should call
      // `findClusters` themselves instead, same as everywhere else.
      .def(
          "relocateMultiEvents",
          [](DD &dd,
             std::list<std::unordered_map<unsigned, Neighbours>> &clusters,
             XCorrCache &xcorrData, XcorrOptions const &xcorrOpt,
             SolverOptions const &solverOpt, bool saveProcessing,
             std::string const &processingDataDir) {
            return dd.relocateMultiEvents(
                clusters, xcorrData, ClusteringOptions(), xcorrOpt, solverOpt,
                saveProcessing, processingDataDir);
          },
          py::arg("clusters"), py::arg("xcorrData"), py::arg("xcorrOpt"),
          py::arg("solverOpt"), py::arg("saveProcessing") = false,
          py::arg("processingDataDir") = "")
      // xcorr-less overload: builds a disabled XcorrOptions and a throwaway
      // XCorrCache internally, for callers that don't want cross-correlation
      // and so have no cache to pass in or read back.
      .def(
          "relocateMultiEvents",
          [](DD &dd,
             std::list<std::unordered_map<unsigned, Neighbours>> &clusters,
             SolverOptions const &solverOpt, bool saveProcessing,
             std::string const &processingDataDir) {
            XCorrCache discardedXcorrData;
            XcorrOptions xcorrOpt;
            xcorrOpt.enable = false;
            return dd.relocateMultiEvents(
                clusters, discardedXcorrData, ClusteringOptions(), xcorrOpt,
                solverOpt, saveProcessing, processingDataDir);
          },
          py::arg("clusters"), py::arg("solverOpt"),
          py::arg("saveProcessing") = false, py::arg("processingDataDir") = "")
      .def(
          "relocateSingleEvent", &DD::relocateSingleEvent,
          py::arg("singleEvent"), py::arg("isManual"), py::arg("clustOpt"),
          py::arg("xcorrOpt"), py::arg("solverOpt"),
          py::arg("saveProcessing") = false,
          py::arg("processingDataDir") = "");

  InitClusteringOptions(m);
  InitXcorrOptions(m);
  InitSolverOptions(m);
  InitConfig(m);
  InitXCorrCache(m);
  InitNeighbours(m);
}
