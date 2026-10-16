# Reproduce the four-mode comparisons

```bash
semantic-robot benchmark --frames 160 --fps 8 --bandwidth 4 --loss 0.01 --out results/default --plots
semantic-robot benchmark --frames 160 --fps 8 --bandwidth 4 --loss 0.01 --variable-link --out results/degraded --plots
semantic-robot benchmark --frames 160 --fps 8 --bandwidth 2 --loss 0.02 --variable-link --out results/severe --plots
python examples/ablation.py
```

## Scenarios

| Scenario | Bandwidth | Loss | Notes |
| --- | --- | --- | --- |
| fixed | 4 Mbps | 1% | 160 frames, 8 fps |
| degraded | 4 Mbps base x [1,.65,.25,1] | 1% + [0,2,7,0] percentage points | 20 frames per phase |
| severe | 2 Mbps base x [1,.65,.25,1] | 2% + [0,2,7,0] percentage points | 0.5 Mbps lowest phase, 28B semantic cap |

All use a 200ms decision deadline, 280ms stale-sample bound, 15ms modeled propagation, jitter ±4ms, and maximum 300ms source queue wait. Both network random number generation and video generation use fixed seeds. Same task schedule and data are used for all four methods.

## Metrics

`bytes_generated` counts encoded application data, even packets dropped before queue entry. `bytes_sent` counts bytes that enter the channel including packets subsequently lost; no TCP/IP, MAC/PHY overhead. `task_decision_accuracy` compares one of GO/STOP/SEARCH/PICKUP against the *synthetic* scene's rule-based decision. `hazard_decision_recall` is final STOP recall, including fallback STOP. `hazard_observation_recall` requires a valid decoded observation of a corridor hazard at decision time. `fresh_observation_ratio` measures same-frame observations usable at deadline. `relevant_object_recall_after_channel` matches task-relevant truth boxes to decoded boxes for packets scheduled to arrive, with 8px center tolerance; it does not impose decision deadline. Frame-level records in `frame_metrics.csv` permit further analysis. Local CPU timing and modeled latency will differ between machines.

## Encoder ablations

A fixed corpus of detected objects is reused for all four codec combinations: all detections full precision, all detections quantized, task-only full precision and task-only quantized. This separates compression from selecting relevant objects. The `adaptive_budgeted` measurement applies task filtering and quantization and additionally respects a byte cap.

## Caveats

This experiment is deliberately constructed. Values are useful for comparing code paths **under these assumptions**, not for claiming actual detection accuracy, certified safety, 6G performance, real radio throughput, or mission success in a physical warehouse.
