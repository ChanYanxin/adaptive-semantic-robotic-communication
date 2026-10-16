import numpy as np
import pytest
from semantic_robot.warehouse import make_scene,task_for_frame
from semantic_robot.vision import ColorDetector
from semantic_robot.decision import decide,hazard_present
from semantic_robot.types import Observation

def test_deterministic_scene():
    a=make_scene(11);b=make_scene(11)
    assert np.array_equal(a.image,b.image) and a.truth==b.truth

def test_task_schedule():
    assert [task_for_frame(i) for i in (0,39,40,79,80)]==['navigation','navigation','transport','transport','navigation']

def test_invalid_task():
    with pytest.raises(ValueError):make_scene(0,'unknown')

def test_detector():
    d=ColorDetector().detect(make_scene(10).image)
    assert len(d)>=6 and {int(x.kind) for x in d}=={1,2,3,4,5}

def test_hazard_stop():
    s=make_scene(29)
    assert hazard_present(s.truth) and decide(s.truth)=='STOP'

def test_empty_transport_search():
    assert decide(Observation(0,'transport',()))=='SEARCH'
