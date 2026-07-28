import math

import obspy
import obspy.core.event as ev
import pytest
from obspy.core.inventory import Channel, Inventory, Network, Station

from pyrtdd.hdd import (
    Catalog,
    Config,
    Homogeneous,
    DD,
    ClusteringOptions,
    SolverOptions,
    Logger,
)
from pyrtdd.obspy.catalog import catalog_from_obspy, catalog_to_obspy

Logger.setLevel(Logger.Level.warning)

T0 = obspy.UTCDateTime(2022, 2, 10, 17, 58, 0)


def _station(code, lat, lon, elev):
    chan = Channel(
        code="HHZ", location_code="", latitude=lat, longitude=lon,
        elevation=elev, depth=0.0,
    )
    return Station(code=code, latitude=lat, longitude=lon, elevation=elev, channels=[chan])


@pytest.fixture
def inventory():
    return Inventory(networks=[Network(code="NET", stations=[_station("STA1", 47.0, 8.0, 500.0)])])


def _pick(time, phase_hint="P", evaluation_mode="manual", station="STA1",
          network="NET", location="", channel="HHZ"):
    p = ev.Pick(
        time=time, phase_hint=phase_hint, evaluation_mode=evaluation_mode,
        waveform_id=ev.WaveformStreamID(
            network_code=network, station_code=station,
            location_code=location, channel_code=channel,
        ),
    )
    return p


def _event_with_one_pick(pick, weight=1.0, mag=2.5):
    arrival = ev.Arrival(pick_id=pick.resource_id, phase=pick.phase_hint, time_weight=weight)
    origin = ev.Origin(time=T0, latitude=47.1, longitude=8.1, depth=10000.0, arrivals=[arrival])
    magnitude = ev.Magnitude(mag=mag)
    return ev.Event(
        picks=[pick], origins=[origin], magnitudes=[magnitude],
        preferred_origin_id=origin.resource_id,
        preferred_magnitude_id=magnitude.resource_id,
    )


def test_catalog_from_obspy_basic(inventory):
    pick = _pick(T0 + 5.0)
    pick.time_errors.uncertainty = 0.05
    obspy_cat = ev.Catalog(events=[_event_with_one_pick(pick)])

    hdd_cat = catalog_from_obspy(obspy_cat, inventory)

    stations = hdd_cat.getStations()
    events = hdd_cat.getEvents()
    phases = hdd_cat.getPhases()

    assert "NET.STA1." in stations
    assert stations["NET.STA1."].latitude == 47.0

    (eid, event), = events.items()
    assert event.latitude == 47.1
    assert event.longitude == 8.1
    assert math.isclose(event.depth, 10.0)  # meters -> km
    assert event.magnitude == 2.5

    (phase,) = phases[eid]
    assert phase.type == "P"
    assert phase.stationId == "NET.STA1."
    assert math.isclose(phase.lowerUncertainty, 0.05)
    assert math.isclose(phase.upperUncertainty, 0.05)


def test_catalog_from_obspy_asymmetric_uncertainty(inventory):
    pick = _pick(T0 + 5.0)
    pick.time_errors.lower_uncertainty = 0.01
    pick.time_errors.upper_uncertainty = 0.03
    obspy_cat = ev.Catalog(events=[_event_with_one_pick(pick)])

    hdd_cat = catalog_from_obspy(obspy_cat, inventory)
    (phase,) = next(iter(hdd_cat.getPhases().values()))
    assert math.isclose(phase.lowerUncertainty, 0.01)
    assert math.isclose(phase.upperUncertainty, 0.03)


def test_catalog_from_obspy_no_uncertainty_is_nan(inventory):
    pick = _pick(T0 + 5.0)
    obspy_cat = ev.Catalog(events=[_event_with_one_pick(pick)])

    hdd_cat = catalog_from_obspy(obspy_cat, inventory)
    (phase,) = next(iter(hdd_cat.getPhases().values()))
    assert math.isnan(phase.lowerUncertainty)
    assert math.isnan(phase.upperUncertainty)


def test_catalog_from_obspy_missing_magnitude_is_nan(inventory):
    pick = _pick(T0 + 5.0)
    arrival = ev.Arrival(pick_id=pick.resource_id, phase="P", time_weight=1.0)
    origin = ev.Origin(time=T0, latitude=47.1, longitude=8.1, depth=10000.0, arrivals=[arrival])
    event = ev.Event(picks=[pick], origins=[origin], preferred_origin_id=origin.resource_id)
    obspy_cat = ev.Catalog(events=[event])

    hdd_cat = catalog_from_obspy(obspy_cat, inventory)
    (event_out,) = hdd_cat.getEvents().values()
    assert math.isnan(event_out.magnitude)


def test_catalog_from_obspy_skips_event_without_arrivals(inventory):
    origin = ev.Origin(time=T0, latitude=47.1, longitude=8.1, depth=10000.0, arrivals=[])
    event = ev.Event(origins=[origin], preferred_origin_id=origin.resource_id)
    obspy_cat = ev.Catalog(events=[event])

    hdd_cat = catalog_from_obspy(obspy_cat, inventory)
    assert len(hdd_cat.getEvents()) == 0


def test_catalog_from_obspy_skips_event_without_depth(inventory):
    pick = _pick(T0 + 5.0)
    arrival = ev.Arrival(pick_id=pick.resource_id, phase="P", time_weight=1.0)
    origin = ev.Origin(time=T0, latitude=47.1, longitude=8.1, arrivals=[arrival])  # no depth
    event = ev.Event(picks=[pick], origins=[origin], preferred_origin_id=origin.resource_id)
    obspy_cat = ev.Catalog(events=[event])

    hdd_cat = catalog_from_obspy(obspy_cat, inventory)
    assert len(hdd_cat.getEvents()) == 0


