"""Abstract deterministic FIFO bandwidth and packet-loss simulator, NOT 6G PHY."""
from dataclasses import dataclass
import random

@dataclass(frozen=True)
class ChannelConfig:
    bandwidth_mbps:float=4.0
    propagation_ms:float=15.0
    jitter_ms:float=4.0
    loss:float=.01
    max_queue_ms:float=300.0
    seed:int=17
    def __post_init__(self):
        if self.bandwidth_mbps<=0 or self.propagation_ms<0 or self.jitter_ms<0 or not 0<=self.loss<=1 or self.max_queue_ms<0:
            raise ValueError('Invalid simulated channel parameters')

@dataclass(frozen=True)
class SendResult:
    delivered_at:float|None
    reason:str
    serialization_ms:float
    queue_ms:float

class SimulatedChannel:
    def __init__(self,config:ChannelConfig):
        self.config=config
        self.busy_until=0.0
        self.rng=random.Random(config.seed)
    def send(self,frame_index:int,size:int,ready_at:float,bandwidth_mbps:float|None=None,loss:float|None=None)->SendResult:
        if size<0:raise ValueError('Negative packet size')
        bw=self.config.bandwidth_mbps if bandwidth_mbps is None else bandwidth_mbps
        p=self.config.loss if loss is None else loss
        if bw<=0 or not 0<=p<=1:raise ValueError('Invalid rate or loss')
        lost=self.rng.random()<p
        jitter=self.rng.uniform(-self.config.jitter_ms,self.config.jitter_ms)
        queue_s=max(0,self.busy_until-ready_at)
        transmission_s=size*8/(bw*1_000_000)
        if queue_s*1000>self.config.max_queue_ms:
            return SendResult(None,'queue_overflow',transmission_s*1000,queue_s*1000)
        finished=max(ready_at,self.busy_until)+transmission_s
        self.busy_until=finished
        if lost:return SendResult(None,'channel_loss',transmission_s*1000,queue_s*1000)
        return SendResult(finished+max(0,self.config.propagation_ms+jitter)/1000,'delivered',transmission_s*1000,queue_s*1000)
