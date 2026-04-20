"""
NVDEC-backed video source using PyAV.

Decoding runs on the GPU's dedicated NVDEC engine, overlapping freely with
the CUDA compute pipeline. PyAV still hands back CPU frames (true zero-copy
NVDEC->CUDA from Python requires CUDA-VideoCodec SDK bindings that are not
broadly available), but decode cost is off the CPU and off the main stream,
which is the dominant win in practice.

The source stages frames into pinned (page-locked) host memory so the
pipeline's async H2D copy can saturate PCIe without CPU-side stalls.

Usage
-----
    src = NvdecSource(path, pinned_slots=3)
    src.open()
    for pinned_frame in src.iter_frames():   # torch.uint8, pinned, (H,W,3) BGR
        ... upload async ...
    src.close()
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterator, Optional, Tuple

import numpy as np
import torch

try:
    import av  # PyAV

    _PYAV_OK = True
except Exception as _e:
    av = None  # type: ignore
    _PYAV_OK = False
    _PYAV_IMPORT_ERR = _e


def pyav_available() -> bool:
    return _PYAV_OK


class NvdecSource:
    """
    Open a video with NVDEC hwaccel when available, fall back to SW decode.

    Maintains a small ring of pinned host buffers so producer (decoder) and
    consumer (async H2D uploader) can run concurrently without reallocating
    page-locked memory per frame.
    """

    def __init__(
        self,
        path: str | Path,
        pinned_slots: int = 3,
        force_sw: bool = False,
    ) -> None:
        if not _PYAV_OK:
            raise RuntimeError(f"PyAV not available: {_PYAV_IMPORT_ERR!r}")

        self.path = str(Path(path))
        self.pinned_slots = pinned_slots
        self.force_sw = force_sw

        self._container = None
        self._stream = None
        self._pinned_ring: list[torch.Tensor] = []
        self._ring_idx = 0
        self._frame_wh: Optional[Tuple[int, int]] = None
        self._fps: Optional[float] = None
        self._frame_count: Optional[int] = None

    # --------- lifecycle --------- #

    def open(self) -> None:
        # Try NVDEC first; PyAV exposes this via codec_context.options.
        opts = {}
        if not self.force_sw:
            opts = {"hwaccel": "cuda"}

        self._container = av.open(self.path, options=opts)
        self._stream = self._container.streams.video[0]

        # PyAV needs THREAD_AUTO so the decode loop doesn't block the GIL
        # more than necessary.
        self._stream.thread_type = "AUTO"

        w = int(self._stream.codec_context.width)
        h = int(self._stream.codec_context.height)
        self._frame_wh = (w, h)
        self._fps = float(self._stream.average_rate) if self._stream.average_rate else 30.0
        self._frame_count = int(self._stream.frames) if self._stream.frames else None

        # Allocate pinned host buffers once (the "9. persistent pool" at host side).
        self._pinned_ring = [
            torch.empty((h, w, 3), dtype=torch.uint8, pin_memory=True)
            for _ in range(self.pinned_slots)
        ]

    def close(self) -> None:
        if self._container is not None:
            self._container.close()
            self._container = None
        self._stream = None
        self._pinned_ring.clear()

    # --------- metadata --------- #

    @property
    def width(self) -> int:
        assert self._frame_wh is not None, "call open() first"
        return self._frame_wh[0]

    @property
    def height(self) -> int:
        assert self._frame_wh is not None, "call open() first"
        return self._frame_wh[1]

    @property
    def fps(self) -> float:
        assert self._fps is not None, "call open() first"
        return self._fps

    @property
    def frame_count(self) -> Optional[int]:
        return self._frame_count

    # --------- iteration --------- #

    def iter_frames(self) -> Iterator[torch.Tensor]:
        """
        Yield frames as pinned torch.uint8 tensors in BGR, shape (H, W, 3).

        The yielded tensor aliases a slot in the pinned ring; the caller
        must finish its async H2D copy (torch.cuda.synchronize on the copy
        stream, or record/wait on an event) before the next next() call
        overwrites the slot.
        """
        assert self._container is not None, "call open() first"

        for packet in self._container.demux(self._stream):
            for frame in packet.decode():
                arr = frame.to_ndarray(format="bgr24")  # (H, W, 3) uint8
                slot = self._pinned_ring[self._ring_idx]
                self._ring_idx = (self._ring_idx + 1) % self.pinned_slots

                # Single memcpy into pinned memory. `slot` is pre-allocated
                # and pinned so the next copy-stream H2D is truly async.
                slot.copy_(torch.from_numpy(arr))
                yield slot
