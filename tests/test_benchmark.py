import json,pytest
from semantic_robot.benchmark import BenchmarkConfig,benchmark,evaluate
from semantic_robot.channel import ChannelConfig
from semantic_robot.types import METHODS

def test_four_baselines(tmp_path):
    cfg=BenchmarkConfig(frames=16,channel=ChannelConfig(loss=0))
    results,records=benchmark(cfg,tmp_path)
    assert [x['method'] for x in results]==list(METHODS)
    assert len(records)==64
    assert json.loads((tmp_path/'summary.json').read_text())['synthetic_only']
    assert (tmp_path/'frame_metrics.csv').exists()

def test_savings():
    s,_=benchmark(BenchmarkConfig(frames=24))
    amount={r['method']:r['bytes_sent'] for r in s}
    assert amount['adaptive']<amount['fixed']<amount['roi']<amount['raw']

def test_decisions():
    s,rows=evaluate('adaptive',BenchmarkConfig(frames=21),adaptive_link=True)
    assert s['frames']==21
    assert all(r['decision'] in ('GO','SEARCH','STOP','PICKUP') for r in rows)

def test_invalid_frames():
    with pytest.raises(ValueError):BenchmarkConfig(frames=0)
