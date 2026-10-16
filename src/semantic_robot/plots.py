"""Optional benchmark visualization. Not used for numeric claims."""
from pathlib import Path

def save_plots(results,output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    names=[r['method'] for r in results]
    metrics=[('traffic.png','Transmitted application bytes','Kilobytes',[r['bytes_sent']/1000 for r in results]),
             ('task_quality.png','Toy task decision accuracy','Percent',[r['task_decision_accuracy']*100 for r in results]),
             ('hazard_recall.png','Hazard observations before decision deadline','Percent',[(r['hazard_observation_recall'] or 0)*100 for r in results]),
             ('fresh_delivery.png','Fresh observations at decision time','Percent',[r['fresh_observation_ratio']*100 for r in results])]
    for filename,title,ylabel,values in metrics:
        fig,ax=plt.subplots(figsize=(7.3,3.8))
        bars=ax.bar(names,values)
        ax.set(title=title,ylabel=ylabel);ax.set_ylim(bottom=0)
        for b,v in zip(bars,values):ax.annotate(f'{v:.1f}',(b.get_x()+b.get_width()/2,v),ha='center',va='bottom',fontsize=9)
        fig.tight_layout();fig.savefig(out/filename,dpi=130);plt.close(fig)
