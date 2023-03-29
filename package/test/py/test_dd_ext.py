import datetime
import pathlib

import numpy as np
import obspy
from pyrtdd.hdd import (
    Catalog,
    Config,
    ConstantVelocity,
    ObspyWaveformProxy,
    UTCClock,
    DD,
    SolverOptions,
    ClusteringOptions,
    NoWaveformProxy,
)

DATA_DIR = pathlib.Path(__file__).parent / "data"

Event = Catalog.Event
Station = Catalog.Station
Phase = Catalog.Phase
PhaseType = Catalog.Phase.Type

event_file = str(DATA_DIR / "starting-event.csv")
phase_file = str(DATA_DIR / "starting-phase.csv")
station_file = str(DATA_DIR / "starting-station.csv")


def test_config_defaults():

    c = Config()

    assert c.validPphases == ["Pg", "P", "Px"]
    assert c.validSphases == ["Sg", "S", "Sx"]
    assert c.compatibleChannels == []
    assert c.diskTraceMinLen == 10

    xc_p = c.XCorr(0.5, -0.5, 0.5, 0.5, ["Z"])
    xc_s = c.XCorr(0.5, -0.5, 0.75, 0.5, ["H"])
    assert c.xcorr == {PhaseType.P: xc_p, PhaseType.S: xc_s}

    assert c.snr == c.SNR_TYPE(2, -3.0, -0.35, -0.35, 1)
    assert c.wfFilter == c.WF_FILTER_TYPE("ITAPER(1)>>BW_HLP(2,1,20)", 0, 1)


def test_config_mutations():

    c = Config()
    c.validPphases = ["X", "y"]
    c.xcorr[PhaseType.S].components = ["my_fav_component"]
    c.wfFilter.filterStr = "my_fav_filter_string"

    assert c.validPphases == ["X", "y"]
    assert c.xcorr == {
        PhaseType.P: c.XCorr(0.5, -0.5, 0.5, 0.5, ["Z"]),
        PhaseType.S: c.XCorr(0.5, -0.5, 0.75, 0.5, ["my_fav_component"]),
    }
    assert c.wfFilter == c.WF_FILTER_TYPE("my_fav_filter_string", 0, 1)
    assert c.snr == c.SNR_TYPE(2, -3.0, -0.35, -0.35, 1)


def test_cv_ttt():

    # This is just a smoke test as there are no public methods
    cv_ttt = ConstantVelocity(2.0, 1.0)


def test_station():

    s0 = Station("xy", 90.0, 0.0, 0.0, "XX", "YY", "ZZ")
    s1 = Station("xy", 90.0, 0.0, 0.0, "XX", "YY", "ZZ")
    s2 = Station("xy", 80.0, 0.0, 0.0, "XX", "YY", "ZZ")

    assert s0.id == "xy"
    assert s0.latitude == 90.0
    assert s0.longitude == 0.0
    assert s0.networkCode == "XX"
    assert s0.stationCode == "YY"
    assert s0.locationCode == "ZZ"

    assert s0 == s1
    assert s0 != s2


def test_utc_time():

    assert UTCClock.fromString(
        "1970-01-01T00:00:00.000Z"
    ) == datetime.timedelta(0)
    assert UTCClock.fromString(
        "1970-01-01T01:00:00.000Z"
    ) == datetime.timedelta(0, 0, 0, 0, 0, 1)
    assert UTCClock.fromString(
        "1980-01-01T01:00:00.000Z"
    ) == datetime.timedelta(3652, 0, 0, 0, 0, 1)


def test_event_phases():

    phases = Event.PHASES_TYPE(0, 0, +1.0, +0.5, +2.0)
    assert phases.usedP == 0
    assert phases.usedS == 0
    assert phases.stationDistMedian == 1.0
    assert phases.stationDistMin == 0.5
    assert phases.stationDistMax == 2.0

    phases.stationDistMin = 1.0
    assert phases.stationDistMin == 1.0


def test_event_dd():

    dd = Event.DD_TYPE(0, 1, 2, 3, 0.0, 1.0, 2.0, 3.0)
    assert dd.numTTp == 0
    assert dd.numTTs == 1
    assert dd.numCCp == 2
    assert dd.numCCs == 3
    assert dd.startResidualMedian == 0.0
    assert dd.startResidualMAD == 1.0
    assert dd.finalResidualMedian == 2.0
    assert dd.finalResidualMAD == 3.0

    dd.numCCp = 0
    assert dd.numCCp == 0


def test_reloc_info_default():

    reloc_info = Event.RELOC_INFO_TYPE()
    assert not reloc_info.isRelocated


def test_reloc_info():

    reloc_info = Event.RELOC_INFO_TYPE(
        True,
        0.0,
        1.0,
        2.0,
        3.0,
        4.0,
        100,
        Event.PHASES_TYPE(0, 0, 1.0, 0.5, 2.0),
        Event.DD_TYPE(0, 1, 2, 3, 0.0, 1.0, 2.0, 3.0),
    )

    reloc_info_1 = Event.RELOC_INFO_TYPE(
        True,
        0.0,
        1.0,
        2.0,
        3.0,
        4.0,
        100,
        Event.PHASES_TYPE(1, 1, 2.0, 0.75, 3.0),
        Event.DD_TYPE(3, 2, 1, 0, 3.0, 2.0, 1.0, 0.0),
    )

    assert reloc_info_1.phases.stationDistMedian == 2.0
    assert reloc_info_1.dd.finalResidualMAD == 0.0

    assert reloc_info.isRelocated
    assert reloc_info.startRms == 0.0
    assert reloc_info.finalRms == 1.0
    assert reloc_info.locChange == 2.0
    assert reloc_info.depthChange == 3.0
    assert reloc_info.timeChange == 4.0
    assert reloc_info.numNeighbours == 100
    assert reloc_info.phases.stationDistMedian == 1.0
    assert reloc_info.dd.finalResidualMAD == 3.0

    reloc_info.phases.stationDistMedian = 3.0
    reloc_info.dd.finalResidualMAD = 4.0

    assert reloc_info.phases.stationDistMedian == 3.0
    assert reloc_info.dd.finalResidualMAD == 4.0

    assert reloc_info_1.phases.stationDistMedian == 2.0
    assert reloc_info_1.dd.finalResidualMAD == 0.0


