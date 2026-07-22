#include "log.h"
#include "pybind11/pybind11.h"

namespace py = pybind11;

void InitLogger(py::module_ &m) {

  auto logger =
      m.def_submodule("Logger", "Control HDD's logging verbosity/output.");

  py::enum_<HDD::Logger::Level>(logger, "Level")
      .value("debug", HDD::Logger::Level::debug)
      .value("info", HDD::Logger::Level::info)
      .value("warning", HDD::Logger::Level::warning)
      .value("error", HDD::Logger::Level::error)
      .value("none", HDD::Logger::Level::none);

  logger.def("setLevel", &HDD::Logger::setLevel);
  logger.def("getLevel", &HDD::Logger::getLevel);

  // HDD itself defaults to `debug` (its most verbose level). Default to
  // `info` instead, which is a saner out-of-the-box level for a library.
  HDD::Logger::setLevel(HDD::Logger::Level::info);
}
