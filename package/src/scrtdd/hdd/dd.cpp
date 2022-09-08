#include "dd.h"
#include "pybind11/pybind11.h"
#include "pybind11/stl.h"

namespace py = pybind11;

void InitConfig(py::module_& m) {

  auto config = py::class_<HDD::Config>(m, "Config");

  config.def(py::init<>())
      .def_readwrite("validPphases", &HDD::Config::validPphases)
      .def_readwrite("validSphases", &HDD::Config::validSphases)
      .def_readwrite("compatibleChannels", &HDD::Config::compatibleChannels)
      .def_readwrite("diskTraceMinLen", &HDD::Config::diskTraceMinLen)
      .def_readwrite("xcorr", &HDD::Config::xcorr);

  py::class_<HDD::Config::XCorr>(config, "XCorr")
      .def(py::init<>())
      .def_readwrite("minCoef", &HDD::Config::XCorr::minCoef)
      .def_readwrite("startOffset", &HDD::Config::XCorr::startOffset)
      .def_readwrite("endOffset", &HDD::Config::XCorr::endOffset)
      .def_readwrite("maxDelay", &HDD::Config::XCorr::maxDelay)
      .def_readwrite("components", &HDD::Config::XCorr::components);
}