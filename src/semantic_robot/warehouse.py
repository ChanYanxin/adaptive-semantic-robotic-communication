"""Deterministic synthetic warehouse scenes. Objects are artificial rectangles."""
from dataclasses import dataclass
import cv2
import numpy as np
from .types import Detection,Kind,Observation

WIDTH,HEIGHT=640,360
COLORS={Kind.PERSON:(68,60,232),Kind.OBSTACLE:(64,125,240),Kind.PACKAGE:(83,174,55),Kind.PALLET:(210,123,64),Kind.ROBOT:(185,68,175)}

@dataclass(frozen=True)
class Scene:
    image: np.ndarray
    truth: Observation

def task_for_frame(frame_id:int,interval:int=40)->str:
    return "navigation" if (frame_id//interval)%2==0 else "transport"

def make_scene(frame_id:int,task:str="navigation",seed:int=7)->Scene:
    if task not in ("navigation","transport") or frame_id<0:
        raise ValueError("Invalid task or frame number")
    rng=np.random.default_rng(seed)
    noise=rng.integers(0,10,size=(HEIGHT,WIDTH,1),dtype=np.uint8)
    img=np.clip(np.repeat(noise,3,axis=2).astype(np.int16)+np.array([209,215,219]),0,255).astype(np.uint8)
    cv2.rectangle(img,(0,44),(WIDTH-1,76),(149,154,159),-1)
    for x in (14,113,508,613):cv2.rectangle(img,(x,75),(x+9,328),(126,132,137),-1)
    for y in (136,225,318):cv2.line(img,(16,y),(624,y),(180,186,189),2)
    cv2.rectangle(img,(145,138),(502,335),(226,230,232),2)
    px=58+(frame_id*5)%535
    py=165+int(26*np.sin(frame_id/14.0))
    ox=160+int(135*(1+np.sin(frame_id/24.0)))
    bx=420-int(100*np.sin(frame_id/31.0))
    objects=[Detection(Kind.PERSON,(px,py,px+24,py+52)),
             Detection(Kind.PACKAGE,(bx,183,bx+42,216)),
             Detection(Kind.PACKAGE,(66,85,103,116)),
             Detection(Kind.PALLET,(550,235,603,268)),
             Detection(Kind.PALLET,(535,99,583,128)),
             Detection(Kind.ROBOT,(44,272,97,310))]
    if 8<=frame_id%40<20:objects.append(Detection(Kind.OBSTACLE,(ox,255,ox+54,294)))
    obs=Observation(frame_id,task,tuple(objects))
    for d in obs.objects:
        cv2.rectangle(img,d.box[:2],d.box[2:],COLORS[d.kind],-1)
        cv2.rectangle(img,d.box[:2],d.box[2:],(40,42,47),1)
    cv2.rectangle(img,(0,0),(WIDTH,42),(35,40,46),-1)
    cv2.putText(img,f"SYNTHETIC WAREHOUSE  |  frame {frame_id:03d}  |  {task.upper()}",(15,27),cv2.FONT_HERSHEY_SIMPLEX,.55,(248,249,250),1,cv2.LINE_AA)
    return Scene(img,obs)
