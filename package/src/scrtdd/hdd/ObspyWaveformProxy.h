#include "catalog.h"
#include "pybind11/embed.h"
#include "pybind11/pybind11.h"
#include "pybind11/stl.h"
#include "timewindow.h"
#include "waveform.h"

#include <iostream>
#include <memory>
#include <pybind11/pytypes.h>
#include <span>
#include <string>
#include <unordered_map>
#include <utility>

namespace HDD::Waveform {

namespace detail {

/**
 * @brief Construct a mapping between traces indices and identifiers.
 *
 * For quick lookup, creates an unordered map that maps an identifier
 * (network.station.location.channel) to an index in a list of traces.
 *
 * @param [in] traces The list of traces.
 * @return A map of identifiers to trace indices.
 */
auto CreateIndexMap(pybind11::list const &traces)
    -> std::unordered_map<std::string, std::size_t>;

/**
 * @brief Wrap the data pointed to by a trace in a span.
 *
 * A span is a simple wrapper around a pointer and a size. This class then
 * simply wraps the Obspy trace's data in place.
 *
 * @param [in] tr The trace.
 * @return A span over the trace data.
 */
auto GetTraceData(pybind11::object const &tr) -> std::span<double const>;

}  // namespace detail

class ObspyWaveformProxy : public Proxy {

 public:
  explicit ObspyWaveformProxy(pybind11::object stream);

  auto loadTrace(
      TimeWindow const &tw, std::string const &networkCode,
      std::string const &stationCode, std::string const &locationCode,
      std::string const &channelCode) -> std::unique_ptr<Trace> override;

  void loadTraces(
      std::unordered_multimap<std::string, TimeWindow const> const &request,
      const std::function<
          void(std::string const &, TimeWindow const &, std::unique_ptr<Trace>)>
          &onTraceLoaded,
      const std::function<
          void(std::string const &, TimeWindow const &, std::string const &)>
          &onTraceFailed) override;

  void getComponentsInfo(
      Catalog::Phase const &ph, ThreeComponents &components) override;

  void filter(Trace &trace, std::string const &filterStr) override;

  void writeTrace(Trace const &trace, std::string const &file) override;

  auto readTrace(std::string const &file) -> std::unique_ptr<Trace> override;

 private:
  pybind11::object _stream{};                           // NOLINT
  std::unordered_map<std::string, std::size_t> _map{};  // NOLINT
};

}  // namespace HDD::Waveform
