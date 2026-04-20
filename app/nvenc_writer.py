"""
NVENC-backed video writer using PyAV.

h264_nvenc / hevc_nvenc offloads the final encode to the GPU's NVENC
engine, which runs concurrently with the CUDA compute engine and the
NVDEC decode engine. The CPU's job collapses to passing already-encoded
packets to the muxer, so the render pipeline no longer competes with
libx264 for cores.

The writer accepts BGR uint8 numpy arrays (same shape convention as
cv2.VideoWriter) and feeds them as yuv420p via PyAV's built-in
rgb->yuv converter (CPU-side swscale for now — the yuv conversion cost
is small next to the encode cost we just eliminated).

Fallback behaviour: if h264_nvenc is not registered (no driver/SDK),
fall back to libx264.
"""
from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import Optional

import numpy as np

try:
    import av
    _PYAV_OK = True
except Exception:
    av = None  # type: ignore
    _PYAV_OK = False


class NvencWriter:
    def __init__(
        self,
        path: str | Path,
        width: int,
        height: int,
        fps: float,
        codec: str = "h264_nvenc",
        preset: str = "p5",         # NVENC presets p1..p7 (p7 = highest quality)
        tune: str = "hq",
        bitrate: Optional[str] = "12M",
        pix_fmt_out: str = "yuv420p",
    ) -> None:
        if not _PYAV_OK:
            raise RuntimeError("PyAV not installed; cannot use NVENC writer")

        self.path = str(Path(path))
        self.width = width
        self.height = height
        self.fps = fps
        self.pix_fmt_out = pix_fmt_out

        self._container = av.open(self.path, mode="w")
        try:
            self._stream = self._container.add_stream(codec, rate=Fraction(fps).limit_denominator(1000))
        except Exception:
            # NVENC unavailable — fall back to CPU encoder.
            self._stream = self._container.add_stream("libx264", rate=Fraction(fps).limit_denominator(1000))
            codec = "libx264"

        self._stream.width = width
        self._stream.height = height
        self._stream.pix_fmt = pix_fmt_out
        if bitrate is not None:
            self._stream.bit_rate = int(float(bitrate.rstrip("Mm")) * 1_000_000) if "M" in bitrate.upper() else int(bitrate)

        # NVENC-specific tuning
        if codec.endswith("_nvenc"):
            self._stream.options = {
                "preset": preset,
                "tune": tune,
                "rc": "vbr",
                "b_ref_mode": "middle",
                "gpu": "0",
            }
        else:
            self._stream.options = {"preset": "medium"}

        self.codec_name = codec

    def write(self, bgr_frame: np.ndarray) -> None:
        """bgr_frame: (H, W, 3) uint8, BGR order (cv2 convention)."""
        # PyAV's VideoFrame.from_ndarray expects RGB; do the swap cheaply.
        rgb = bgr_frame[..., ::-1]
        if not rgb.flags["C_CONTIGUOUS"]:
            rgb = np.ascontiguousarray(rgb)
        frame = av.VideoFrame.from_ndarray(rgb, format="rgb24")
        for packet in self._stream.encode(frame):
            self._container.mux(packet)

    def close(self) -> None:
        # Flush encoder.
        if self._stream is not None:
            for packet in self._stream.encode():
                self._container.mux(packet)
        if self._container is not None:
            self._container.close()
        self._stream = None
        self._container = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
