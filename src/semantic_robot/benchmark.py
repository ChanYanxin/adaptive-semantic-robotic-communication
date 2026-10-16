"""Paired synthetic benchmark: decision quality vs transmitted bytes and latency.

Toy decision accuracy is NOT real robot task success or object detection mAP.
"""
from dataclasses import dataclass,asdict
from statistics import mean
from pathlib import Path
import csv,json,time
from .channel import ChannelConfig,SimulatedChannel
from .codec import encode,decode,budget_from_bandwidth
from .decision import decide,hazard_present,relevant
from .types import METHODS,Observation
from .vision import ColorDetector
from .warehouse import make_scene,task_for_frame

@dataclass(frozen=True)
class BenchmarkConfig:
    frames:int=160
    fps:int=8
    deadline_ms:float=200
    max_staleness_ms:float=280
    seed:int=7
    channel:ChannelConfig=ChannelConfig()
    def __post_init__(self):
        if self.frames<1 or self.fps<1 or self.deadline_ms<=0 or self.max_staleness_ms<0:raise ValueError('Invalid benchmark settings')

def link_state(index:int,config:ChannelConfig,variable_link:bool)->tuple[float,float]:
    if not variable_link:return config.bandwidth_mbps,config.loss
    phase=(index//20)%4
    return config.bandwidth_mbps*(1.,.65,.25,1.)[phase],min(1.,config.loss+(0.,.02,.07,0.)[phase])

def evaluate(method:str,cfg:BenchmarkConfig,adaptive_link:bool=False):
    if method not in METHODS:raise ValueError(method)
    detector=ColorDetector();channel=SimulatedChannel(cfg.channel)
    latest=None;pending=[];rows=[];measured=[]
    for i in range(cfg.frames):
        task=task_for_frame(i);scene=make_scene(i,task,cfg.seed);now=i/cfg.fps
        bw,loss=link_state(i,cfg.channel,adaptive_link)
        start=time.perf_counter()
        sensed=detector.detect(scene.image) if method in ('fixed','adaptive') else ()
        packet=encode(method,scene.image,Observation(i,task,sensed),budget=budget_from_bandwidth(bw))
        cpu_client=(time.perf_counter()-start)*1000
        start=time.perf_counter();decoded=decode(packet,detector)
        cpu_edge=(time.perf_counter()-start)*1000
        measured.append(cpu_client+cpu_edge)
        tx=channel.send(i,len(packet.data),now+cpu_client/1000,bw,loss)
        completion=None if tx.delivered_at is None else tx.delivered_at+cpu_edge/1000
        if completion is not None:pending.append((completion,decoded,now))
        cutoff=now+cfg.deadline_ms/1000
        ready=[item for item in pending if item[0]<=cutoff]
        if ready:latest=max(ready,key=lambda p:(p[1].frame_id,p[0]))
        pending=[item for item in pending if item[0]>cutoff]
        valid=latest is not None and latest[1].task==task and 0<=cutoff-latest[2]<=cfg.max_staleness_ms/1000
        result=decide(latest[1]) if valid else 'STOP'  # conservative fallback, NOT detection
        truth=decide(scene.truth)
        fresh=valid and latest[1].frame_id==i
        had_hazard=hazard_present(scene.truth)
        hazard_seen=valid and hazard_present(latest[1])
        target=[d for d in scene.truth.objects if relevant(d,task)]
        perceived=decoded.objects if completion is not None else ()
        matched=sum(any(d.kind==g.kind and abs(d.cx-g.cx)<=8 and abs(d.cy-g.cy)<=8 for d in perceived) for g in target)
        rows.append({
            'frame':i,'task':task,'method':method,'bandwidth_mbps':round(bw,3),
            'loss_probability':round(loss,4),'payload_bytes':len(packet.data),
            'transmitted_bytes':0 if tx.reason=='queue_overflow' else len(packet.data),
            'sent_objects':packet.sent_objects,'network_status':tx.reason,
            'queue_ms':round(tx.queue_ms,3),'serialization_ms':round(tx.serialization_ms,3),
            'client_cpu_ms':round(cpu_client,3),'edge_cpu_ms':round(cpu_edge,3),
            'packet_completion_ms':round((completion-now)*1000,3) if completion is not None else None,
            'fresh':int(bool(fresh)),'used_frame':latest[1].frame_id if valid else -1,
            'ground_truth':truth,'decision':result,'hazard':int(had_hazard),
            'hazard_observed':int(bool(hazard_seen)),'relevant_count':len(target),
            'relevant_recalled':matched,'correct':int(result==truth),
            'hazard_recalled':int(not had_hazard or result=='STOP'),
            'unsafe_go':int(truth=='STOP' and result!='STOP'),
            'unnecessary_stop':int(truth!='STOP' and result=='STOP')
        })
    hazards=[r for r in rows if r['hazard']]
    total_objects=sum(r['relevant_count'] for r in rows)
    fresh_latency=[r['packet_completion_ms'] for r in rows if r['fresh'] and r['packet_completion_ms'] is not None]
    summary={
        'method':method,'frames':cfg.frames,'bytes_generated':sum(r['payload_bytes'] for r in rows),
        'bytes_sent':sum(r['transmitted_bytes'] for r in rows),'mean_payload_bytes':round(mean(r['payload_bytes'] for r in rows),2),
        'task_decision_accuracy':round(mean(r['correct'] for r in rows),4),
        'hazard_decision_recall':round(mean(r['hazard_recalled'] for r in hazards),4) if hazards else None,
        'hazard_observation_recall':round(mean(r['hazard_observed'] for r in hazards),4) if hazards else None,
        'relevant_object_recall_after_channel':round(sum(r['relevant_recalled'] for r in rows)/total_objects,4) if total_objects else None,
        'unsafe_go_frames':sum(r['unsafe_go'] for r in rows),
        'unnecessary_stop_frames':sum(r['unnecessary_stop'] for r in rows),
        'fresh_observation_ratio':round(mean(r['fresh'] for r in rows),4),
        'network_delivery_ratio':round(mean(r['network_status']=='delivered' for r in rows),4),
        'loss_drops':sum(r['network_status']=='channel_loss' for r in rows),
        'queue_drops':sum(r['network_status']=='queue_overflow' for r in rows),
        'mean_cpu_ms':round(mean(measured),3),
        'mean_fresh_packet_latency_ms':round(mean(fresh_latency),3) if fresh_latency else None}
    return summary,rows

def benchmark(cfg:BenchmarkConfig,output:str|Path|None=None,adaptive_link:bool=False):
    summaries=[];records=[]
    for method in METHODS:
        summary,rows=evaluate(method,cfg,adaptive_link)
        summaries.append(summary);records+=rows
    if output is not None:
        target=Path(output);target.mkdir(parents=True,exist_ok=True)
        with (target/'summary.json').open('w') as f:
            json.dump({'setting':asdict(cfg),'variable_link':adaptive_link,'synthetic_only':True,'results':summaries},f,indent=2)
        with (target/'frame_metrics.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    return summaries,records
