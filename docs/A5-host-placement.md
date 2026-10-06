# A5 — Host placement for OneStreamer-4B (WO-038)

Date 2026-10-06 · Read-only analysis, no code run · Status: **(a) phone: NO-GO as host, GO as pre-filter · (b) M3 Air: GO at ~1 fps (Halo's expected rate), NO-GO at 4 fps · (c) GPU host: GO for 4 fps.** Numbers marked *est.* are not measured yet; the first B-track hour should replace them.

## Facts found (2026-10-06)

- **Weights are public.** `MCG-NJU/OneStreamer-4B` (ungated, created 2026-09-28; arch `Qwen3VLForConditionalGeneration`, init from Qwen3-VL-4B-Instruct). Community GGUF: `mradermacher/OneStreamer-4B-GGUF` (2026-10-02) incl. vision projector: Q4_K_M 2.5 GB + mmproj Q8_0 0.45 GB; Q8_0 4.3 GB. → WO-038 Track B trigger (i) appears met; needs Malik's confirmation.
- Vision encoder: patch 16, spatial merge 2, temporal patch 2, 24 layers, width 1024 (~0.4 B params).
- At 640×480: (640/32)·(480/32) = **300 visual tokens per 2-frame temporal group.** 4 fps → 2 groups/s → **~600 visual tokens/s**, plus up to 128 text tokens per update. 1 fps → ~150 visual tokens/s.

## Options (rev1 lettering: (a) phone, (b) M3 Air, (c) GPU host)

**(a) Phone-side small VLM: NO-GO for OneStreamer, GO only as a pre-filter.** OneStreamer-4B at Q4 is ~3 GB plus a 0.4 B vision tower; on a phone that means thermal throttling within minutes and no StreamingSession runtime (iOS/Android ports of llama.cpp's multimodal path exist, but not the rolling-window/PHCM loop). A sub-1B VLM on the phone could run a cheap "anything changed?" pre-filter that decides which Halo stills are worth sending to (b) or (c), cutting uplink and battery. *est.*, not measured.

The table below covers the laptop and GPU-host options (its (a)/(b) rows are the Air under llama.cpp and MLX, i.e. rev1 option (b)).

| Option | Fits memory | 4 fps real-time gate | ~1 fps captions | Port effort | Privacy |
|---|---|---|---|---|---|
| (a) M3 Air 16 GB, llama.cpp (mtmd) Q4_K_M | Yes: ~3 GB weights + KV for a 64-frame window (~9.6k vis tokens) ≈ 1–2 GB *est.* | **Doubtful.** Needs sustained ≥600 tok/s prefill + ViT per group; M3 Air base GPU *est.* 250–450 tok/s prefill for a 4B Q4, and fanless throttling under sustained load | **Likely yes** (~150 tok/s) | **Medium–high:** llama.cpp has no StreamingSession (rolling 64-frame window, PHCM caption memory, `</Silence>/</Standby>/</Response>` loop). Rebuild that loop in Python around `llama-server` | Best: nothing leaves the laptop |
| (b) M3 Air, MLX (`mlx-vlm`, Qwen3-VL support) | Yes | Same compute ceiling as (a); MLX prefill on M3 *est.* similar or slightly better | Likely yes | **Medium:** port `Inference/inference.py` session logic to MLX; Qwen3-VL arch is supported upstream *(verify OneStreamer's custom tokens load)* | Best |
| (c) GPU host over network (cloud or local box, Terraform `infra/`, OpenShell) | n/a | **Yes**, original CUDA code path, no port | Yes | **Low:** run upstream as-is | Frames cross a private network to a host you control; never to a third-party API |

## Latency budget for (c)

Gate decisions arrive every update (4 fps → 250 ms frame period). Budget per update, glasses → reply:

| Step | Budget |
|---|---|
| Capture + JPEG encode on device | 30 ms |
| Uplink (Tailscale/WireGuard, home → GPU host) | 40–80 ms |
| Model step (ViT + prefill + decode of gate token) | 80–120 ms on a 24 GB-class GPU *est.* |
| Downlink (text event only) | 10–40 ms |
| **Total to gate decision** | **~160–270 ms** → OK for Silence/Standby; a spoken Response adds TTS (out of scope) |

A response is useful within ~1 s of the evidence appearing, so (c) has slack at 4 fps; (a)/(b) at 1 fps add up to ~1 s of frame latency, which costs timing F1 on fast events. That is exactly what B3's 4 fps vs ~1 fps runs should measure.

## Recommendation

1. **Now (no spend):** prototype (b) or (a) at 1 fps on the Air for captions + gate, measure tokens/s and thermals for 10 min. This answers the doubtful cell with numbers.
2. **For the 4 fps gate:** (c), gated on Malik's GPU approval (Track B trigger ii), 20 GPU-hour cap.
3. Keep the A1 contract as the seam: the Air (1 fps) and the GPU host (4 fps) are just two `onestreamer` adapter instances with different `source` suffixes.

Effort: (a) or (b) 1-fps prototype ≈ 1–2 days *est.*; (c) bring-up ≈ 0.5 day once a host exists *est.*

## Note on Halo (A6)

Halo delivers ~1 fps stills over BLE (rev1 A6 estimate). At that rate (b) the M3 Air is sufficient on compute, so a fully local Halo → laptop → OneStreamer path is plausible without any GPU spend. B3's 1 fps run will show what timing F1 that costs versus 4 fps.
