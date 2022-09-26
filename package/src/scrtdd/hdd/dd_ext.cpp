#include "dd.h"
#include "pybind11/operators.h"
#include "pybind11/pybind11.h"
#include "pybind11/stl.h"

namespace py = pybind11;

using StrVec = std::vector<std::string>;

using XCorr_t = HDD::Config::XCorr;
using Snr_t = decltype(HDD::Config::snr);
using Wff_t = decltype(HDD::Config::wfFilter);

auto operator==(XCorr_t const &a, XCorr_t const &b) {
  return a.minCoef == b.minCoef && a.startOffset == b.startOffset &&
      a.endOffset == b.endOffset && a.maxDelay == b.maxDelay &&
      a.components == b.components;
};

auto operator==(Wff_t const &a, Wff_t const &b) {
  return a.filterStr == b.filterStr && a.extraTraceLen == b.extraTraceLen &&
      a.resampleFreq == b.resampleFreq;
};

auto operator==(Snr_t const &a, Snr_t const &b) {
  return a.minSnr == b.minSnr && a.noiseEnd == b.noiseEnd &&
      a.noiseStart == b.noiseStart && a.signalStart == b.signalStart &&
      a.signalEnd == b.signalEnd;
}

void InitConfig(py::module_ &m) {

  auto config = py::class_<HDD::Config>(m, "Config");

  config.def(py::init<>())
      .def_readwrite("validPphases", &HDD::Config::validPphases)
      .def_readwrite("validSphases", &HDD::Config::validSphases)
      .def_readwrite("compatibleChannels", &HDD::Config::compatibleChannels)
      .def_readwrite("diskTraceMinLen", &HDD::Config::diskTraceMinLen)
      .def_readwrite("xcorr", &HDD::Config::xcorr)
      .def_readwrite("wfFilter", &HDD::Config::wfFilter)
      .def_readwrite("snr", &HDD::Config::snr);

  py::class_<XCorr_t>(config, "XCorr")
      .def(py::init<>())
      .def(py::init<double, double, double, double, StrVec>())
      .def("__eq__", [](XCorr_t const &a, XCorr_t const &b) { return a == b; })
      .def_readwrite("minCoef", &HDD::Config::XCorr::minCoef)
      .def_readwrite("startOffset", &HDD::Config::XCorr::startOffset)
      .def_readwrite("endOffset", &HDD::Config::XCorr::endOffset)
      .def_readwrite("maxDelay", &HDD::Config::XCorr::maxDelay)
      .def_readwrite("components", &HDD::Config::XCorr::components);

  py::class_<Wff_t>(config, "WF_FILTER_TYPE")
      .def(py::init<>())
      .def(py::init<std::string, double, double>())
      .def("__eq__", [](Wff_t const &a, Wff_t const &b) { return a == b; })
      .def_readwrite("filterStr", &Wff_t::filterStr)
      .def_readwrite("resampleFreq", &Wff_t::resampleFreq)
      .def_readwrite("extraTraceLen", &Wff_t::extraTraceLen);

  py::class_<Snr_t>(config, "SNR_TYPE")
      .def(py::init<>())
      .def(py::init<double, double, double, double, double>())
      .def("__eq__", [](Snr_t const &a, Snr_t const &b) { return a == b; })
      .def_readwrite("minSnr", &Snr_t::minSnr)
      .def_readwrite("noiseStart", &Snr_t::noiseStart)
      .def_readwrite("noiseEnd", &Snr_t::noiseEnd)
      .def_readwrite("signalStart", &Snr_t::signalStart)
      .def_readwrite("signalEnd", &Snr_t::signalEnd);
}