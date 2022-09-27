#include "ObspyWaveformProxy.h"
#include "utctime.h"

#include <algorithm>
#include <cstddef>
#include <exception>
#include <iterator>
#include <memory>
#include <numeric>
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
    , _map(detail::CreateIndexMap(_stream.attr("traces"))) {

  for (auto [k, v] : _map) { std::cout << k << "\n"; }
};

auto ObspyWaveformProxy::loadTrace(
    TimeWindow const &tw, std::string const &networkCode,
    std::string const &stationCode, std::string const &locationCode,
    std::string const &channelCode) -> std::unique_ptr<Trace> {

  auto const k =
      networkCode + "." + stationCode + "." + locationCode + "." + channelCode;

  auto idx = _map.find(k);
  if (idx == _map.end()) {
    throw std::runtime_error(
        std::string("Trace with identifier ") + k + " not found.");
  }

  auto tr = py::cast<py::list>(_stream.attr("traces"));
  auto span = detail::GetTraceData(tr[idx->second]);

  return std::make_unique<Trace>(
      networkCode, stationCode, locationCode, channelCode, UTCTime(), 1.0,
      span.data(), span.size());
};

void ObspyWaveformProxy::loadTraces(
    std::unordered_multimap<std::string, TimeWindow const> const &request,
    const std::function<
        void(std::string const &, TimeWindow const &, std::unique_ptr<Trace>)>
        &onTraceLoaded,
    const std::function<
        void(std::string const &, TimeWindow const &, std::string const &)>
        &onTraceFailed){};
void ObspyWaveformProxy::getComponentsInfo(
    Catalog::Phase const &ph, ThreeComponents &components){};
void ObspyWaveformProxy::filter(Trace &trace, std::string const &filterStr){};

void ObspyWaveformProxy::writeTrace(
    Trace const &trace, std::string const &file){};

auto ObspyWaveformProxy::readTrace(std::string const &file)
    -> std::unique_ptr<Trace> {
  return nullptr;
};

auto detail::CreateIndexMap(py::list const &tr)
    -> std::unordered_map<std::string, std::size_t> {

  // Extract a generic attribute from an Obspy "stats" object.
  auto attr = [](std::string const &k, auto const &tr) {
    py::dict m = tr.attr("stats");
    for (auto const &[_k, v] : m) {
      if (_k.cast<std::string>() == k) { return v.cast<std::string>(); }
    };
    return std::string("");
  };

  // Extract a trace's identifier.
  auto key = [=](auto const &tr,
                 auto const idx) -> std::pair<std::string, std::size_t> {
    return {
        attr("network", tr) + "." + attr("station", tr) + "." +
            attr("location", tr) + "." + attr("channel", tr),
        idx};
  };

  std::vector<std::size_t> idx(tr.size());
  std::unordered_map<std::string, std::size_t> map;

  std::iota(idx.begin(), idx.end(), 0);
  std::transform(
      tr.begin(), tr.end(), idx.begin(), std::inserter(map, map.end()), key);

  return map;
}

auto detail::GetTraceData(py::object const &tr) -> std::span<double const> {
  py::array_t<double> data = py::cast<py::object>(tr.attr("data"));
  return {data.data(), data.data() + data.size()};  // NOLINT
};

}  // namespace HDD::Waveform

void InitObspyWaveformProxy(pybind11::module_ &m) {
  py::class_<HDD::Waveform::ObspyWaveformProxy>(m, "ObspyWaveformProxy")
      .def(pybind11::init<pybind11::object>());
}
