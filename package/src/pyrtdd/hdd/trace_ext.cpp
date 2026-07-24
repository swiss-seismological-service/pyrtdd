#include "pybind11/chrono.h"
#include "pybind11/numpy.h"
#include "pybind11/operators.h"
#include "pybind11/pybind11.h"
#include "pybind11/stl.h"
#include "timewindow.h"
#include "trace.h"
#include "utctime.h"
#include "waveform.h"

#include <array>
#include <string>
#include <vector>

namespace py = pybind11;

using HDD::Trace;
using HDD::TimeWindow;
using HDD::Waveform::ThreeComponents;

void InitTimeWindow(py::module_ &m) {

  py::class_<TimeWindow>(m, "TimeWindow")
      .def(py::init<>())
      .def(py::init<HDD::UTCTime const &, HDD::UTCTime const &>())
      .def(py::self == py::self)  // NOLINT
      .def(py::self != py::self)  // NOLINT
      .def_property_readonly("startTime", &TimeWindow::startTime)
      .def_property_readonly("endTime", &TimeWindow::endTime)
      .def("contains", py::overload_cast<HDD::UTCTime const &>(
                            &TimeWindow::contains, py::const_))
      .def("empty", &TimeWindow::empty);
}

void InitThreeComponents(py::module_ &m) {

  auto tc =
      py::class_<ThreeComponents>(m, "ThreeComponents")
          .def(py::init<>())
          .def_property(
              "names",
              [](ThreeComponents const &c) {
                return std::vector<std::string>{c.names[0], c.names[1], c.names[2]};
              },
              [](ThreeComponents &c, std::array<std::string, 3> const &v) {
                for (int i = 0; i < 3; i++) c.names[i] = v[i];
              })
          .def_property(
              "dip",
              [](ThreeComponents const &c) {
                return std::vector<double>{c.dip[0], c.dip[1], c.dip[2]};
              },
              [](ThreeComponents &c, std::array<double, 3> const &v) {
                for (int i = 0; i < 3; i++) c.dip[i] = v[i];
              })
          .def_property(
              "azimuth",
              [](ThreeComponents const &c) {
                return std::vector<double>{
                    c.azimuth[0], c.azimuth[1], c.azimuth[2]};
              },
              [](ThreeComponents &c, std::array<double, 3> const &v) {
                for (int i = 0; i < 3; i++) c.azimuth[i] = v[i];
              });

  py::enum_<ThreeComponents::Component>(tc, "Component")
      .value("Vertical", ThreeComponents::Vertical)
      .value("FirstHorizontal", ThreeComponents::FirstHorizontal)
      .value("SecondHorizontal", ThreeComponents::SecondHorizontal);
}

void InitTrace(py::module_ &m) {

  InitTimeWindow(m);
  InitThreeComponents(m);

  py::class_<Trace>(m, "Trace")
      .def(
          py::init([](std::string const &net, std::string const &sta,
                      std::string const &loc, std::string const &cha,
                      HDD::UTCTime const &stime, double samplingFrequency,
                      py::array_t<double, py::array::c_style |
                                              py::array::forcecast> data) {
            py::buffer_info buf = data.request();
            return Trace(
                net, sta, loc, cha, stime, samplingFrequency,
                static_cast<double const *>(buf.ptr),
                static_cast<size_t>(buf.size));
          }),
          py::arg("networkCode"), py::arg("stationCode"),
          py::arg("locationCode"), py::arg("channelCode"),
          py::arg("startTime"), py::arg("samplingFrequency"),
          py::arg("data"))
      .def_property(
          "networkCode", &Trace::networkCode, &Trace::setNetworkCode)
      .def_property(
          "stationCode", &Trace::stationCode, &Trace::setStationCode)
      .def_property(
          "locationCode", &Trace::locationCode, &Trace::setLocationCode)
      .def_property(
          "channelCode", &Trace::channelCode, &Trace::setChannelCode)
      .def_property(
          "startTime", &Trace::startTime, &Trace::setStartTime)
      .def_property_readonly("endTime", &Trace::endTime)
      .def_property(
          "samplingFrequency", &Trace::samplingFrequency,
          &Trace::setSamplingFrequency)
      .def_property_readonly("sampleCount", &Trace::sampleCount)
      .def_property_readonly("timeWindow", &Trace::timeWindow)
      // A mutable, zero-copy view onto the trace's own data buffer: writes
      // through this array mutate the Trace in place (used by proxy `filter`
      // implementations). `base` ties the array's lifetime to `self` so the
      // buffer stays valid as long as the returned array is referenced.
      .def("data", [](py::object self) {
        Trace &t = self.cast<Trace &>();
        return py::array_t<double>(
            {static_cast<py::ssize_t>(t.sampleCount())}, {sizeof(double)},
            t.data(), self);
      });
}
