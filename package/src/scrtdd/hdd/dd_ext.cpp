#include "dd.h"
#include "nanobind/nanobind.h"
#include "nanobind/stl/pair.h"
#include "nanobind/stl/string.h"
#include "nanobind/stl/vector.h"

namespace nb = nanobind;
using namespace nb::literals;

NB_MODULE(dd_ext, m) {  // NOLINT
  nb::class_<HDD::Config>(m, "Config")
      .def(nb::init<>())
      .def_readwrite("validPphases", &HDD::Config::validPphases)
      .def_readwrite("validSphases", &HDD::Config::validSphases)
      .def_readwrite("compatibleChannels", &HDD::Config::compatibleChannels)
      .def_readwrite("diskTraceMinLen", &HDD::Config::diskTraceMinLen);
}