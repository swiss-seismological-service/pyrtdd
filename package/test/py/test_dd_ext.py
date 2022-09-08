import pytest

from scrtdd.hdd import Config

def test_config_defaults():
    
    c = Config()
    assert c.validPphases == ["Pg", "P", "Px"]
    assert c.validSphases == ["Sg", "S", "Sx"]
    assert c.compatibleChannels == []
    assert c.diskTraceMinLen == 10