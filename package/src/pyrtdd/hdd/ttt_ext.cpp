#include "pybind11/pybind11.h"
#include "ttt.h"

#include <memory>

namespace py = pybind11;

void InitTtt(py::module_ &m) {

  py::class_<HDD::TravelTimeTable, std::shared_ptr<HDD::TravelTimeTable>>(
      m, "TravelTimeTable");  // NOLINT
}
