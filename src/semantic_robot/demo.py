"""Generate preview of synthetic scene; not a real robot capture."""
from pathlib import Path
import cv2
from .warehouse import make_scene
from .vision import ColorDetector
from .decision import decide
from .types import Observation

def draw_demo(out='docs/assets/warehouse_demo.png',frame=30):
    s=make_scene(frame,'navigation');image=s.image.copy()
    detected=ColorDetector().detect(image)
    for d in detected:
        cv2.rectangle(image,d.box[:2],d.box[2:],(20,20,20),2)
        cv2.putText(image,d.kind.name,(d.box[0],max(48,d.box[1]-6)),cv2.FONT_HERSHEY_SIMPLEX,.42,(19,25,35),1)
    cv2.putText(image,'TASK DECISION: '+decide(Observation(frame,'navigation',detected)),(150,347),cv2.FONT_HERSHEY_SIMPLEX,.47,(25,30,40),1)
    path=Path(out);path.parent.mkdir(exist_ok=True,parents=True)
    if not cv2.imwrite(str(path),image):raise RuntimeError('Unable to save preview')
    return path
if __name__=='__main__':print(draw_demo())
