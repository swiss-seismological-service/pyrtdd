#include "cvttt.h"
#include "pybind11/pybind11.h"
#include "ttt.h"

#include <memory>

namespace py = pybind11;

void InitCvTtt(py::module_ &m) {

  auto cvTtt = py::class_<
      HDD::ConstantVelocity, HDD::TravelTimeTable,
      std::shared_ptr<HDD::ConstantVelocity>>(m, "ConstantVelocity");

  cvTtt.def(py::init<double, double>());
}
