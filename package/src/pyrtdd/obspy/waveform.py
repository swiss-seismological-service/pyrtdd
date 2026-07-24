"""obspy-backed implementations of `pyrtdd.hdd.Proxy`.

This module is not imported by `pyrtdd` or `pyrtdd.hdd`, so obspy is only
required if you actually use one of these classes (`pip install pyrtdd[obspy]`).

Three backends are provided, all requiring an `obspy.Inventory` to resolve
channel orientation (dip/azimuth) for the R/T/L2 cross-correlation component
transforms:

- `StreamProxy`: wraps an already-loaded `obspy.Stream`.
- `ObspyClientProxy`: wraps any obspy client exposing `get_waveforms(...)`
  (e.g. `obspy.clients.filesystem.sds.Client`, `obspy.clients.fdsn.Client`,
  `obspy.clients.earthworm.Client`). Uses `get_waveforms_bulk` for batch
  preloading when the client supports it.
- `FileScannerProxy`: scans a local folder for waveform files (any format
  obspy can read) and serves them like an archive.
"""

import collections
import datetime
import pathlib

import numpy as np
import obspy

from pyrtdd.hdd import Proxy, Trace, ThreeComponents


def _to_utcdatetime(td):
    return obspy.UTCDateTime(td.total_seconds())


def _to_hdd_time(utcdatetime):
    return datetime.timedelta(seconds=utcdatetime.timestamp)


def _band_and_instrument_codes(channel_code):
    return channel_code[:2]


def _obspy_trace_to_hdd(tr):
    return Trace(
        tr.stats.network,
        tr.stats.station,
        tr.stats.location,
        tr.stats.channel,
        _to_hdd_time(tr.stats.starttime),
        tr.stats.sampling_rate,
        tr.data.astype(np.float64, copy=False),
    )


def _hdd_trace_to_obspy(trace):
    return obspy.Trace(
        data=np.array(trace.data(), copy=True),
        header={
            "network": trace.networkCode,
            "station": trace.stationCode,
            "location": trace.locationCode,
            "channel": trace.channelCode,
            "starttime": _to_utcdatetime(trace.startTime),
            "sampling_rate": trace.samplingFrequency,
        },
    )


def resolve_three_components(
    inventory, networkCode, stationCode, locationCode, channelCode, time, guess_zne
):
    """Resolve the (vertical, first-horizontal, second-horizontal) triplet
    for `channelCode` from an obspy Inventory, matching HDD's
    `Waveform::ThreeComponents` contract."""

    root = _band_and_instrument_codes(channelCode)

    channels = []
    try:
        selected = inventory.select(
            network=networkCode,
            station=stationCode,
            location=locationCode,
            channel=root + "?",
            time=_to_utcdatetime(time),
        )
        for net in selected:
            for sta in net:
                channels.extend(sta)
    except Exception:
        channels = []

    vertical = None
    horizontals = []
    for cha in channels:
        if abs(abs(cha.dip) - 90.0) < 1e-6:
            vertical = cha
        else:
            horizontals.append(cha)

    tc = ThreeComponents()
    if vertical is not None and len(horizontals) >= 2:
        tc.names = [vertical.code, horizontals[0].code, horizontals[1].code]
        tc.dip = [vertical.dip, horizontals[0].dip, horizontals[1].dip]
        tc.azimuth = [vertical.azimuth, horizontals[0].azimuth, horizontals[1].azimuth]
        return tc

    if not guess_zne:
        raise RuntimeError(
            f"cannot resolve component orientation for "
            f"{networkCode}.{stationCode}.{locationCode}.{root} from the "
            "supplied Inventory, and guess_zne is disabled"
        )

    tc.names = [root + "Z", root + "N", root + "E"]
    tc.dip = [-90.0, 0.0, 0.0]
    tc.azimuth = [0.0, 0.0, 90.0]
    return tc


class _ObspyProxyBase(Proxy):
    def __init__(self, inventory, guess_zne=False):
        super().__init__()
        self._inventory = inventory
        self._guess_zne = guess_zne
        self._components_cache = {}

    # --- to be implemented by subclasses ---

    def _fetch(self, networkCode, stationCode, locationCode, channelCode, starttime, endtime):
        """Return an `obspy.Trace` covering [starttime, endtime] (or as much
        of it as available), or None if nothing is available."""
        raise NotImplementedError

    # --- Proxy interface ---

    def loadTrace(self, tw, networkCode, stationCode, locationCode, channelCode):
        tr = self._fetch(
            networkCode, stationCode, locationCode, channelCode,
            _to_utcdatetime(tw.startTime), _to_utcdatetime(tw.endTime),
        )
        if tr is None:
            raise RuntimeError(
                f"no waveform data for {networkCode}.{stationCode}."
                f"{locationCode}.{channelCode}"
            )
        return _obspy_trace_to_hdd(tr)

    def loadTraces(self, request, onTraceLoaded, onTraceFailed):
        for streamId, tw in request:
            networkCode, stationCode, locationCode, channelCode = streamId.split(".")
            try:
                trace = self.loadTrace(tw, networkCode, stationCode, locationCode, channelCode)
                onTraceLoaded(streamId, tw, trace)
            except Exception as e:
                onTraceFailed(streamId, tw, str(e))

    def getComponentsInfo(self, ph):
        key = (ph.networkCode, ph.stationCode, ph.locationCode, _band_and_instrument_codes(ph.channelCode))
        if key not in self._components_cache:
            self._components_cache[key] = resolve_three_components(
                self._inventory, ph.networkCode, ph.stationCode,
                ph.locationCode, ph.channelCode, ph.time, self._guess_zne,
            )
        return self._components_cache[key]

    def filter(self, trace, filterStr):
        kind, *kwparts = filterStr.split(";")
        kwargs = {}
        for part in kwparts:
            key, value = part.split("=")
            kwargs[key] = float(value)

        tmp = obspy.Trace(
            data=np.array(trace.data(), copy=True),
            header={"sampling_rate": trace.samplingFrequency},
        )
        tmp.filter(kind, **kwargs)
        trace.data()[:] = tmp.data

    def writeTrace(self, trace, file):
        _hdd_trace_to_obspy(trace).write(file, format="MSEED")

    def readTrace(self, file):
        st = obspy.read(file)
        return _obspy_trace_to_hdd(st[0])


