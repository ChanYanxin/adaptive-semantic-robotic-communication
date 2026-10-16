"""Task-oriented application codecs; no wireless PHY or learned semantic model."""
from dataclasses import dataclass
import struct
import cv2
import msgpack
import numpy as np
from .types import Detection,Kind,Observation,METHODS
from .decision import relevant,CORRIDOR

QSTEP=2
@dataclass(frozen=True)
class Packet:
    method:str
    data:bytes
    frame_id:int
    task:str
    sent_objects:int

def roi_for(task:str):return (115,110,525,343) if task=="transport" else (125,110,520,343)

def _jpeg(img,quality):
    good,array=cv2.imencode('.jpg',img,[cv2.IMWRITE_JPEG_QUALITY,quality])
    if not good:raise RuntimeError("JPEG encoder error")
    return array.tobytes()

def _pack_semantic(obs,objects,quantized):
    step=QSTEP if quantized else 1
    records=[[int(d.kind),*[int(round(c/step)) for c in d.box],min(255,max(0,int(round(d.confidence*255))))] for d in objects]
    return msgpack.packb([1,obs.frame_id,0 if obs.task=="navigation" else 1,step,records],use_bin_type=True)

def budget_from_bandwidth(mbps:float)->int:
    return 28 if mbps<1 else 45 if mbps<3 else 80

def _sort_key(d,task):
    if d.kind in (Kind.PERSON,Kind.OBSTACLE) and relevant(d,task):return 0,abs(d.cx-323)
    if d.kind==Kind.PACKAGE and relevant(d,task):return 1,abs(d.cx-400)
    return 2,d.cx

def encode(method:str,image:np.ndarray,obs:Observation,budget=80,jpeg_quality=75)->Packet:
    if method not in METHODS:raise ValueError(method)
    if method=="raw":return Packet(method,_jpeg(image,jpeg_quality),obs.frame_id,obs.task,0)
    if method=="roi":
        x1,y1,x2,y2=roi_for(obs.task)
        return Packet(method,struct.pack('!HH',x1,y1)+_jpeg(image[y1:y2,x1:x2],jpeg_quality),obs.frame_id,obs.task,0)
    if method=="fixed":
        return Packet(method,_pack_semantic(obs,obs.objects,False),obs.frame_id,obs.task,len(obs.objects))
    selected=[]
    if len(_pack_semantic(obs,[],True))>budget:raise ValueError("Insufficient payload budget")
    for obj in sorted([d for d in obs.objects if relevant(d,obs.task)],key=lambda d:_sort_key(d,obs.task)):
        if len(_pack_semantic(obs,selected+[obj],True))<=budget:selected.append(obj)
    return Packet(method,_pack_semantic(obs,selected,True),obs.frame_id,obs.task,len(selected))

def decode(packet:Packet,detector,image_shape=(360,640))->Observation:
    if packet.method in ('raw','roi'):
        offset=(0,0);payload=packet.data
        if packet.method=='roi':
            offset=struct.unpack('!HH',payload[:4]);payload=payload[4:]
        img=cv2.imdecode(np.frombuffer(payload,dtype=np.uint8),cv2.IMREAD_COLOR)
        if img is None:raise ValueError('Invalid JPEG')
        objects=[]
        for d in detector.detect(img):
            x1,y1,x2,y2=d.box;ox,oy=offset
            objects.append(Detection(d.kind,(x1+ox,y1+oy,x2+ox,y2+oy),d.confidence))
        return Observation(packet.frame_id,packet.task,tuple(objects),image_shape[1],image_shape[0])
    obj=msgpack.unpackb(packet.data,raw=False)
    if not isinstance(obj,list) or len(obj)!=5 or obj[0]!=1 or obj[3] not in (1,QSTEP):raise ValueError('Invalid semantic schema')
    version,frame,bit,step,records=obj
    if bit not in (0,1) or frame<0:raise ValueError('Invalid frame metadata')
    objects=[]
    for rec in records:
        if not isinstance(rec,list) or len(rec)!=6:raise ValueError('Invalid semantic record')
        box=tuple(int(v*step) for v in rec[1:5])
        if any(x<0 for x in box):raise ValueError('Negative coordinate')
        objects.append(Detection(Kind(rec[0]),box,rec[5]/255))
    return Observation(frame,'navigation' if bit==0 else 'transport',tuple(objects),image_shape[1],image_shape[0])
