# RX4 implementation and rollback

`joint_delay_dsp.py` searches all 360° directions at 2° grid spacing and multiple horizontal projections. Guard projections outside the accepted physical range are included, allowing unsupported maxima to be rejected instead of forced onto a physical boundary. Pair coherence curves retain a free carrier-phase intercept. A common geometric vector supplies all pair delays before their evidence is aggregated.

The rescue requires six represented channels and twelve supported pairs; mean coherence ≥0.94, worst-pair coherence ≥0.80, projection 0.25–1.3, and a spectral-loss budget `min(0.02,max(0.002,1.5*(1-independent_coherence)))`. Current-frame competing peaks need score separation; these are engineering thresholds, not calibrated probabilities. No previous-angle condition exists.

`highband_dsp.py` caches the original scoring arrays and invokes the rescue only after both original paths fail, with at least six code-matched channels. Original residual fields may describe the rejected primary fit; `joint_attempt` contains the actual rescue evidence. A coherent model by construction is not itself proof of a correct physical angle.

`app_instance.py` and `refresh_and_start.py` provide a nonce-scoped local restart. No unrelated process is killed and no network update is downloaded. The app closes through its ordinary shutdown path. Runtime checkpoint and source hash are checked in `logs/one-click-update-status.json`.

The phone trial utility records exact raw-block/sequence pairs while keeping the normal GUI visible. Analysis is offline and separates user interruptions, no-code windows and direction fitting. Plots use median spectra to reduce transient bias; the mean unmatched spectrum remains visible as a dashed diagnostic curve.

Before-RX4 sources and firmware are in `backups/before-RX4.zip`. To roll back the estimator, close the app, restore `highband_dsp.py` from that archive and restart. Keep raw evidence. The rescue module may remain unused. GPIO, firmware payload, default code, band and smoothing were not changed.
