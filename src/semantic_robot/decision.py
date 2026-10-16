"""Toy safety decision; NOT a real safety controller."""
from .types import Kind,Observation
CORRIDOR=(145,138,502,335)
PICKUP_ZONE=(325,165,495,242)
HAZARDS=frozenset((Kind.PERSON,Kind.OBSTACLE))

def _inside(d,zone)->bool:
    x1,y1,x2,y2=zone
    return x1<=d.cx<=x2 and y1<=d.cy<=y2

def hazard_present(obs:Observation)->bool:
    return any(d.kind in HAZARDS and _inside(d,CORRIDOR) for d in obs.objects)

def relevant(d,task:str)->bool:
    return (d.kind in HAZARDS and _inside(d,CORRIDOR)) or (task=="transport" and d.kind==Kind.PACKAGE and _inside(d,PICKUP_ZONE))

def decide(obs:Observation)->str:
    if hazard_present(obs):return "STOP"
    if obs.task=="transport":
        return "PICKUP" if any(d.kind==Kind.PACKAGE and _inside(d,PICKUP_ZONE) for d in obs.objects) else "SEARCH"
    return "GO"
