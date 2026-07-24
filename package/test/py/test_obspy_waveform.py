import datetime
import os
import tempfile

import numpy as np
import obspy
import pytest
from obspy.core.inventory import Channel, Inventory, Network, Station

from pyrtdd.hdd import TimeWindow
from pyrtdd.obspy.waveform import (
    FileScannerProxy,
    ObspyClientProxy,
    StreamProxy,
    resolve_three_components,
)

T0 = obspy.UTCDateTime(2020, 1, 1)


def _hdd_time(utcdatetime):
    return datetime.timedelta(seconds=utcdatetime.timestamp)


def _tw(start, end):
    return TimeWindow(_hdd_time(start), _hdd_time(end))


class _FakePhase:
    def __init__(self, networkCode, stationCode, locationCode, channelCode, time):
        self.networkCode = networkCode
        self.stationCode = stationCode
        self.locationCode = locationCode
        self.channelCode = channelCode
        self.time = time


@pytest.fixture
def inventory():
    chans = [
        Channel(
            code="HHZ", location_code="", latitude=0, longitude=0,
            elevation=0, depth=0, dip=-90.0, azimuth=0.0,
        ),
        Channel(
            code="HHN", location_code="", latitude=0, longitude=0,
            elevation=0, depth=0, dip=0.0, azimuth=0.0,
        ),
        Channel(
            code="HHE", location_code="", latitude=0, longitude=0,
            elevation=0, depth=0, dip=0.0, azimuth=90.0,
        ),
    ]
    sta = Station(code="STA", latitude=0, longitude=0, elevation=0, channels=chans)
    net = Network(code="XX", stations=[sta])
    return Inventory(networks=[net])


def test_resolve_three_components(inventory):
    tc = resolve_three_components(
        inventory, "XX", "STA", "", "HHZ", _hdd_time(T0 + 1), guess_zne=False
    )
    assert tc.names == ["HHZ", "HHN", "HHE"]
    assert tc.dip == [-90.0, 0.0, 0.0]
    assert tc.azimuth == [0.0, 0.0, 90.0]


def test_resolve_three_components_missing_raises_without_guess():
    empty = Inventory(networks=[])
    with pytest.raises(RuntimeError):
        resolve_three_components(
            empty, "YY", "STB", "", "HHZ", _hdd_time(T0 + 1), guess_zne=False
        )


def test_resolve_three_components_guess_zne_fallback():
    empty = Inventory(networks=[])
    tc = resolve_three_components(
        empty, "YY", "STB", "", "HHZ", _hdd_time(T0 + 1), guess_zne=True
    )
    assert tc.names == ["HHZ", "HHN", "HHE"]
    assert tc.dip == [-90.0, 0.0, 0.0]
    assert tc.azimuth == [0.0, 0.0, 90.0]


def _make_stream():
    data = np.linspace(0, 1, 1000)
    tr = obspy.Trace(
        data,
        {
            "network": "XX", "station": "STA", "location": "", "channel": "HHZ",
            "starttime": T0, "sampling_rate": 100.0,
        },
    )
    return obspy.Stream([tr])


def test_stream_proxy_load_trace(inventory):
    proxy = StreamProxy(_make_stream(), inventory)
    tr = proxy.loadTrace(_tw(T0 + 1, T0 + 2), "XX", "STA", "", "HHZ")
    assert tr.networkCode == "XX"
    assert tr.sampleCount > 0


def test_stream_proxy_load_trace_missing_raises(inventory):
    proxy = StreamProxy(_make_stream(), inventory)
    with pytest.raises(RuntimeError):
        proxy.loadTrace(_tw(T0 + 1, T0 + 2), "XX", "NOPE", "", "HHZ")


def test_stream_proxy_get_components_info(inventory):
    proxy = StreamProxy(_make_stream(), inventory)
    ph = _FakePhase("XX", "STA", "", "HHZ", _hdd_time(T0 + 1))
    tc = proxy.getComponentsInfo(ph)
    assert tc.names == ["HHZ", "HHN", "HHE"]


