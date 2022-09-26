#include "cvttt.h"
#include "pybind11/pybind11.h"
#include "ttt.h"

namespace py = pybind11;

void InitTtt(py::module_ &m) {

  py::class_<HDD::TravelTimeTable>(m, "TravelTimeTable");  // NOLINT

  auto cvTtt = py::class_<HDD::ConstantVelocity, HDD::TravelTimeTable>(
      m, "ConstantVelocity");

  cvTtt.def(py::init<double, double>());
}