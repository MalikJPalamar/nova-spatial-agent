# nova-spatial-agent

Implementation body for WO-038 (private spec). Doctrine, rules and work orders live in MalikJPalamar/Centaurion docs/PRD.md — this repo holds code only (R2/R3).

Layout:
- `perception/` — PerceptionSource + adapters: gemini-live, onestreamer, halo
- `gate/` — state machine
- `replay/` — OneStreamer-1M harness
- `rnd/splat-memory/` — 3DGS seam, notes only
