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

/**
 * @brief Waveform proxy wrapping an Obspy stream.
 *
 * An Obspy Stream is the canonical way to hold a collection of data in Obspy's
 * Python processing workflow. This proxy object is a lightweight C++ wrapper
 * around a stream that conforms the SCRTDD's "Proxy" interface. No internal
 * copies of the Obspy traces are made, except for those that may happen within
 * the SCRTDD trace object.
 */
class ObspyWaveformProxy : public Proxy {

 public:

  /**
   * @brief Construct a new Obspy Waveform Proxy from an Obspy stream.
   *
   * @param [in] stream The Obspy stream.
   */
  explicit ObspyWaveformProxy(pybind11::object stream);

  /**
   * @brief Load a trace from the encapsulated Obspy stream.
   *
   * Will throw a runtime error if the trace is not present.
   *
   * @param [in] tw The time window (currently ignored).
   * @param [in] networkCode The network code.
   * @param [in] stationCode The station code.
   * @param [in] locationCode The location code.
   * @param [in] channelCode The channel code.
   * @return An SCRTDD Trace object that wraps the Obspy trace.
   */
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

  inline auto Map() const -> auto const & { return _map; }
  inline auto Stream() const -> auto const & { return _stream; }

 private:
  pybind11::object _stream{};                           // NOLINT
  std::unordered_map<std::string, std::size_t> _map{};  // NOLINT
};

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

/**
 * @brief Get the index of a trace residing in an Obspy waveform proxy.
 *
 * The id should be a concatented version of the identification codes,
 * specifically "NetworkCode.StationCode.LocationCode.ChannelCode". If the proxy
 * object is found not to contain the specified trace and runtime error is
 * thrown.
 *
 * @param [in] p The waveform proxy.
 * @param [in] id The identifier of the trace to get.
 * @return The trace index.
 */
auto GetTraceIdx(ObspyWaveformProxy const &p, std::string const &id)
    -> std::size_t;

/**
 * @brief Return the Obspy Trace object given its index in a stream.
 *
 * No bounds checking is done to ensure that the index is contained within the
 * stream's size.
 *
 * @param [in] p The waveform proxy.
 * @param [in] idx The trace index.
 * @return The Obspy Trace object as a pybind11 object.
 */
auto GetTrace(ObspyWaveformProxy const &p, std::size_t idx) -> pybind11::object;

/**
 * @brief Get an attribute from an Obspy "stats" object attached to a trace.
 *
 * @tparam T The expected type of the return value.
 * @param [in] k The key to get.
 * @param [in] tr The trace to get the stats from.
 * @return The associated value, or an empty value.
 */
template <typename T = pybind11::object>
auto StatsAttr(std::string const &k, auto const &tr) {
  pybind11::dict m = tr.attr("stats");
  for (auto const &[_k, v] : m) {
    if (_k.cast<std::string>() == k) { return v.cast<T>(); }
  };
  return T{};
}

}  // namespace detail

}  // namespace HDD::Waveform
