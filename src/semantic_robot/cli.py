"""Command-line paired benchmark runner."""
import argparse,json
from .benchmark import BenchmarkConfig,benchmark
from .channel import ChannelConfig

def main():
    p=argparse.ArgumentParser(description='Synthetic warehouse task-aware semantic communication')
    sub=p.add_subparsers(dest='command',required=True)
    b=sub.add_parser('benchmark')
    b.add_argument('--frames',type=int,default=160)
    b.add_argument('--fps',type=int,default=8)
    b.add_argument('--bandwidth',type=float,default=4.)
    b.add_argument('--loss',type=float,default=.01)
    b.add_argument('--variable-link',action='store_true')
    b.add_argument('--out',default='results/default')
    b.add_argument('--plots',action='store_true')
    args=p.parse_args()
    if args.command=='benchmark':
        cfg=BenchmarkConfig(frames=args.frames,fps=args.fps,channel=ChannelConfig(bandwidth_mbps=args.bandwidth,loss=args.loss))
        summary,_=benchmark(cfg,args.out,args.variable_link)
        if args.plots:
            from .plots import save_plots
            save_plots(summary,args.out)
        print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
