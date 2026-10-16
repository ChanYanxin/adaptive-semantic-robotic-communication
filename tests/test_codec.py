import pytest
from semantic_robot.codec import encode,decode,budget_from_bandwidth
from semantic_robot.types import Observation,Kind
from semantic_robot.warehouse import make_scene
from semantic_robot.vision import ColorDetector
from semantic_robot.decision import decide

def sample():
    s=make_scene(30,'transport')
    return s.image,Observation(30,'transport',ColorDetector().detect(s.image))

@pytest.mark.parametrize('method',['raw','roi','fixed','adaptive'])
def test_roundtrip(method):
    img,obs=sample();p=encode(method,img,obs,budget=80)
    got=decode(p,ColorDetector())
    assert got.frame_id==obs.frame_id and got.task==obs.task and len(got.objects)>0

def test_budgets():
    img,obs=sample()
    for x in (28,45,80):assert len(encode('adaptive',img,obs,budget=x).data)<=x

def test_selection():
    img,obs=sample()
    a=decode(encode('adaptive',img,obs,80),ColorDetector())
    f=decode(encode('fixed',img,obs),ColorDetector())
    assert len(a.objects)<len(f.objects)

def test_order():
    img,obs=sample()
    size={m:len(encode(m,img,obs,80).data) for m in ('raw','roi','fixed','adaptive')}
    assert size['adaptive']<size['fixed']<size['roi']<size['raw']

def test_insufficient_budget():
    img,obs=sample()
    with pytest.raises(ValueError):encode('adaptive',img,obs,budget=3)

def test_bad_method():
    img,obs=sample()
    with pytest.raises(ValueError):encode('x',img,obs)

def test_link_policy():assert budget_from_bandwidth(.5)<budget_from_bandwidth(2)<budget_from_bandwidth(5)

def test_severe_prioritizes_hazards():
    s=make_scene(48,'transport');obs=Observation(48,'transport',ColorDetector().detect(s.image))
    low=decode(encode('adaptive',s.image,obs,28),ColorDetector())
    high=decode(encode('adaptive',s.image,obs,80),ColorDetector())
    assert len(low.objects)<len(high.objects)
    assert all(d.kind in (Kind.PERSON,Kind.OBSTACLE) for d in low.objects)
    assert decide(low)==decide(high)=='STOP'
