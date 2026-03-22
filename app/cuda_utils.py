"""
Optional GPU/CUDA acceleration utilities for ntsCuda.

CuPy provides a NumPy-compatible API for GPU computation.
Falls back transparently to CPU NumPy when no GPU is available.

Installation (choose the version matching your CUDA toolkit):
    pip install cupy-cuda12x   # CUDA 12.x
    pip install cupy-cuda11x   # CUDA 11.x
    pip install cupy-cuda102   # CUDA 10.2

Usage:
    from app.cuda_utils import xp, to_cpu, is_gpu_available
    arr = xp.asarray(numpy_array)   # moves to GPU if available
    result = to_cpu(arr)            # always returns numpy array
"""

import numpy as np

_cupy_available = False
cp = None

try:
    import cupy as _cp
    # Verify a GPU device is actually accessible
    _cp.cuda.Device(0).compute_capability
    cp = _cp
    _cupy_available = True
except Exception:
    pass

# xp is the active array module: cupy on GPU, numpy on CPU
xp = cp if _cupy_available else np


def is_gpu_available() -> bool:
    """Returns True if a CUDA-capable GPU is detected."""
    return _cupy_available


def to_gpu(arr: np.ndarray):
    """Transfer a numpy array to GPU memory. No-op if GPU is unavailable."""
    if _cupy_available and cp is not None:
        return cp.asarray(arr)
    return arr


def to_cpu(arr) -> np.ndarray:
    """Transfer an array to CPU numpy. Handles both numpy and cupy arrays."""
    if _cupy_available and cp is not None and isinstance(arr, cp.ndarray):
        return cp.asnumpy(arr)
    return np.asarray(arr)


def fft2(arr):
    """2D FFT using GPU when available, CPU otherwise."""
    if _cupy_available and cp is not None:
        return cp.fft.fft2(cp.asarray(arr))
    return np.fft.fft2(arr)


def ifft2(arr):
    """Inverse 2D FFT. Returns a numpy array on CPU."""
    if _cupy_available and cp is not None:
        if isinstance(arr, cp.ndarray):
            return cp.asnumpy(cp.fft.ifft2(arr))
        return cp.asnumpy(cp.fft.ifft2(cp.asarray(arr)))
    return np.fft.ifft2(arr)


def fftshift(arr):
    """FFT shift using the same module as the input array."""
    if _cupy_available and cp is not None and isinstance(arr, cp.ndarray):
        return cp.fft.fftshift(arr)
    return np.fft.fftshift(to_cpu(arr))


def ifftshift(arr):
    """Inverse FFT shift using the same module as the input array."""
    if _cupy_available and cp is not None and isinstance(arr, cp.ndarray):
        return cp.fft.ifftshift(arr)
    return np.fft.ifftshift(to_cpu(arr))


def asarray(arr):
    """Convert to GPU array if GPU is available, otherwise keep as numpy."""
    if _cupy_available and cp is not None:
        return cp.asarray(arr)
    return np.asarray(arr)


def real(arr) -> np.ndarray:
    """Return real part as a CPU numpy array."""
    if _cupy_available and cp is not None and isinstance(arr, cp.ndarray):
        return cp.asnumpy(cp.real(arr))
    return np.real(arr)
