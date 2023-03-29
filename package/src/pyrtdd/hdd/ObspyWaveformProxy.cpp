#include "ObspyWaveformProxy.h"
#include "timewindow.h"
#include "utctime.h"
#include "waveform.h"

#include <algorithm>
#include <cstddef>
#include <exception>
#include <iterator>
#include <memory>
#include <numeric>
#include <optional>
#include <pybind11/attr.h>
#include <pybind11/buffer_info.h>
#include <pybind11/detail/common.h>
#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/pytypes.h>
#include <stdexcept>
#include <string>
#include <unordered_map>

namespace py = pybind11;

namespace HDD::Waveform {

ObspyWaveformProxy::ObspyWaveformProxy(py::object stream)
    : _stream(std::move(stream))
    , _map(detail::CreateIndexMap(_stream.attr("traces"))){};

auto ObspyWaveformProxy::loadTrace(
    TimeWindow const &tw, std::string const &networkCode,
    std::string const &stationCode, std::string const &locationCode,
    std::string const &channelCode) -> std::unique_ptr<Trace> {

  using namespace detail;

  auto k =
      networkCode + "." + stationCode + "." + locationCode + "." + channelCode;

  auto tr = GetTrace(*this, GetTraceIdx(*this, k));
  auto span = GetTraceData(tr);
  double sr = StatsAttr<double>("sampling_rate", tr);
  auto time = StatsAttr("starttime", tr).attr("__str__")().cast<std::string>();

  return std::make_unique<Trace>(
      networkCode, stationCode, locationCode, channelCode,
      UTCClock::fromString(time), sr, span.data(), span.size());
};

void ObspyWaveformProxy::loadTraces(
    std::unordered_multimap<std::string, TimeWindow const> const &request,
    const std::function<
        void(std::string const &, TimeWindow const &, std::unique_ptr<Trace>)>
        &onTraceLoaded,
    const std::function<
        void(std::string const &, TimeWindow const &, std::string const &)>
        &onTraceFailed) {
  throw std::runtime_error("LoadTraces not yet implemented.");
};

void ObspyWaveformProxy::getComponentsInfo(
    Catalog::Phase const &ph, ThreeComponents &components){};
void ObspyWaveformProxy::filter(Trace &trace, std::string const &filterStr) {
  throw std::runtime_error("getComponentsInfo not yet implemented.");
};

void ObspyWaveformProxy::writeTrace(
    Trace const &trace, std::string const &file) {
  throw std::runtime_error("writeTrace not yet implemented.");
};

auto ObspyWaveformProxy::readTrace(std::string const &file)
    -> std::unique_ptr<Trace> {
  throw std::runtime_error("readTrace not yet implemented.");
};

namespace detail {

auto CreateIndexMap(py::list const &tr)
    -> std::unordered_map<std::string, std::size_t> {

  using Str = std::string;

  // Extract a trace's identifier.
  auto key = [=](auto const &tr,
                 auto const idx) -> std::pair<std::string, std::size_t> {
    return {
        StatsAttr<Str>("network", tr) + "." + StatsAttr<Str>("station", tr) +
            "." + StatsAttr<Str>("location", tr) + "." +
            StatsAttr<Str>("channel", tr),
        idx};
  };

  std::vector<std::size_t> idx(tr.size());
  std::unordered_map<std::string, std::size_t> map;

  std::iota(idx.begin(), idx.end(), 0);
  std::transform(
      tr.begin(), tr.end(), idx.begin(), std::inserter(map, map.end()), key);

  return map;
}

auto GetTraceData(py::object const &tr) -> std::span<double const> {
  auto data = py::cast<py::array_t<double>>(tr.attr("data"));
  return {data.data(), data.data() + data.size()};  // NOLINT
};

auto GetTraceIdx(ObspyWaveformProxy const &p, std::string const &id)
    -> std::size_t {

  auto idx = p.Map().find(id);
  if (idx == p.Map().end()) {
    throw std::runtime_error(
        std::string("Trace with identifier " + id + " not found."));
  }
  return idx->second;
}

auto GetTrace(ObspyWaveformProxy const &p, std::size_t idx) -> py::object {
  return py::cast<py::list>(p.Stream().attr("traces"))[idx];
}

}  // namespace detail

}  // namespace HDD::Waveform

using HDD::Waveform::ObspyWaveformProxy;

void InitObspyWaveformProxy(py::module_ &m) {

  py::class_<HDD::Waveform::Proxy, std::shared_ptr<HDD::Waveform::Proxy>>(
      m, "Proxy");

  py::class_<
      ObspyWaveformProxy, HDD::Waveform::Proxy,
      std::shared_ptr<ObspyWaveformProxy>>(m, "ObspyWaveformProxy")
      .def(py::init<py::object>())
      .def(
          "getTraceData",
          [](ObspyWaveformProxy &p, std::string const &nc,
             std::string const &sc, std::string const &lc,
             std::string const &cc) {
            using namespace HDD::Waveform::detail;
            auto const k = nc + "." + sc + "." + lc + "." + cc;
            auto const tr = GetTraceData(GetTrace(p, GetTraceIdx(p, k)));
            return py::array(py::ssize_t(tr.size()), tr.data());
          })
      .def(
          "_getTraceAddr",
          [](ObspyWaveformProxy &p, std::string const &nc,
             std::string const &sc, std::string const &lc,
             std::string const &cc) {
            using namespace HDD::Waveform::detail;
            auto const k = nc + "." + sc + "." + lc + "." + cc;
	    std::ostringstream tmp;
	    tmp << GetTraceData(GetTrace(p, GetTraceIdx(p, k))).data();
            return tmp.str();
          });

  // Also just init "NoWaveformProxy" so we can use it.
  py::class_<
      HDD::Waveform::NoWaveformProxy, HDD::Waveform::Proxy,
      std::shared_ptr<HDD::Waveform::NoWaveformProxy>>(m, "NoWaveformProxy")
      .def(py::init<>());
}
