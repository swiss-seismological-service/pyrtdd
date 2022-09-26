from scrtdd.hdd import Config, Catalog, ConstantVelocity, UTCClock
import datetime

Event = Catalog.Event
Station = Catalog.Station
PhaseType = Catalog.Phase.Type


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

    assert UTCClock.fromString("1970-01-01T00:00:00.000Z") == datetime.timedelta(0)
    assert UTCClock.fromString("1970-01-01T01:00:00.000Z") == datetime.timedelta(0, 0, 0, 0, 0, 1)
    assert UTCClock.fromString("1980-01-01T01:00:00.000Z") == datetime.timedelta(3652, 0, 0, 0, 0, 1)

def test_event():
    
    phases = Event.PHASES_TYPE(0, 0, +1.0, +0.5, +2.0)