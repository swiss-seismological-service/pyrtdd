#include "pybind11/pybind11.h"
#include "pybind11/stl.h"
#include "ttt.h"

#include <memory>
#include <string>
#include <tuple>

namespace py = pybind11;

void InitTtt(py::module_ &m) {

  // `smart_holder` allows `TravelTimeTable` instances constructed in Python
  // to later have their ownership moved into a C++ `unique_ptr<TravelTimeTable>`
  // (e.g. HDD::DD's constructor), which a plain `std::unique_ptr` holder
  // cannot do.
  py::classh<HDD::TravelTimeTable>(m, "TravelTimeTable")  // NOLINT
      .def(
          "compute",
          [](HDD::TravelTimeTable &t, double eventLat, double eventLon,
             double eventDepth, double stationLat, double stationLon,
             double stationElevation, std::string const &phaseType) {
            return t.compute(
                eventLat, eventLon, eventDepth, stationLat, stationLon,
                stationElevation, phaseType);
          },
          py::arg("eventLat"), py::arg("eventLon"), py::arg("eventDepth"),
          py::arg("stationLat"), py::arg("stationLon"),
          py::arg("stationElevation"), py::arg("phaseType"))
      .def(
          "computeAll",
          [](HDD::TravelTimeTable &t, double eventLat, double eventLon,
             double eventDepth, double stationLat, double stationLon,
             double stationElevation, std::string const &phaseType) {
            double travelTime, takeOffAzi, takeOffDip, dtdd, dtdh;
            t.compute(
                eventLat, eventLon, eventDepth, stationLat, stationLon,
                stationElevation, phaseType, travelTime, takeOffAzi,
                takeOffDip, dtdd, dtdh);
            return std::make_tuple(
                travelTime, takeOffAzi, takeOffDip, dtdd, dtdh);
          },
          py::arg("eventLat"), py::arg("eventLon"), py::arg("eventDepth"),
          py::arg("stationLat"), py::arg("stationLon"),
          py::arg("stationElevation"), py::arg("phaseType"));
}
