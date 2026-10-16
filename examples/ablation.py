"""Compute source-encoding byte ablation; no wireless metrics."""
from statistics import mean
import json
from semantic_robot.codec import _pack_semantic,encode
from semantic_robot.decision import relevant
from semantic_robot.types import Observation
from semantic_robot.vision import ColorDetector
from semantic_robot.warehouse import make_scene,task_for_frame

def run(frames=160):
    buckets={k:[] for k in ('all_full_precision','all_quantized','task_only','task_plus_quantization','adaptive_budgeted')}
    detector=ColorDetector()
    for i in range(frames):
        scene=make_scene(i,task_for_frame(i))
        obs=Observation(i,scene.truth.task,detector.detect(scene.image))
        selected=[d for d in obs.objects if relevant(d,obs.task)]
        sizes={
            'all_full_precision':len(_pack_semantic(obs,obs.objects,False)),
            'all_quantized':len(_pack_semantic(obs,obs.objects,True)),
            'task_only':len(_pack_semantic(obs,selected,False)),
            'task_plus_quantization':len(_pack_semantic(obs,selected,True)),
            'adaptive_budgeted':len(encode('adaptive',scene.image,obs,budget=80).data)}
        for key in sizes:buckets[key].append(sizes[key])
    return {key:round(mean(val),2) for key,val in buckets.items()}
if __name__=='__main__':print(json.dumps(run(),indent=2))
