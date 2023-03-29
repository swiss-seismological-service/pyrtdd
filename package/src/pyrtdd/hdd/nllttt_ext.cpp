#include "nllttt.h"
#include "pybind11/pybind11.h"
#include "ttt.h"

#include <memory>

namespace py = pybind11;

void InitNllTtt(py::module_ &m) {

  auto nllTtt = py::class_<
      HDD::NLL::TravelTimeTable, HDD::TravelTimeTable,
      std::shared_ptr<HDD::NLL::TravelTimeTable>>(m, "NLL");

  nllTtt.def(py::init<const std::string&, const std::string&,
                      const std::string&, bool, unsigned>());
}