class StreamProxy(_ObspyProxyBase):
    """Wraps an already-loaded `obspy.Stream`."""

    def __init__(self, stream, inventory, guess_zne=False):
        super().__init__(inventory, guess_zne)
        self._stream = stream

    def _fetch(self, networkCode, stationCode, locationCode, channelCode, starttime, endtime):
        st = self._stream.select(
            network=networkCode, station=stationCode,
            location=locationCode, channel=channelCode,
        )
        if not st:
            return None
        st = st.slice(starttime, endtime)
        if not st:
            return None
        st.merge(method=1)
        return st[0]


class ObspyClientProxy(_ObspyProxyBase):
    """Wraps any obspy client exposing `get_waveforms(network, station,
    location, channel, starttime, endtime)`, e.g.
    `obspy.clients.filesystem.sds.Client`, `obspy.clients.fdsn.Client`, or
    `obspy.clients.earthworm.Client`. When the client also exposes
    `get_waveforms_bulk` (FDSN), it's used to preload/batch requests in a
    single call instead of one request per trace."""

    def __init__(self, client, inventory, guess_zne=False):
        super().__init__(inventory, guess_zne)
        self._client = client

    def _fetch(self, networkCode, stationCode, locationCode, channelCode, starttime, endtime):
        st = self._client.get_waveforms(
            networkCode, stationCode, locationCode, channelCode, starttime, endtime,
        )
        if not st:
            return None
        st.merge(method=1)
        return st[0]

    def loadTraces(self, request, onTraceLoaded, onTraceFailed):
        if not hasattr(self._client, "get_waveforms_bulk"):
            super().loadTraces(request, onTraceLoaded, onTraceFailed)
            return

        entries = []
        bulk = []
        for streamId, tw in request:
            networkCode, stationCode, locationCode, channelCode = streamId.split(".")
            t0, t1 = _to_utcdatetime(tw.startTime), _to_utcdatetime(tw.endTime)
            entries.append((streamId, tw, networkCode, stationCode, locationCode, channelCode))
            bulk.append((networkCode, stationCode, locationCode, channelCode, t0, t1))

        try:
            st = self._client.get_waveforms_bulk(bulk)
        except Exception as e:
            for streamId, tw, *_ in entries:
                onTraceFailed(streamId, tw, str(e))
            return

        for streamId, tw, networkCode, stationCode, locationCode, channelCode in entries:
            sel = st.select(
                network=networkCode, station=stationCode,
                location=locationCode, channel=channelCode,
            )
            if not sel:
                onTraceFailed(streamId, tw, "no data returned by get_waveforms_bulk")
                continue
            sel.merge(method=1)
            try:
                onTraceLoaded(streamId, tw, _obspy_trace_to_hdd(sel[0]))
            except Exception as e:
                onTraceFailed(streamId, tw, str(e))


class FileScannerProxy(_ObspyProxyBase):
    """Scans a local folder for waveform files (any format obspy can read,
    e.g. miniSEED) and serves them like an archive. The folder is indexed
    once at construction time by reading file headers only."""

    def __init__(self, folder, inventory, guess_zne=False, recursive=True):
        super().__init__(inventory, guess_zne)
        self._index = self._scan(pathlib.Path(folder), recursive)

    @staticmethod
    def _scan(folder, recursive):
        index = collections.defaultdict(list)
        pattern = "**/*" if recursive else "*"
        for path in folder.glob(pattern):
            if not path.is_file():
                continue
            try:
                st = obspy.read(str(path), headonly=True)
            except Exception:
                continue
            for tr in st:
                key = (tr.stats.network, tr.stats.station, tr.stats.location, tr.stats.channel)
                index[key].append((str(path), tr.stats.starttime, tr.stats.endtime))
        return index

    def _fetch(self, networkCode, stationCode, locationCode, channelCode, starttime, endtime):
        entries = self._index.get((networkCode, stationCode, locationCode, channelCode), [])
        matching = [f for f, s, e in entries if s <= endtime and e >= starttime]
        if not matching:
            return None

        st = obspy.Stream()
        for f in matching:
            st += obspy.read(f, starttime=starttime, endtime=endtime)
        if not st:
            return None
        st.merge(method=1)
        return st[0]
