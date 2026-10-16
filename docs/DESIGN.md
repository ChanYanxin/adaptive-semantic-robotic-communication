# Engineering design and trust boundaries

## Research hypothesis

Task-aware, compact semantic features can consume fewer application-layer bytes than full image offloading while supporting simple synthetic navigation and package-transport decisions. This project tests the hypothesis rather than asserting field performance.

## Workload and geometry

The warehouse is deterministic, 640 x 360 synthetic imagery. A simple color-based segmentation detector identifies rectangular representations of people, obstacles, packages, pallets and a robot. It does not learn any visual concept. Objects move according to scripted trajectories, not physics. Camera perspective, obstacle corridor `(145,138,502,335)` and package pickup zone `(325,165,495,242)` are hard-coded. Every 40 frames, the task alternates between navigation and transport.

## Four comparable pipelines

| Mode | Client | Payload | Edge |
| --- | --- | --- | --- |
| `raw` | JPEG full frame | bytes of JPEG | image decoding, segmentation |
| `roi` | crop a fixed task ROI | crop origin + JPEG | decoding, segmentation, coordinate restore |
| `fixed` | segment all objects | MessagePack of all labels, boxes and confidences | decode and task decision |
| `adaptive` | segment, prioritize task-relevant objects, quantize coordinates, enforce byte cap | MessagePack selected semantic records | decode and task decision |

This separates image transport from structured semantic transport. Moving the detector onboard for the two semantic modes **changes compute placement**; CPU stages are measured on the *same machine*, so performance/power of embedded platforms is not established. The semantic representation is task-specific structure, not a learned joint source-channel encoder.

## Task-aware encoder

Hazards inside the corridor are highest priority. During transport, packages inside the pickup zone are next. Remaining detections are omitted. Bounding-box coordinates are quantized to 2-pixel bins, with confidence stored as 8-bit integer. Application-layer budgets vary with estimated available bandwidth: less than 1Mbps -> 28B, less than 3Mbps -> 45B, at least 3Mbps -> 80B. The third package record can be dropped in the restricted budget while hazards are retained; information loss is intentional and explicitly measured.

## Decision logic

`STOP` for a known hazard in corridor; during transport, `PICKUP` for a package in target pickup zone; otherwise `GO` (navigation) or `SEARCH` (transport). With no recent observation from the current task, a conservative `STOP` is returned. Fallback STOP is **not** evidence of successful visual hazard detection. `hazard_decision_recall` (may credit fallback) and `hazard_observation_recall` (requires an observed hazard) must be kept separate. This is not a certified emergency stop controller.

## Link simulator and reproducibility

Deterministic seed 17 drives independent per-frame loss and jitter draws identically for each compared method. The FIFO rate limiter computes bytes x 8 / bitrate, simulated 15ms propagation, ±4ms jitter, configurable loss, and max 300ms queue wait. Each frame has an 8fps simulated timestamp and a 200ms decision deadline. Local client and edge CPU processing are measured and included in simulated packet availability timestamps. A queue-dropped packet is not counted as transmitted bytes; a transmitted packet later lost in transit does count. Model does not include MAC frames, PHY rate adaptation, interference, retransmission, congestion control, real Wi-Fi, 6G signaling, power or robot dynamics.

## Interpretation and limitations

- `task_decision_accuracy` is agreement with a toy rule, not physical task-completion percentage.
- Synthetic color segmentation has no field-valid object detection precision / recall or mAP.
- `relevant_object_recall_after_channel` is geometrical match under a simple center-tolerance rule for packets scheduled to arrive; it does not enforce deadline and is not mAP.
- A fixed ROI enjoys pre-selected corridor information.
- Semantic methods spend extra onboard inference work; a Jetson or other embedded test is necessary to understand power/throughput tradeoffs.
- The real TCP adapter only uses loopback and has no simulated packet loss; it proves framing and parsing work over a socket, not wireless efficiency.
- Optional Ultralytics adapter maps a subset of COCO classes; warehouse-specific packages and pallets need a task-specific dataset and training.
- The optional ROS 2 adapter publishes a state string, not a motor command or complete Gazebo integration.

Next steps: real camera and annotated datasets, calibrated hazards, hardware CPU/power measurements, actual Wi-Fi loss and p95 latency, multi-node ROS 2/Gazebo, and learned task-based semantic compression with rate-utility curves.
