"""Toy color segmentation baseline and optional real YOLO interface."""
import cv2
import numpy as np
from .types import Kind,Detection
from .warehouse import COLORS

class ColorDetector:
    def detect(self,image:np.ndarray)->tuple[Detection,...]:
        output=[]
        for kind,color in COLORS.items():
            low=np.maximum(np.array(color,dtype=np.int16)-14,0).astype(np.uint8)
            high=np.minimum(np.array(color,dtype=np.int16)+14,255).astype(np.uint8)
            mask=cv2.inRange(image,low,high)
            n,_,stats,_=cv2.connectedComponentsWithStats(mask,8)
            for i in range(1,n):
                x,y,w,h,pixels=[int(z) for z in stats[i]]
                if pixels>=75 and w>=6 and h>=6:
                    output.append(Detection(kind,(x,y,x+w,y+h),.99))
        return tuple(sorted(output,key=lambda d:(int(d.kind),d.box[0],d.box[1])))

class YoloDetector:
    """Optional COCO adapter. Package/pallet categories need custom training."""
    COCO_MAP={"person":Kind.PERSON,"backpack":Kind.PACKAGE,"suitcase":Kind.PACKAGE,"handbag":Kind.PACKAGE,"chair":Kind.OBSTACLE,"car":Kind.OBSTACLE,"truck":Kind.OBSTACLE}
    def __init__(self,weights="yolov8n.pt",conf=.3):
        try:from ultralytics import YOLO
        except ImportError as e:raise RuntimeError("Install optional extra: pip install -e '.[yolo]'") from e
        self.model=YOLO(weights)
        self.conf=conf
    def detect(self,image):
        result=self.model.predict(image,conf=self.conf,verbose=False)[0]
        out=[]
        for box in result.boxes:
            kind=self.COCO_MAP.get(self.model.names[int(box.cls[0])])
            if kind is not None:out.append(Detection(kind,tuple(int(z) for z in box.xyxy[0].tolist()),float(box.conf[0])))
        return tuple(out)
