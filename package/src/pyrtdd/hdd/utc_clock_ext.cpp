#include "pybind11/chrono.h"
#include "pybind11/pybind11.h"
#include "utctime.h"

#include <chrono>

namespace py = pybind11;

void InitUtcTime(py::module_ &m) {

  py::class_<std::chrono::time_point<HDD::UTCClock, std::chrono::microseconds>>(
      m, "UTCClock")
      .def_static("fromString", &HDD::UTCClock::fromString)
      .def_static("toString", &HDD::UTCClock::toString);
}