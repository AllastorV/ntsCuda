"""
Fused NTSC degradation kernel written in OpenAI Triton.

A single program instance processes one BLOCK_H x BLOCK_W tile of the frame,
performing the full BGR -> YIQ -> (chroma lag + luma lowpass + scanline
attenuation + noise) -> BGR pipeline without intermediate round-trips to
global memory. Inputs and outputs are FP16 tensors (tensor-core friendly);
compute accumulators stay in FP32 for numerical headroom.

Tile layout
-----------
    program_id(0) -> block row index   (y tiles)
    program_id(1) -> block col index   (x tiles)
    Each program loads a (BLOCK_H, BLOCK_W, 3) slab of pixels using masked
    tl.load, operates on it, and stores it back. The slab sits in registers
    for the duration of the kernel, so there is no shared-memory spill for
    the 3x3 tap 1D luma low-pass.

Windows note
------------
    Triton on Windows runs via the `triton-windows` wheel; see
    https://github.com/woct0rdho/triton-windows. If the import fails the
    caller should fall back to the CuPy path in app/ntsc.py.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import torch

try:
    import triton
    import triton.language as tl

    _TRITON_OK = True
except Exception as _e:  # pragma: no cover - import guard
    triton = None  # type: ignore
    tl = None  # type: ignore
    _TRITON_OK = False
    _TRITON_IMPORT_ERR = _e


def triton_available() -> bool:
    return _TRITON_OK and torch.cuda.is_available()


@dataclass
class NTSCParams:
    """Tunable knobs passed to the fused kernel. FP32 scalars."""

    chroma_lag_px: int = 6           # horizontal shift on I/Q in pixels
    luma_lowpass_strength: float = 0.85  # 0..1 mix with 3-tap blur
    scanline_attenuation: float = 0.35   # even-row dim factor (0..1)
    noise_amplitude: float = 0.04        # in YIQ Y-channel units (0..1)
    noise_seed: int = 1337


if _TRITON_OK:

    @triton.jit
    def _hash_u32(x):
        """Integer hash -> pseudo-uniform float in [-0.5, 0.5]. Deterministic."""
        x = x ^ (x >> 16)
        x = x * 0x7FEB352D
        x = x ^ (x >> 15)
        x = x * 0x846CA68B
        x = x ^ (x >> 16)
        return (x.to(tl.float32) / 4294967295.0) - 0.5

    # Autotune sweeps tile geometry per unique (H, W). The best config is
    # cached by Triton's JIT, so only the first frame at a given resolution
    # pays the tuning cost; replays hit the cache.
    _AUTOTUNE_CONFIGS = [
        triton.Config({"BLOCK_H": 8,  "BLOCK_W": 64},  num_warps=4, num_stages=2),
        triton.Config({"BLOCK_H": 16, "BLOCK_W": 64},  num_warps=4, num_stages=2),
        triton.Config({"BLOCK_H": 16, "BLOCK_W": 128}, num_warps=4, num_stages=3),
        triton.Config({"BLOCK_H": 32, "BLOCK_W": 64},  num_warps=8, num_stages=2),
        triton.Config({"BLOCK_H": 32, "BLOCK_W": 128}, num_warps=8, num_stages=3),
        triton.Config({"BLOCK_H": 8,  "BLOCK_W": 256}, num_warps=8, num_stages=2),
    ]

    @triton.autotune(configs=_AUTOTUNE_CONFIGS, key=["H", "W"])
    @triton.jit
    def fused_ntsc_kernel(
        in_ptr,               # *fp16, (H, W, 3) BGR, contiguous
        out_ptr,              # *fp16, (H, W, 3)
        H,
        W,
        STRIDE_Y: tl.constexpr,
        STRIDE_X: tl.constexpr,
        chroma_lag: tl.constexpr,
        luma_mix: tl.constexpr,
        scan_atten: tl.constexpr,
        noise_amp: tl.constexpr,
        seed: tl.constexpr,
        BLOCK_H: tl.constexpr,
        BLOCK_W: tl.constexpr,
    ):
        pid_y = tl.program_id(0)
        pid_x = tl.program_id(1)

        # Absolute pixel coords for this tile.
        offs_y = pid_y * BLOCK_H + tl.arange(0, BLOCK_H)
        offs_x = pid_x * BLOCK_W + tl.arange(0, BLOCK_W)
        mask_y = offs_y < H
        mask_x = offs_x < W
        mask = mask_y[:, None] & mask_x[None, :]

        # Base offsets into the (H, W, 3) buffer.
        base = offs_y[:, None] * STRIDE_Y + offs_x[None, :] * STRIDE_X

        # ---- Vectorized load: 3 channels as three aligned fp16 loads ----
        # Triton's compiler coalesces consecutive element loads into the
        # widest available transaction (up to 128-bit) when stride is 1.
        b = tl.load(in_ptr + base + 0, mask=mask, other=0.0).to(tl.float32)
        g = tl.load(in_ptr + base + 1, mask=mask, other=0.0).to(tl.float32)
        r = tl.load(in_ptr + base + 2, mask=mask, other=0.0).to(tl.float32)

        b = b / 255.0
        g = g / 255.0
        r = r / 255.0

        # ---- BGR -> YIQ (NTSC FCC matrix) ----
        y = 0.299 * r + 0.587 * g + 0.114 * b
        i_ = 0.596 * r - 0.274 * g - 0.322 * b
        q_ = 0.211 * r - 0.523 * g + 0.312 * b

        # ---- Luma 3-tap horizontal low-pass (in-tile, no shared mem spill) ----
        # Wrap-inside-tile; edges between tiles get a small seam but avoid
        # any extra gmem traffic. Acceptable for NTSC aesthetic.
        y_left = tl.load(in_ptr + base - STRIDE_X + 0, mask=mask & (offs_x[None, :] > 0), other=0.0).to(tl.float32) / 255.0 * 0.114 \
               + tl.load(in_ptr + base - STRIDE_X + 1, mask=mask & (offs_x[None, :] > 0), other=0.0).to(tl.float32) / 255.0 * 0.587 \
               + tl.load(in_ptr + base - STRIDE_X + 2, mask=mask & (offs_x[None, :] > 0), other=0.0).to(tl.float32) / 255.0 * 0.299
        y_right = tl.load(in_ptr + base + STRIDE_X + 0, mask=mask & (offs_x[None, :] < W - 1), other=0.0).to(tl.float32) / 255.0 * 0.114 \
                + tl.load(in_ptr + base + STRIDE_X + 1, mask=mask & (offs_x[None, :] < W - 1), other=0.0).to(tl.float32) / 255.0 * 0.587 \
                + tl.load(in_ptr + base + STRIDE_X + 2, mask=mask & (offs_x[None, :] < W - 1), other=0.0).to(tl.float32) / 255.0 * 0.299
        y_blur = 0.25 * y_left + 0.5 * y + 0.25 * y_right
        y = y * (1.0 - luma_mix) + y_blur * luma_mix

        # ---- Chroma horizontal lag ----
        # Shift I/Q right by chroma_lag px by sampling from the left neighbour.
        src_x = offs_x[None, :] - chroma_lag
        lag_mask = (src_x >= 0) & mask
        lag_base = offs_y[:, None] * STRIDE_Y + src_x * STRIDE_X
        lb = tl.load(in_ptr + lag_base + 0, mask=lag_mask, other=0.0).to(tl.float32) / 255.0
        lg = tl.load(in_ptr + lag_base + 1, mask=lag_mask, other=0.0).to(tl.float32) / 255.0
        lr = tl.load(in_ptr + lag_base + 2, mask=lag_mask, other=0.0).to(tl.float32) / 255.0
        i_ = 0.596 * lr - 0.274 * lg - 0.322 * lb
        q_ = 0.211 * lr - 0.523 * lg + 0.312 * lb

        # ---- Scanline attenuation on even rows ----
        is_even = (offs_y[:, None] % 2) == 0
        atten = tl.where(is_even, 1.0 - scan_atten, 1.0)
        y = y * atten

        # ---- Per-pixel deterministic noise on Y ----
        pix_id = (
            offs_y[:, None].to(tl.uint32) * tl.full((), 1973, tl.uint32)
            + offs_x[None, :].to(tl.uint32) * tl.full((), 9277, tl.uint32)
            + tl.full((), seed, tl.uint32)
        )
        n = _hash_u32(pix_id) * noise_amp
        y = y + n

        # ---- YIQ -> BGR ----
        r_out = y + 0.956 * i_ + 0.621 * q_
        g_out = y - 0.272 * i_ - 0.647 * q_
        b_out = y - 1.106 * i_ + 1.703 * q_

        r_out = tl.minimum(tl.maximum(r_out, 0.0), 1.0) * 255.0
        g_out = tl.minimum(tl.maximum(g_out, 0.0), 1.0) * 255.0
        b_out = tl.minimum(tl.maximum(b_out, 0.0), 1.0) * 255.0

        tl.store(out_ptr + base + 0, b_out.to(tl.float16), mask=mask)
        tl.store(out_ptr + base + 1, g_out.to(tl.float16), mask=mask)
        tl.store(out_ptr + base + 2, r_out.to(tl.float16), mask=mask)


def launch_fused_ntsc(
    frame_in: "torch.Tensor",
    frame_out: "torch.Tensor",
    params: NTSCParams,
) -> None:
    """
    Launch the fused kernel. Both tensors must be CUDA, FP16, (H, W, 3),
    contiguous. The chroma-lag read path samples a neighbour pixel, so
    DO NOT alias frame_in and frame_out.

    Tile geometry is chosen by @triton.autotune per unique (H, W).
    """
    if not triton_available():
        raise RuntimeError(
            f"Triton not available: {_TRITON_IMPORT_ERR!r}"
            if not _TRITON_OK
            else "CUDA device not available"
        )

    assert frame_in.is_cuda and frame_out.is_cuda
    assert frame_in.dtype == torch.float16 and frame_out.dtype == torch.float16
    assert frame_in.shape == frame_out.shape and frame_in.shape[-1] == 3
    assert frame_in.is_contiguous() and frame_out.is_contiguous()

    H, W, _ = frame_in.shape
    stride_y = W * 3
    stride_x = 3

    # Grid lambda lets autotune-chosen BLOCK_{H,W} drive program count.
    grid = lambda meta: (triton.cdiv(H, meta["BLOCK_H"]), triton.cdiv(W, meta["BLOCK_W"]))
    fused_ntsc_kernel[grid](
        frame_in,
        frame_out,
        H,
        W,
        STRIDE_Y=stride_y,
        STRIDE_X=stride_x,
        chroma_lag=int(params.chroma_lag_px),
        luma_mix=float(params.luma_lowpass_strength),
        scan_atten=float(params.scanline_attenuation),
        noise_amp=float(params.noise_amplitude),
        seed=int(params.noise_seed),
    )