def test_stream_proxy_filter(inventory):
    proxy = StreamProxy(_make_stream(), inventory)
    tr = proxy.loadTrace(_tw(T0 + 1, T0 + 2), "XX", "STA", "", "HHZ")
    before = np.array(tr.data(), copy=True)
    proxy.filter(tr, "bandpass;freqmin=1;freqmax=10;corners=4")
    assert not np.allclose(before, tr.data())


def test_stream_proxy_write_read_trace_roundtrip(inventory):
    proxy = StreamProxy(_make_stream(), inventory)
    tr = proxy.loadTrace(_tw(T0 + 1, T0 + 2), "XX", "STA", "", "HHZ")
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "t.mseed")
        proxy.writeTrace(tr, path)
        tr2 = proxy.readTrace(path)
    np.testing.assert_allclose(tr2.data(), tr.data())


def test_stream_proxy_load_traces_batch(inventory):
    proxy = StreamProxy(_make_stream(), inventory)
    request = [("XX.STA..HHZ", _tw(T0 + 1, T0 + 2)), ("XX.NOPE..HHZ", _tw(T0 + 1, T0 + 2))]
    loaded, failed = {}, {}
    proxy.loadTraces(
        request,
        lambda sid, tw, tr: loaded.__setitem__(sid, tr),
        lambda sid, tw, err: failed.__setitem__(sid, err),
    )
    assert "XX.STA..HHZ" in loaded
    assert "XX.NOPE..HHZ" in failed


def test_file_scanner_proxy(tmp_path):
    data = np.linspace(0, 1, 1000)
    tr = obspy.Trace(
        data,
        {
            "network": "XX", "station": "STA", "location": "", "channel": "HHZ",
            "starttime": T0, "sampling_rate": 100.0,
        },
    )
    tr.write(str(tmp_path / "day1.mseed"), format="MSEED")

    proxy = FileScannerProxy(tmp_path, inventory=None, guess_zne=True)
    hdd_tr = proxy.loadTrace(_tw(T0 + 1, T0 + 2), "XX", "STA", "", "HHZ")
    assert hdd_tr.sampleCount > 0

    with pytest.raises(RuntimeError):
        proxy.loadTrace(_tw(T0 + 1, T0 + 2), "XX", "NOPE", "", "HHZ")


def test_obspy_client_proxy_uses_bulk_when_available():
    calls = {"bulk": 0, "single": 0}

    class FakeBulkClient:
        def get_waveforms_bulk(self, bulk):
            calls["bulk"] += 1
            st = obspy.Stream()
            for net, sta, loc, cha, t0, t1 in bulk:
                st += obspy.Trace(
                    np.linspace(0, 1, 500),
                    {
                        "network": net, "station": sta, "location": loc,
                        "channel": cha, "starttime": t0, "sampling_rate": 100.0,
                    },
                )
            return st

        def get_waveforms(self, *args, **kwargs):
            calls["single"] += 1
            raise AssertionError("should not be called when bulk is available")

    proxy = ObspyClientProxy(FakeBulkClient(), inventory=None, guess_zne=True)
    request = [
        ("XX.STA..HHZ", _tw(T0 + 1, T0 + 2)),
        ("XX.STB..HHZ", _tw(T0 + 1, T0 + 2)),
    ]
    loaded, failed = {}, {}
    proxy.loadTraces(
        request,
        lambda sid, tw, tr: loaded.__setitem__(sid, tr),
        lambda sid, tw, err: failed.__setitem__(sid, err),
    )
    assert set(loaded) == {"XX.STA..HHZ", "XX.STB..HHZ"}
    assert not failed
    assert calls["bulk"] == 1
    assert calls["single"] == 0


def test_obspy_client_proxy_falls_back_to_loop_without_bulk():
    class FakeSimpleClient:
        def get_waveforms(self, net, sta, loc, cha, t0, t1):
            return obspy.Stream(
                [
                    obspy.Trace(
                        np.linspace(0, 1, 500),
                        {
                            "network": net, "station": sta, "location": loc,
                            "channel": cha, "starttime": t0, "sampling_rate": 100.0,
                        },
                    )
                ]
            )

    proxy = ObspyClientProxy(FakeSimpleClient(), inventory=None, guess_zne=True)
    tr = proxy.loadTrace(_tw(T0 + 1, T0 + 2), "XX", "STA", "", "HHZ")
    assert tr.sampleCount > 0
