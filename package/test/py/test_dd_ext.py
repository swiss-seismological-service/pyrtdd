from scrtdd.hdd import Config, Catalog

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
