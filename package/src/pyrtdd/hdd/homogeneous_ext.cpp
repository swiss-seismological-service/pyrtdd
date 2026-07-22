#include "pybind11/pybind11.h"
#include "ttt.h"
#include "ttt/homogeneous.h"

#include <memory>

namespace py = pybind11;

void InitHomogeneous(py::module_ &m) {

  auto homogeneous =
      py::classh<HDD::TTT::Homogeneous, HDD::TravelTimeTable>(m, "Homogeneous");

  homogeneous.def(py::init<double, double>());
}
