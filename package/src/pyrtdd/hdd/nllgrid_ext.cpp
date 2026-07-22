#include "pybind11/pybind11.h"
#include "ttt.h"
#include "ttt/nllgrid.h"

#include <memory>
#include <string>

namespace py = pybind11;

void InitNLLGrid(py::module_ &m) {

  auto nllGrid =
      py::classh<HDD::TTT::NLLGrid, HDD::TravelTimeTable>(m, "NLLGrid");

  nllGrid.def(
      py::init<
          const std::string &, const std::string &, double, bool, unsigned,
          const std::string &>(),
      py::arg("gridPath"), py::arg("gridModel"),
      py::arg("maxSearchDistance") = 0.1, py::arg("swapBytes") = false,
      py::arg("maxOpenFiles") = 512, py::arg("accessMethod") = "KeepOpen");
}
