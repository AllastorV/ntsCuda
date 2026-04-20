"""
CUDA pipeline renderer for ntsCuda — full async, minimal CPU involvement.

Architecture
------------
Producer/consumer overlap with a 2-slot ring and two pre-captured CUDA
graphs:

    frame N   CPU fills pinned_upload[slot_a]
              GPU replays graph_a (H2D + fused kernel + D2H into pinned_download[slot_a])
              NVENC encodes pinned_download[slot_a-1]   (from previous iter)

    frame N+1 CPU fills pinned_upload[slot_b]            (overlaps GPU)
              GPU replays graph_b
              NVENC encodes pinned_download[slot_a]

Each graph is fully captured — including the cudaMemcpy H2D from the
corresponding pinned host slot and the cudaMemcpy D2H to the matching
pinned host slot — so per-frame CPU overhead collapses to ``graph.replay()``
plus an event wait.

Components
----------
* ``NvdecSource``   : PyAV NVDEC decode into a pinned host ring.
* ``launch_fused_ntsc`` : autotuned Triton kernel (BGR->YIQ->effects->BGR, FP16).
* ``NvencWriter``   : PyAV h264_nvenc encode (falls back to libx264 if NVENC
  unregistered).

VRAM pool
---------
All large GPU tensors (uint8 staging in/out, fp16 compute in/out) are
allocated once in a shared graph pool and reused by both captured graphs.
Zero malloc/free in the hot loop.

Known limits kept for honesty
-----------------------------
* PyAV VideoFrame ingress for NVENC currently re-uploads pixel data; true
  GPU-resident encode requires NVIDIA VPF or cuda-python NVENC bindings.
  NVENC itself still runs on GPU hardware, freeing CPU from libx264 work.
* Triton on Windows needs ``triton-windows``. If unavailable, the
  pipeline falls back to ``DefaultRenderer`` on first launch check.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

import numpy as np

from app.logs import logger

try:
    import torch
    _TORCH_OK = torch.cuda.is_available()
except Exception:
    torch = None  # type: ignore
    _TORCH_OK = False

from app.Renderer import DefaultRenderer
from app.triton_kernels import NTSCParams, launch_fused_ntsc, triton_available
from app.nvdec_source import NvdecSource, pyav_available
from app.nvenc_writer import NvencWriter


def cuda_pipeline_available() -> tuple[bool, str]:
    if not _TORCH_OK:
        return False, "torch CUDA not available"
    if not triton_available():
        return False, "triton not available (install triton-windows on Windows)"
    if not pyav_available():
        return False, "PyAV not installed (pip install av)"
    return True, ""


class CudaPipelineRenderer(DefaultRenderer):
    """
    Replaces DefaultRenderer.run() with an end-to-end async CUDA pipeline.

    Qt signals, Config, and pause/stop semantics are inherited unchanged;
    only the decode/process/encode hot loop is replaced.
    """

    ntsc_params: NTSCParams = NTSCParams()
    encoder_codec: str = "h264_nvenc"
    encoder_preset: str = "p5"
    encoder_bitrate: str = "12M"

    def run(self) -> None:  # noqa: C901 — the hot loop stays whole for clarity
        ok, reason = cuda_pipeline_available()
        if not ok:
            logger.warning(f"CUDA pipeline unavailable ({reason}); falling back")
            return super().run()

        import cv2  # only used for optional CPU resize to render_wh

        self.set_up()
        self.running = True
        render_wh = self.config["render_wh"]
        container_wh = self.config["container_wh"]
        upscale_2x = self.config["upscale_2x"]
        fps = self.render_data["input_video"]["orig_fps"]

        # --------- 1. Source (NVDEC) --------- #
        src = NvdecSource(self.render_data["input_video"]["path"], pinned_slots=3)
        src.open()
        W, H = render_wh
        device = torch.device("cuda")

        # --------- 2. Persistent VRAM pool + pinned host double buffer --------- #
        # Pinned host: 2 slots for upload, 2 for download (ping-pong).
        pinned_upload = [torch.empty((H, W, 3), dtype=torch.uint8, pin_memory=True) for _ in range(2)]
        pinned_download = [torch.empty((H, W, 3), dtype=torch.uint8, pin_memory=True) for _ in range(2)]

        # Single shared GPU staging set — both graphs reuse these. The graph
        # pool handle keeps allocations stable across the two captures.
        frame_in_u8_gpu = torch.empty((H, W, 3), dtype=torch.uint8, device=device)
        frame_in_gpu = torch.empty((H, W, 3), dtype=torch.float16, device=device)
        frame_out_gpu = torch.empty((H, W, 3), dtype=torch.float16, device=device)
        frame_out_u8_gpu = torch.empty((H, W, 3), dtype=torch.uint8, device=device)

        compute_stream = torch.cuda.Stream(device=device)

        # --------- 3. Warm-up (autotune + JIT) --------- #
        # Run once before capture so Triton autotune picks + caches a config.
        with torch.cuda.stream(compute_stream):
            frame_in_u8_gpu.copy_(pinned_upload[0], non_blocking=True)
            frame_in_gpu.copy_(frame_in_u8_gpu.to(torch.float16))
            launch_fused_ntsc(frame_in_gpu, frame_out_gpu, self.ntsc_params)
            frame_out_u8_gpu.copy_(frame_out_gpu.clamp(0, 255).to(torch.uint8))
            pinned_download[0].copy_(frame_out_u8_gpu, non_blocking=True)
        compute_stream.synchronize()

        # --------- 4. Capture TWO graphs sharing one memory pool --------- #
        pool = torch.cuda.graph_pool_handle()
        graphs: list[torch.cuda.CUDAGraph] = []
        events: list[torch.cuda.Event] = []

        for slot in range(2):
            g = torch.cuda.CUDAGraph()
            with torch.cuda.graph(g, pool=pool, stream=compute_stream):
                # H2D from pinned slot -> gpu u8 staging
                frame_in_u8_gpu.copy_(pinned_upload[slot], non_blocking=True)
                # u8 -> fp16
                frame_in_gpu.copy_(frame_in_u8_gpu.to(torch.float16))
                # fused effect
                launch_fused_ntsc(frame_in_gpu, frame_out_gpu, self.ntsc_params)
                # fp16 -> u8 (clamped)
                frame_out_u8_gpu.copy_(frame_out_gpu.clamp(0, 255).to(torch.uint8))
                # D2H into pinned slot
                pinned_download[slot].copy_(frame_out_u8_gpu, non_blocking=True)
            graphs.append(g)
            events.append(torch.cuda.Event())

        # --------- 5. NVENC writer --------- #
        tmp_output = self.render_data["target_file"].parent / (
            f"tmp_{self.render_data['target_file'].stem}.mp4"
        )
        writer = NvencWriter(
            path=tmp_output,
            width=container_wh[0],
            height=container_wh[1],
            fps=float(fps),
            codec=self.encoder_codec,
            preset=self.encoder_preset,
            bitrate=self.encoder_bitrate,
        )
        logger.info(f"Encoder: {writer.codec_name}")

        # --------- 6. Hot loop with ping-pong --------- #
        self.current_frame_index = -1
        self.renderStateChanged.emit(True)
        status_string = "CUDA pipeline starting..."
        total = self.render_data["input_video"]["frames_count"] or "?"

        src_wh = (src.width, src.height)
        pending_slot: Optional[int] = None  # slot whose GPU work is in flight

        try:
            for host_frame in src.iter_frames():
                if not self.running:
                    break
                if self.pause:
                    self.sendStatus.emit(f"{status_string} [P]")
                    time.sleep(0.3)
                    continue

                self.current_frame_index += 1
                slot = self.current_frame_index % 2

                # (a) If a frame is already in flight on `slot` (from 2 iters ago),
                #     wait and emit its result before overwriting its buffers.
                if self.current_frame_index >= 2:
                    events[slot].synchronize()
                    self._emit_frame(pinned_download[slot], container_wh, upscale_2x, writer)

                # (b) Fill upload slot with the freshly decoded frame.
                frame_np = host_frame.numpy()
                if src_wh != (W, H):
                    frame_np = cv2.resize(frame_np, (W, H))
                pinned_upload[slot].copy_(torch.from_numpy(frame_np))

                # (c) Launch graph for this slot; record completion event.
                with torch.cuda.stream(compute_stream):
                    graphs[slot].replay()
                    events[slot].record(compute_stream)

                pending_slot = slot
                self.increment_progress.emit()

                status_string = f"[CUDA/NVENC] {self.current_frame_index}/{total}"
                self.sendStatus.emit(status_string)

            # --------- 7. Drain the last 1-2 in-flight frames --------- #
            # After the loop, at most 2 frames are still on the GPU:
            # frame N (last launched) on slot N%2, and frame N-1 on the
            # opposite slot (if N >= 1). Emit in chronological order.
            if self.current_frame_index == 0:
                events[0].synchronize()
                self._emit_frame(pinned_download[0], container_wh, upscale_2x, writer)
            elif self.current_frame_index >= 1:
                prev_slot = (self.current_frame_index - 1) % 2
                last_slot = self.current_frame_index % 2
                events[prev_slot].synchronize()
                self._emit_frame(pinned_download[prev_slot], container_wh, upscale_2x, writer)
                events[last_slot].synchronize()
                self._emit_frame(pinned_download[last_slot], container_wh, upscale_2x, writer)
        finally:
            writer.close()
            src.close()
            # Release graphs before tensors (captured-allocator invariants).
            del graphs

        # --------- 8. Mux audio in --------- #
        self._mux_audio(tmp_output)

        self.renderStateChanged.emit(False)
        self.sendStatus.emit("[DONE] CUDA/NVENC render done")

    # ------------------------------------------------------------------ #

    def _emit_frame(
        self,
        pinned: "torch.Tensor",
        container_wh: tuple[int, int],
        upscale_2x: bool,
        writer: NvencWriter,
    ) -> None:
        import cv2

        out_np = pinned.numpy()
        if upscale_2x:
            out_np = cv2.resize(out_np, container_wh, interpolation=cv2.INTER_NEAREST)
        if self.current_frame_index % 30 == 0 or self.liveView:
            self.frameMoved.emit(self.current_frame_index)
            self.newFrame.emit(out_np)
        writer.write(out_np)

    def _mux_audio(self, tmp_output: Path) -> None:
        import ffmpeg

        orig_path = str(self.render_data["input_video"]["path"].resolve())
        result_path = str(self.render_data["target_file"].resolve())
        orig = ffmpeg.input(orig_path)
        temp_video = ffmpeg.input(str(tmp_output.resolve()))
        try:
            ffmpeg.output(
                temp_video.video,
                orig.audio,
                result_path,
                shortest=None,
                vcodec="copy",
                acodec="copy",
            ).overwrite_output().run()
        except ffmpeg.Error:
            ffmpeg.output(
                temp_video.video, result_path, shortest=None, vcodec="copy"
            ).overwrite_output().run()

        if tmp_output.exists():
            try:
                tmp_output.unlink()
            except OSError:
                pass