def test_event():

    e = Event(
        0,
        UTCClock.fromString("2022-02-10T17:58:00.000Z"),
        0.0,
        90.0,
        10.0,
        5.5,
        Event.RELOC_INFO_TYPE(
            True,
            0.0,
            1.0,
            2.0,
            3.0,
            4.0,
            100,
            Event.PHASES_TYPE(0, 0, 1.0, 0.5, 2.0),
            Event.DD_TYPE(0, 1, 2, 3, 0.0, 1.0, 2.0, 3.0),
        ),
    )

    assert e.id == 0
    assert e.time == datetime.timedelta(19033, 0, 0, 0, 58, 17)
    assert e.latitude == 0.0
    assert e.longitude == 90.0
    assert e.depth == 10.0
    assert e.magnitude == 5.5

    assert e.relocInfo.dd.numCCs == 3
    e.relocInfo.dd.numCCs = 2
    assert e.relocInfo.dd.numCCs == 2


def test_catalog():

    c = Catalog(station_file, event_file, phase_file, False)

    st_test = c.getStations()["NET.ST08."]
    ev_test = c.getEvents()[11]
    (ph_test,) = filter(
        lambda x: x.time == UTCClock.fromString("2041-06-14T23:45:10.733093Z"),
        c.getPhases()[24],
    )

    assert st_test == Station(
        "NET.ST08.", 47.095355, 8.359807, 0.0, "NET", "ST08", ""
    )

    assert ev_test.latitude == 47.000531
    assert ev_test.longitude == 8.459671
    assert ev_test.magnitude == 1.00
    assert ev_test.depth == 6.6365
    assert ev_test.time == UTCClock.fromString("2041-06-14T23:46:05.010713Z")

    assert ph_test.time == UTCClock.fromString("2041-06-14T23:45:10.733093Z")
    assert ph_test.type == "P"
    assert ph_test.lowerUncertainty == 0.0
    assert ph_test.upperUncertainty == 0.0
    assert ph_test.networkCode == "NET"
    assert ph_test.stationCode == "ST02"
    assert ph_test.isManual


def test_obspy_waveform_proxy():

    tr0 = obspy.Trace(
        np.linspace(0, 1, 101),
        {"network": "XX", "station": "YY", "channel": "Z", "location": "0"},
    )

    tr1 = obspy.Trace(
        np.linspace(1, 2, 101),
        {"network": "XX", "station": "YY", "channel": "Y", "location": "1"},
    )

    p = ObspyWaveformProxy(obspy.Stream([tr0, tr1]))

    assert p._getTraceAddr("XX", "YY", "0", "Z") == hex(tr0.data.ctypes.data)
    assert p._getTraceAddr("XX", "YY", "1", "Y") == hex(tr1.data.ctypes.data)
    np.testing.assert_allclose(
        p.getTraceData("XX", "YY", "0", "Z"), np.linspace(0, 1, 101)
    )
    np.testing.assert_allclose(
        p.getTraceData("XX", "YY", "1", "Y"), np.linspace(1, 2, 101)
    )


def test_dd():

    con = Config()
    cat = Catalog(station_file, event_file, phase_file, False)
    ttt = ConstantVelocity(5.8, 3.36)
    # prx = ObspyWaveformProxy(obspy.Stream([]))

    dd = DD(cat, con, ttt, NoWaveformProxy())

    cluster_cfg = ClusteringOptions()
    cluster_cfg.numEllipsoids = 0
    cluster_cfg.maxEllipsoidSize = 15
    cluster_cfg.xcorrMaxEvStaDist = 0
    cluster_cfg.xcorrMaxInterEvDist = 0
    cluster_cfg.xcorrDetectMissingPhases = False

    solver_cfg = SolverOptions()
    solver_cfg.algoIterations = 20
    solver_cfg.absLocConstraintStart = 0.3
    solver_cfg.absLocConstraintEnd = 0.3
    solver_cfg.dampingFactorStart = 0.01
    solver_cfg.dampingFactorEnd = 0.01
    solver_cfg.downWeightingByResidualStart = 0
    solver_cfg.downWeightingByResidualEnd = 0
    solver_cfg.airQuakes.action = SolverOptions.AQ_ACTION.RESET_DEPTH

    cat_new = dd.relocateMultiEvents(cluster_cfg, solver_cfg)

    event_file_true = str(DATA_DIR / "relocated-event.csv")
    phase_file_true = str(DATA_DIR / "relocated-phase.csv")
    station_file_true = str(DATA_DIR / "relocated-station.csv")

    cat_true = Catalog(
        station_file_true, event_file_true, phase_file_true, False
    )

    for en, eo in zip(
        cat_new.getEvents().values(), cat_true.getEvents().values()
    ):
        np.testing.assert_allclose(en.latitude, eo.latitude, rtol=1e-5)
        np.testing.assert_allclose(en.longitude, eo.longitude, rtol=1e-5)
        np.testing.assert_allclose(en.depth, eo.depth, rtol=1e-5)
        np.testing.assert_allclose(en.magnitude, eo.magnitude, rtol=1e-5)
        # assert vn == vo
