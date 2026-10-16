import pytest
from semantic_robot.channel import ChannelConfig,SimulatedChannel

def test_seeded():
    cfg=ChannelConfig(bandwidth_mbps=2,loss=.23,seed=11)
    a,b=SimulatedChannel(cfg),SimulatedChannel(cfg)
    assert [a.send(i,240,i/8) for i in range(20)]==[b.send(i,240,i/8) for i in range(20)]

def test_byte_rate():
    cfg=ChannelConfig(loss=0,jitter_ms=0,propagation_ms=0)
    a,b=SimulatedChannel(cfg),SimulatedChannel(cfg)
    assert a.send(0,100000,0).delivered_at>b.send(0,100,0).delivered_at

def test_forced_loss():
    tx=SimulatedChannel(ChannelConfig(loss=1)).send(0,20,0)
    assert tx.delivered_at is None and tx.reason=='channel_loss'

def test_overflow():
    c=SimulatedChannel(ChannelConfig(bandwidth_mbps=.1,loss=0,max_queue_ms=10))
    c.send(0,100000,0)
    assert c.send(1,100000,.1).reason=='queue_overflow'

def test_bad_bandwidth():
    with pytest.raises(ValueError):ChannelConfig(bandwidth_mbps=0)

def test_bad_loss():
    with pytest.raises(ValueError):ChannelConfig(loss=1.1)
