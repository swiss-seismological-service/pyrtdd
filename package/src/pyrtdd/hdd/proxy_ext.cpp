#include "catalog.h"
#include "pybind11/functional.h"
#include "pybind11/pybind11.h"
#include "pybind11/stl.h"
#include "timewindow.h"
#include "trace.h"
#include "waveform.h"

#include <memory>
#include <string>
#include <unordered_map>

namespace py = pybind11;

using HDD::Catalog;
using HDD::Trace;
using HDD::TimeWindow;
using HDD::Waveform::Proxy;
using HDD::Waveform::ThreeComponents;

namespace {

// Trampoline: lets `Proxy` be subclassed directly in Python. Combined with
// the `smart_holder` binding below, an instance created in Python can have
// its ownership moved into a C++ `unique_ptr<Proxy>` (as `HDD::DD`'s
// constructor does) and virtual calls still dispatch back to the Python
// overrides afterwards.
class PyProxy : public Proxy, public py::trampoline_self_life_support {
public:
  using Proxy::Proxy;

  std::unique_ptr<Trace> loadTrace(
      TimeWindow const &tw, std::string const &networkCode,
      std::string const &stationCode, std::string const &locationCode,
      std::string const &channelCode) override {
    PYBIND11_OVERRIDE_PURE(
        std::unique_ptr<Trace>, Proxy, loadTrace, tw, networkCode,
        stationCode, locationCode, channelCode);
  }

  // `request`'s type (`unordered_multimap`) has no pybind11 STL caster, so
  // this override is hand-rolled instead of using the PYBIND11_OVERRIDE_PURE
  // macro: it's converted into a plain list of (streamId, TimeWindow) pairs,
  // which the callback types (`std::function`, via pybind11/functional.h)
  // and `TimeWindow` (bound separately) both cast automatically.
  void loadTraces(
      std::unordered_multimap<std::string, TimeWindow const> const &request,
      OnTraceLoadedCallback const &onTraceLoaded,
      OnTraceFailedCallback const &onTraceFailed) override {
    py::gil_scoped_acquire gil;
    py::function override = py::get_override(this, "loadTraces");
    if (!override) {
      py::pybind11_fail("Tried to call pure virtual function \"Proxy::loadTraces\"");
    }
    py::list pyRequest;
    for (auto const &kv : request) {
      pyRequest.append(py::make_tuple(kv.first, kv.second));
    }
    override(pyRequest, onTraceLoaded, onTraceFailed);
  }

  // Returns a `ThreeComponents` from Python instead of mutating an
  // out-parameter: raw C-array struct members don't support pybind11's
  // by-reference mutation, so the trampoline copies the returned value into
  // `components` itself.
  void getComponentsInfo(
      Catalog::Phase const &ph, ThreeComponents &components) override {
    py::gil_scoped_acquire gil;
    py::function override = py::get_override(this, "getComponentsInfo");
    if (!override) {
      py::pybind11_fail(
          "Tried to call pure virtual function \"Proxy::getComponentsInfo\"");
    }
    components = override(ph).cast<ThreeComponents>();
  }

  void filter(Trace &trace, std::string const &filterStr) override {
    PYBIND11_OVERRIDE_PURE(void, Proxy, filter, trace, filterStr);
  }

  void writeTrace(Trace const &trace, std::string const &file) override {
    PYBIND11_OVERRIDE_PURE(void, Proxy, writeTrace, trace, file);
  }

  std::unique_ptr<Trace> readTrace(std::string const &file) override {
    PYBIND11_OVERRIDE_PURE(std::unique_ptr<Trace>, Proxy, readTrace, file);
  }
};

}  // namespace

void InitProxy(py::module_ &m) {

  py::classh<Proxy, PyProxy>(m, "Proxy")
      .def(py::init<>())
      .def("loadTrace", &Proxy::loadTrace)
      .def("getComponentsInfo", &Proxy::getComponentsInfo)
      .def("filter", &Proxy::filter)
      .def("writeTrace", &Proxy::writeTrace)
      .def("readTrace", &Proxy::readTrace);

  py::classh<HDD::Waveform::NoWaveformProxy, Proxy>(m, "NoWaveformProxy")
      .def(py::init<>());
}
