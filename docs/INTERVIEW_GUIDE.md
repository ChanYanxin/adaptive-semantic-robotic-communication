# Interview technical discussion

**Q: What was built?** A runnable task-oriented structured perception and communication pipeline, a seeded queue/loss simulator, paired comparisons against full-frame and ROI image transmission, a real loopback TCP interface, unit tests, reproducible CSV/JSON reports, an optional YOLO adapter, and a minimal ROS 2 state publisher.

**Q: Is this 6G semantic communication?** No. It is an *application-layer task-oriented semantic information exchange* prototype. It does not learn an end-to-end encoder, optimize PHY signaling or implement a cellular radio stack. The INDA posting mentions semantic communication; this is an engineering exploration of one possible component.

**Q: Why 99.92% fewer bytes than JPEG?** Because the benchmark transmits a tiny number of structured boxes/class IDs rather than a 640x360 image, *and moves segmentation onboard*. Such savings are task- and dataset-specific and ignore IP/MAC overhead and onboard cost. They are not evidence that learned semantics beat all image codecs.

**Q: Why is adaptive better than fixed?** It removes task-irrelevant objects and uses quantization. In severe-link periods it drops lower-priority package records when necessary. This can reduce object completeness, so report that tradeoff rather than only a compression rate.

**Q: What is the safety tradeoff?** A fail-safe STOP might avoid an unsafe GO but can reduce productivity without any actual hazard recognition. Report `hazard_observation_recall`, `unnecessary_stop_frames` and `task_decision_accuracy` separately.

**Q: How was latency measured?** Python encode/decode CPU time was measured on one host. Serialization, propagation, loss, jitter and queuing were **simulated**. There was a separate real TCP loopback framing test, but no Wi-Fi latency measurement.

**Q: What should happen next?** Use labeled warehouse data and a trained detector, deploy source and edge on physically separated systems, test over Wi-Fi, implement a Gazebo robot and physical task-success metrics, and consider a learned rate-utility or uncertainty-aware encoder.