def test_catalog_from_obspy_skips_phase_with_unresolvable_station(inventory):
    pick = _pick(T0 + 5.0, station="UNKNOWN")
    obspy_cat = ev.Catalog(events=[_event_with_one_pick(pick)])

    hdd_cat = catalog_from_obspy(obspy_cat, inventory)
    # the event is still created, just without the unresolvable phase
    assert len(hdd_cat.getEvents()) == 1
    (eid,) = hdd_cat.getEvents().keys()
    assert hdd_cat.getPhases().get(eid, []) == []
    assert len(hdd_cat.getStations()) == 0


def test_catalog_from_obspy_discard_unused_automatic_picks(inventory):
    pick = _pick(T0 + 5.0, evaluation_mode="automatic")
    obspy_cat = ev.Catalog(events=[_event_with_one_pick(pick, weight=0.0)])

    kept = catalog_from_obspy(obspy_cat, inventory, discard_unused_automatic_picks=False)
    assert len(next(iter(kept.getPhases().values()))) == 1

    discarded = catalog_from_obspy(obspy_cat, inventory, discard_unused_automatic_picks=True)
    (eid,) = discarded.getEvents().keys()
    assert discarded.getPhases().get(eid, []) == []


def test_catalog_from_obspy_manual_pick_always_kept_regardless_of_weight(inventory):
    pick = _pick(T0 + 5.0, evaluation_mode="manual")
    obspy_cat = ev.Catalog(events=[_event_with_one_pick(pick, weight=0.0)])

    hdd_cat = catalog_from_obspy(obspy_cat, inventory, discard_unused_automatic_picks=True)
    assert len(next(iter(hdd_cat.getPhases().values()))) == 1


def test_catalog_to_obspy_basic(inventory):
    pick = _pick(T0 + 5.0)
    pick.time_errors.uncertainty = 0.05
    obspy_cat = ev.Catalog(events=[_event_with_one_pick(pick)])
    hdd_cat = catalog_from_obspy(obspy_cat, inventory)

    roundtripped = catalog_to_obspy(hdd_cat)

    assert len(roundtripped) == 1
    origin = roundtripped[0].preferred_origin()
    assert origin.latitude == 47.1
    assert origin.longitude == 8.1
    assert origin.depth == 10000.0  # km -> meters
    assert len(origin.arrivals) == 1
    assert len(roundtripped[0].picks) == 1
    assert roundtripped[0].preferred_magnitude().mag == 2.5


def test_catalog_to_obspy_no_magnitude_when_nan(inventory):
    pick = _pick(T0 + 5.0)
    arrival = ev.Arrival(pick_id=pick.resource_id, phase="P", time_weight=1.0)
    origin = ev.Origin(time=T0, latitude=47.1, longitude=8.1, depth=10000.0, arrivals=[arrival])
    event = ev.Event(picks=[pick], origins=[origin], preferred_origin_id=origin.resource_id)
    hdd_cat = catalog_from_obspy(ev.Catalog(events=[event]), inventory)

    roundtripped = catalog_to_obspy(hdd_cat)
    assert roundtripped[0].preferred_magnitude() is None


def test_catalog_round_trip_through_relocation():
    stations_meta = [("STA%d" % i, 47.0 + 0.01 * i, 8.0 + 0.01 * i, 500.0) for i in range(5)]
    inv = Inventory(networks=[Network(
        code="NET", stations=[_station(*s) for s in stations_meta],
    )])

    events = []
    for i in range(6):
        org_time = T0 + i * 60
        picks, arrivals = [], []
        for code, lat, lon, elev in stations_meta:
            p = _pick(org_time + 3.0 + 0.01 * i, station=code)
            p.time_errors.uncertainty = 0.02
            picks.append(p)
            arrivals.append(ev.Arrival(pick_id=p.resource_id, phase="P", time_weight=1.0))
        origin = ev.Origin(
            time=org_time, latitude=47.05 + 0.001 * i, longitude=8.05 + 0.001 * i,
            depth=8000.0 + 100 * i, arrivals=arrivals,
        )
        magnitude = ev.Magnitude(mag=1.0 + 0.1 * i)
        events.append(ev.Event(
            picks=picks, origins=[origin], magnitudes=[magnitude],
            preferred_origin_id=origin.resource_id,
            preferred_magnitude_id=magnitude.resource_id,
        ))

    hdd_cat = catalog_from_obspy(ev.Catalog(events=events), inv)
    assert len(hdd_cat.getStations()) == 5
    assert len(hdd_cat.getEvents()) == 6

    cfg = Config()
    dd = DD(hdd_cat, cfg, Homogeneous(5.8, 3.36))

    cluster_cfg = ClusteringOptions()
    cluster_cfg.numEllipsoids = 0
    cluster_cfg.maxNeighbourDist = 50
    cluster_cfg.minNumNeigh = 2
    cluster_cfg.minNumPhases = 2

    solver_cfg = SolverOptions()
    solver_cfg.algoIterations = 5

    clusters = dd.findClusters(cluster_cfg)
    cat_new = dd.relocateMultiEvents(clusters, solver_cfg)
    assert len(cat_new.getEvents()) == 6

    roundtripped = catalog_to_obspy(cat_new)
    assert len(roundtripped) == 6

    relocated_arrivals = sum(
        1
        for e in roundtripped
        for arr in e.preferred_origin().arrivals
        if arr.time_weight
    )
    assert relocated_arrivals > 0
