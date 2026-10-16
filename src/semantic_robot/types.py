from dataclasses import dataclass
from enum import IntEnum

class Kind(IntEnum):
    PERSON = 1
    OBSTACLE = 2
    PACKAGE = 3
    PALLET = 4
    ROBOT = 5

@dataclass(frozen=True)
class Detection:
    kind: Kind
    box: tuple[int,int,int,int]
    confidence: float = 1.0
    @property
    def cx(self) -> float:
        return (self.box[0]+self.box[2])/2
    @property
    def cy(self) -> float:
        return (self.box[1]+self.box[3])/2

@dataclass(frozen=True)
class Observation:
    frame_id: int
    task: str
    objects: tuple[Detection,...]
    width: int=640
    height: int=360

METHODS=("raw","roi","fixed","adaptive")
