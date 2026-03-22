import math
import random
import sys
from enum import Enum
from pathlib import Path
from typing import List

import numpy
import scipy
from scipy.signal import lfilter
from scipy.ndimage.interpolation import shift

import numpy as np
import cv2

from app import cuda_utils

M_PI = math.pi

Int_MIN_VALUE = -2147483648
Int_MAX_VALUE = 2147483647

ring_pattern_real_path = 'app/ringPattern.npy'
if getattr(sys, 'frozen', False):
    ring_pattern_real_path = f'{sys._MEIPASS}/app/ringPattern.npy'

ring_pattern_path = Path(ring_pattern_real_path)
RingPattern = np.load(str(ring_pattern_path.resolve()))


def ringing(img2d, alpha=0.5, noiseSize=0, noiseValue=2, clip=True, seed=None):
    """
    https://bavc.github.io/avaa/artifacts/ringing.html
    :param img2d: 2d image
    :param alpha: float, reconstruction quality (0-1) optimal values for tv ringing modeling is 0.3-0.99
    :param noiseSize: float, noise size  (0-1) optimal values  is 0.5-0.99 if noiseSize=0 - no noise
    :param noiseValue: float, noise amplitude  (0-5) optimal values  is 0.5-2
    :return: 2d image

    GPU-accelerated via CuPy when available; otherwise uses numpy FFT.
    """
    rows, cols = img2d.shape
    crow, ccol = rows // 2, cols // 2

    # GPU FFT when available, otherwise numpy FFT (both faster than cv2.dft)
    dft_shift = cuda_utils.fftshift(cuda_utils.fft2(img2d.astype(np.float32)))

    # Build frequency-domain band-pass mask (2D real mask)
    mask = np.zeros((rows, cols), dtype=np.float32)
    maskH = min(crow, int(1 + alpha * crow))
    mask[:, ccol - maskH:ccol + maskH] = 1.0

    if noiseSize > 0:
        noise = np.ones((rows, cols), dtype=np.float32) * noiseValue - noiseValue / 2.0
        start = int(ccol - ((1 - noiseSize) * ccol))
        stop = int(ccol + ((1 - noiseSize) * ccol))
        noise[:, start:stop] = 0.0
        rnd = np.random.RandomState(seed)
        mask = mask + rnd.rand(rows, cols).astype(np.float32) * noise - noise / 2.0

    # Move mask to GPU if dft_shift is on GPU
    mask_arr = cuda_utils.asarray(mask)
    img_back = cuda_utils.real(cuda_utils.ifft2(cuda_utils.ifftshift(dft_shift * mask_arr)))

    if clip:
        _min, _max = img2d.min(), img2d.max()
        return np.clip(img_back, _min, _max)
    else:
        return img_back


def ringing2(img2d, power=4, shift=0, clip=True):
    """
    https://bavc.github.io/avaa/artifacts/ringing.html
    :param img2d: 2d image
    :param power: int, ringing pattern power (optimal 2 - 6)
    :return: 2d image

    GPU-accelerated via CuPy when available; otherwise uses numpy FFT.
    """
    rows, cols = img2d.shape

    # GPU FFT when available, otherwise numpy FFT
    dft_shift = cuda_utils.fftshift(cuda_utils.fft2(img2d.astype(np.float32)))

    scalecols = int(cols * (1 + shift))
    mask = cv2.resize(RingPattern[np.newaxis, :], (scalecols, 1), interpolation=cv2.INTER_LINEAR)[0]
    mask = mask[(scalecols // 2) - (cols // 2):(scalecols // 2) + (cols // 2)]
    mask = (mask ** power).astype(np.float32)

    # mask[None, :] broadcasts to (rows, cols) — applied equally to real & imag
    mask_arr = cuda_utils.asarray(mask[None, :])
    img_back = cuda_utils.real(cuda_utils.ifft2(cuda_utils.ifftshift(dft_shift * mask_arr)))

    if clip:
        _min, _max = img2d.min(), img2d.max()
        return np.clip(img_back, _min, _max)
    else:
        return img_back


def fmod(x: float, y: float) -> float:
    return x % y


class NumpyRandom:
    def __init__(self, seed=None):
        self.rnd = numpy.random.RandomState(seed)

    def nextInt(self, _from: int = Int_MIN_VALUE, until: int = Int_MAX_VALUE) -> int:
        return self.rnd.randint(_from, until)

    def nextIntArray(self, size: int, _from: int = Int_MIN_VALUE, until: int = Int_MAX_VALUE) -> numpy.ndarray:
        return self.rnd.randint(_from, until, size, dtype=numpy.int32)


class XorWowRandom:
    def __init__(self, seed1: int, seed2: int):
        self.x: int = numpy.int32(seed1)
        self.y: int = numpy.int32(seed2)
        self.z: int = numpy.int32(0)
        self.w: int = numpy.int32(0)
        self.v: int = -numpy.int32(seed1) - 1
        self.addend: int = numpy.int32((numpy.int32(seed1) << 10) ^ (numpy.uint32(seed2) >> 4))
        [self._nextInt() for _ in range(0, 64)]

    def _nextInt(self) -> int:
        t = self.x
        t = numpy.int32(t ^ (numpy.uint32(t) >> 2))
        self.x = numpy.int32(self.y)
        self.y = numpy.int32(self.z)
        self.z = numpy.int32(self.w)
        v0 = numpy.int32(self.v)
        self.w = numpy.int32(v0)
        t = (t ^ (t << 1)) ^ v0 ^ (v0 << 4)
        self.v = numpy.int32(t)
        self.addend += 362437
        return t + numpy.int32(self.addend)

    def nextInt(self, _from: int = Int_MIN_VALUE, until: int = Int_MAX_VALUE) -> numpy.int32:
        n = until - _from
        if n > 0 or n == Int_MIN_VALUE:
            if (n & -n) == n:
                assert False, "not implemented"
            else:
                v: int = 0
                while True:
                    bits = numpy.uint32(self._nextInt()) >> 1
                    v = bits % n
                    if bits - v + (n - 1) >= 0:
                        break
                return numpy.int32(_from + v)
        else:
            r = range(_from, until)
            while True:
                rnd = self._nextInt()
                if rnd in r:
                    return numpy.int32(rnd)

    def nextIntArray(self, size: int, _from: int = Int_MIN_VALUE, until: int = Int_MAX_VALUE) -> numpy.ndarray:
        zeros = numpy.zeros(size, dtype=numpy.int32)
        for i in range(0, size):
            zeros[i] = self.nextInt(_from=_from, until=until)
        return zeros


# interleaved uint8 HWC BGR to -> planar int32 CHW YIQ
def bgr2yiq(bgrimg: numpy.ndarray) -> numpy.ndarray:
    xp = cuda_utils.xp
    if cuda_utils.is_gpu_available():
        img = xp.asarray(bgrimg, dtype=xp.float32)
        planar = xp.transpose(img, (2, 0, 1))
        b, g, r = planar
        dY = 0.30 * r + 0.59 * g + 0.11 * b
        Y = (dY * 256).astype(xp.int32)
        I = (256 * (-0.27 * (b - dY) + 0.74 * (r - dY))).astype(xp.int32)
        Q = (256 * (0.41 * (b - dY) + 0.48 * (r - dY))).astype(xp.int32)
        return cuda_utils.to_cpu(xp.stack([Y, I, Q], axis=0).astype(xp.int32))
    planar = numpy.transpose(bgrimg, (2, 0, 1))
    b, g, r = planar.astype(numpy.float32)
    dY = 0.30 * r + 0.59 * g + 0.11 * b
    Y = (dY * 256).astype(numpy.int32)
    I = (256 * (-0.27 * (b - dY) + 0.74 * (r - dY))).astype(numpy.int32)
    Q = (256 * (0.41 * (b - dY) + 0.48 * (r - dY))).astype(numpy.int32)
    return numpy.stack([Y, I, Q], axis=0).astype(numpy.int32)


# one field of planar int32 CHW YIQ -> one field of interleaved uint8 HWC BGR to
def yiq2bgr(yiq: numpy.ndarray, dst_bgr: numpy.ndarray = None, field: int = 0) -> numpy.ndarray:
    c, h, w = yiq.shape
    dst_bgr = dst_bgr if dst_bgr is not None else numpy.zeros((h, w, c))
    xp = cuda_utils.xp
    if cuda_utils.is_gpu_available():
        Y_g, I_g, Q_g = xp.asarray(yiq[0]), xp.asarray(yiq[1]), xp.asarray(yiq[2])
        if field == 0:
            Y_g, I_g, Q_g = Y_g[::2], I_g[::2], Q_g[::2]
        else:
            Y_g, I_g, Q_g = Y_g[1::2], I_g[1::2], Q_g[1::2]
        r = ((1.000 * Y_g + 0.956 * I_g + 0.621 * Q_g) / 256).astype(xp.int32)
        g = ((1.000 * Y_g + -0.272 * I_g + -0.647 * Q_g) / 256).astype(xp.int32)
        b = ((1.000 * Y_g + -1.106 * I_g + 1.703 * Q_g) / 256).astype(xp.int32)
        r = xp.clip(r, 0, 255)
        g = xp.clip(g, 0, 255)
        b = xp.clip(b, 0, 255)
        planarBGR = cuda_utils.to_cpu(xp.stack([b, g, r]))
        interleavedBGR = numpy.transpose(planarBGR, (1, 2, 0))
        if field == 0:
            dst_bgr[::2] = interleavedBGR
        else:
            dst_bgr[1::2] = interleavedBGR
        return dst_bgr
    Y, I, Q = yiq
    if field == 0:
        Y, I, Q = Y[::2], I[::2], Q[::2]
    else:
        Y, I, Q = Y[1::2], I[1::2], Q[1::2]

    r = ((1.000 * Y + 0.956 * I + 0.621 * Q) / 256).astype(numpy.int32)
    g = ((1.000 * Y + -0.272 * I + -0.647 * Q) / 256).astype(numpy.int32)
    b = ((1.000 * Y + -1.106 * I + 1.703 * Q) / 256).astype(numpy.int32)
    r = numpy.clip(r, 0, 255)
    g = numpy.clip(g, 0, 255)
    b = numpy.clip(b, 0, 255)
    planarBGR = numpy.stack([b, g, r])
    interleavedBGR = numpy.transpose(planarBGR, (1, 2, 0))
    if field == 0:
        dst_bgr[::2] = interleavedBGR
    else:
        dst_bgr[1::2] = interleavedBGR
    return dst_bgr


class LowpassFilter:
    def __init__(self, rate: float, hz: float, value: float = 0.0):
        self.timeInterval: float = 1.0 / rate
        self.tau: float = 1 / (hz * 2.0 * M_PI)
        self.alpha: float = self.timeInterval / (self.tau + self.timeInterval)
        self.prev: float = value

    def lowpass(self, sample: float) -> float:
        stage1 = sample * self.alpha
        stage2 = self.prev - self.prev * self.alpha
        self.prev = stage1 + stage2
        return self.prev

    def highpass(self, sample: float) -> float:
        stage1 = sample * self.alpha
        stage2 = self.prev - self.prev * self.alpha
        self.prev = stage1 + stage2
        return sample - self.prev

    def lowpass_array(self, samples: numpy.ndarray) -> numpy.ndarray:
        if self.prev == 0.0:
            return lfilter([self.alpha], [1, -(1.0 - self.alpha)], samples)
        else:
            ic = scipy.signal.lfiltic([self.alpha], [1, -(1.0 - self.alpha)], [self.prev])
            return lfilter([self.alpha], [1, -(1.0 - self.alpha)], samples, zi=ic)[0]

    def highpass_array(self, samples: numpy.ndarray) -> numpy.ndarray:
        f = self.lowpass_array(samples)
        return samples - f


def _apply_lfilter_3stage(rows: numpy.ndarray, alpha: float, reset: float = 0.0) -> numpy.ndarray:
    """Apply 3-stage IIR lowpass filter to all rows simultaneously (vectorized).

    Processes every scanline at once using scipy.signal.lfilter with axis=1,
    replacing the original per-scanline Python loop for a significant speedup.

    Args:
        rows: 2D array (n_scanlines, n_pixels)
        alpha: IIR filter coefficient
        reset: Initial filter state value (0.0 means zero initial conditions)

    Returns:
        Filtered array, same shape as rows, dtype float64
    """
    b = [alpha]
    a = [1.0, -(1.0 - alpha)]
    data = rows.astype(numpy.float64)
    if reset == 0.0:
        result = lfilter(b, a, data, axis=1)
        result = lfilter(b, a, result, axis=1)
        result = lfilter(b, a, result, axis=1)
    else:
        # Each row gets the same initial condition zi
        zi_1d = scipy.signal.lfiltic(b, a, [float(reset)])  # shape (1,)
        n_rows = rows.shape[0]
        zi = numpy.tile(zi_1d[None, :], (n_rows, 1))  # (n_rows, 1)
        result, _ = lfilter(b, a, data, axis=1, zi=zi)
        zi = numpy.tile(zi_1d[None, :], (n_rows, 1))
        result, _ = lfilter(b, a, result, axis=1, zi=zi)
        zi = numpy.tile(zi_1d[None, :], (n_rows, 1))
        result, _ = lfilter(b, a, result, axis=1, zi=zi)
    return result


def cut_black_line_border(image: numpy.ndarray, bordersize: int = None) -> None:
    h, w, _ = image.shape
    if bordersize is None:
        line_width = int(w * 0.017)  # 1.7%
    else:
        line_width = bordersize  # TODO: value to settings

    image[:, -1*line_width:] = 0  # 0 set to black


def composite_lowpass(yiq: numpy.ndarray, field: int, fieldno: int):
    _, height, width = yiq.shape
    fY, fI, fQ = yiq
    for p in range(1, 3):
        cutoff = 1300000.0 if p == 1 else 600000.0
        delay = 2 if (p == 1) else 4
        P = fI if (p == 1) else fQ
        P_field = P[field::2]
        # Vectorized: process all scanlines at once (reset=0.0 → no initial condition)
        alpha = lowpassFilters(cutoff, reset=0.0)[0].alpha
        result = _apply_lfilter_3stage(P_field, alpha, reset=0.0)
        P_field[:, 0:width - delay] = result.astype(numpy.int32)[:, delay:]


# lighter-weight filtering, probably what your old CRT does to reduce color fringes a bit
def composite_lowpass_tv(yiq: numpy.ndarray, field: int, fieldno: int):
    _, height, width = yiq.shape
    fY, fI, fQ = yiq
    delay = 1
    alpha = lowpassFilters(2600000.0, reset=0.0)[0].alpha
    for p in range(1, 3):
        P = fI if (p == 1) else fQ
        P_field = P[field::2]
        # Vectorized: process all scanlines at once
        result = _apply_lfilter_3stage(P_field, alpha, reset=0.0)
        P_field[:, 0:width - delay] = result.astype(numpy.int32)[:, delay:]


def composite_preemphasis(yiq: numpy.ndarray, field: int, composite_preemphasis: float,
                          composite_preemphasis_cut: float):
    fY, fI, fQ = yiq
    pre = LowpassFilter(Ntsc.NTSC_RATE, composite_preemphasis_cut, 16.0)
    rows = fY[field::2]
    # Vectorized: single-stage highpass for all scanlines at once
    alpha = pre.alpha
    b = [alpha]
    a = [1.0, -(1.0 - alpha)]
    data = rows.astype(numpy.float64)
    # reset=16.0 → initial condition for all rows
    zi_1d = scipy.signal.lfiltic(b, a, [16.0])
    n_rows = rows.shape[0]
    zi = numpy.tile(zi_1d[None, :], (n_rows, 1))  # (n_rows, 1)
    lp, _ = lfilter(b, a, data, axis=1, zi=zi)
    highpass = data - lp
    fY[field::2] = (data + highpass * composite_preemphasis).astype(numpy.int32)


class VHSSpeed(Enum):
    VHS_SP = (2400000.0, 320000.0, 9)
    VHS_LP = (1900000.0, 300000.0, 12)
    VHS_EP = (1400000.0, 280000.0, 14)

    def __init__(self, luma_cut: float, chroma_cut: float, chroma_delay: int):
        self.luma_cut = luma_cut
        self.chroma_cut = chroma_cut
        self.chroma_delay = chroma_delay


class Ntsc:
    # https://en.wikipedia.org/wiki/NTSC
    NTSC_RATE = 315000000.00 / 88 * 4  # 315/88 Mhz rate * 4

    def __init__(self, precise=False, random=None):
        self.precise = precise
        self.random = random if random is not None else XorWowRandom(31374242, 0)
        self._composite_preemphasis_cut = 1000000.0
        # analog artifacts related to anything that affects the raw composite signal i.e. CATV modulation
        self._composite_preemphasis = 0.0  # values 0..8 look realistic

        self._vhs_out_sharpen = 1.5  # 1.0..5.0

        self._vhs_edge_wave = 0  # 0..10

        self._vhs_head_switching = False  # turn this on only on frames height 486 pixels or more
        self._head_switching_speed = 0  # 0..100 this is /1000 increment for _vhs_head_switching_point 0 is static
        self._vhs_head_switching_point = 1.0 - (4.5 + 0.01) / 262.5  # 4 scanlines NTSC up from vsync
        self._vhs_head_switching_phase = (1.0 - 0.01) / 262.5  # 4 scanlines NTSC up from vsync
        self._vhs_head_switching_phase_noise = 1.0 / 500 / 262.5  # 1/500th of a scanline

        self._color_bleed_before = True  # color bleed comes before other degradations if True or after otherwise
        self._color_bleed_horiz = 0  # horizontal color bleeding 0 = no color bleed, 1..10 sane values
        self._color_bleed_vert = 0  # vertical color bleeding  0 = no color bleed, 1..10 sane values
        self._ringing = 1.0  # 1 = no ringing, 0.3..0.99 = sane values
        self._enable_ringing2 = False
        self._ringing_power = 2
        self._ringing_shift = 0
        self._freq_noise_size = 0  # (0-1) optimal values  is 0.5..0.99 if noiseSize=0 - no noise
        self._freq_noise_amplitude = 2  # noise amplitude  (0-5) optimal values  is 0.5-2
        self._composite_in_chroma_lowpass = True  # apply chroma lowpass before composite encode
        self._composite_out_chroma_lowpass = True
        self._composite_out_chroma_lowpass_lite = True

        self._video_chroma_noise = 0  # 0..16384
        self._video_chroma_phase_noise = 0  # 0..50
        self._video_chroma_loss = 0  # 0..100_000
        self._video_noise = 2  # 0..4200
        self._subcarrier_amplitude = 50
        self._subcarrier_amplitude_back = 50
        self._emulating_vhs = False
        self._nocolor_subcarrier = False  # if set, emulate subcarrier but do not decode back to color (debug)
        self._vhs_chroma_vert_blend = True  # if set, and VHS, blend vertically the chroma scanlines (as the VHS format does)
        self._vhs_svideo_out = False  # if not set, and VHS, video is recombined as if composite out on VCR

        self._output_ntsc = True  # NTSC color subcarrier emulation
        self._video_scanline_phase_shift = 180
        self._video_scanline_phase_shift_offset = 0  # 0..4
        self._output_vhs_tape_speed = VHSSpeed.VHS_SP

        self._black_line_cut = False  # Add black line glitch (credits to @rgm89git)

    def rand(self) -> numpy.int32:
        return self.random.nextInt(_from=0)

    def rand_array(self, size: int) -> numpy.ndarray:
        return self.random.nextIntArray(size, 0, Int_MAX_VALUE)

    def video_noise(self, yiq: numpy.ndarray, field: int, video_noise: int):
        _, height, width = yiq.shape
        fY, fI, fQ = yiq
        noise_mod = video_noise * 2 + 1
        fields = fY[field::2]
        fh, fw = fields.shape
        if not self.precise:  # this one works FAST
            lp = LowpassFilter(1, 1, 0)
            lp.alpha = 0.5
            rnds = self.rand_array(fw * fh) % noise_mod - video_noise
            noises = shift(lp.lowpass_array(rnds).astype(numpy.int32), 1)
            fields += noises.reshape(fields.shape)
        else:  # this one works EXACTLY like original code
            noise = 0
            for field1 in fields:
                rnds = self.rand_array(fw) % noise_mod - video_noise
                for x in range(0, fw):
                    field1[x] += noise
                    noise += rnds[x]
                    noise = int(noise / 2)

    # https://bavc.github.io/avaa/artifacts/chrominance_noise.html
    def video_chroma_noise(self, yiq: numpy.ndarray, field: int, video_chroma_noise: int):
        _, height, width = yiq.shape
        fY, fI, fQ = yiq

        noise_mod = video_chroma_noise * 2 + 1
        U = fI[field::2]
        V = fQ[field::2]
        fh, fw = U.shape
        if not self.precise:
            lp = LowpassFilter(1, 1, 0)
            lp.alpha = 0.5
            rndsU = self.rand_array(fw * fh) % noise_mod - video_chroma_noise
            noisesU = shift(lp.lowpass_array(rndsU).astype(numpy.int32), 1)

            rndsV = self.rand_array(fw * fh) % noise_mod - video_chroma_noise
            noisesV = shift(lp.lowpass_array(rndsV).astype(numpy.int32), 1)

            U += noisesU.reshape(U.shape)
            V += noisesV.reshape(V.shape)
        else:
            noiseU = 0
            noiseV = 0
            for y in range(0, fh):
                for x in range(0, fw):
                    U[y][x] += noiseU
                    noiseU += self.rand() % noise_mod - video_chroma_noise
                    noiseU = int(noiseU / 2)

                    V[y][x] += noiseV
                    noiseV += self.rand() % noise_mod - video_chroma_noise
                    noiseV = int(noiseV / 2)

    def video_chroma_phase_noise(self, yiq: numpy.ndarray, field: int, video_chroma_phase_noise: int):
        _, height, width = yiq.shape
        fY, fI, fQ = yiq
        noise_mod = video_chroma_phase_noise * 2 + 1
        U = fI[field::2]
        V = fQ[field::2]
        fh, fw = U.shape
        # Pre-compute all per-scanline noise values (sequential dependency)
        noises = numpy.empty(fh, dtype=numpy.float64)
        noise = 0
        for y in range(fh):
            noise += self.rand() % noise_mod - video_chroma_phase_noise
            noise = int(noise / 2)
            noises[y] = noise
        # Vectorized rotation applied to all scanlines at once
        pi_vals = noises * (M_PI / 100.0)
        sinpi = numpy.sin(pi_vals)   # (fh,)
        cospi = numpy.cos(pi_vals)   # (fh,)
        # Broadcast (fh,) → (fh, 1) for element-wise ops with (fh, fw) arrays
        new_u = U * cospi[:, None] - V * sinpi[:, None]
        new_v = U * sinpi[:, None] + V * cospi[:, None]
        fI[field::2] = new_u
        fQ[field::2] = new_v

    def vhs_head_switching(self, yiq: numpy.ndarray, field: int = 0):
        _, height, width = yiq.shape
        fY, fI, fQ = yiq
        twidth = width + width // 10
        shy = 0
        noise = 0.0
        if self._vhs_head_switching_phase_noise != 0.0:
            x = numpy.int32(random.randint(1, 2000000000))
            noise = x / 1000000000.0 - 1.0
            noise *= self._vhs_head_switching_phase_noise

        t = twidth * (262.5 if self._output_ntsc else 312.5)
        p = int(fmod(self._vhs_head_switching_point + noise, 1.0) * t)
        self._vhs_head_switching_point += self._head_switching_speed/1000
        y = int(p // twidth * 2) + field
        p = int(fmod(self._vhs_head_switching_phase + noise, 1.0) * t)
        x = p % twidth
        y -= (262 - 240) * 2 if self._output_ntsc else (312 - 288) * 2
        tx = x
        ishif = x - twidth if x >= twidth // 2 else x
        shif = 0
        while y < height:
            if y >= 0:
                Y = fY[y]
                if shif != 0:
                    tmp = numpy.zeros(twidth)
                    x2 = (tx + twidth + shif) % twidth
                    tmp[:width] = Y

                    x = tx
                    while x < width:
                        Y[x] = tmp[x2]
                        x2 += 1
                        if x2 == twidth:
                            x2 = 0
                        x += 1

            shif = ishif if shy == 0 else int(shif * 7 / 8)
            tx = 0
            y += 2
            shy += 1

    _Umult = numpy.array([1, 0, -1, 0], dtype=numpy.int32)
    _Vmult = numpy.array([0, 1, 0, -1], dtype=numpy.int32)

    def _chroma_luma_xi(self, fieldno: int, y: int):
        if self._video_scanline_phase_shift == 90:
            return int(fieldno + self._video_scanline_phase_shift_offset + (y >> 1)) & 3
        elif self._video_scanline_phase_shift == 180:
            return int(((((fieldno + y) & 2) + self._video_scanline_phase_shift_offset) & 3))
        elif self._video_scanline_phase_shift == 270:
            return int(((fieldno + self._video_scanline_phase_shift_offset) & 3))
        else:
            return int(self._video_scanline_phase_shift_offset & 3)

    def chroma_into_luma(self, yiq: numpy.ndarray, field: int, fieldno: int, subcarrier_amplitude: int):
        _, height, width = yiq.shape
        fY, fI, fQ = yiq
        y = field
        umult = numpy.tile(Ntsc._Umult, int((width / 4) + 1))
        vmult = numpy.tile(Ntsc._Vmult, int((width / 4) + 1))
        while y < height:
            Y = fY[y]
            I = fI[y]
            Q = fQ[y]
            xi = self._chroma_luma_xi(fieldno, y)

            chroma = I * subcarrier_amplitude * umult[xi:xi + width]
            chroma += Q * subcarrier_amplitude * vmult[xi:xi + width]
            Y[:] = Y + chroma.astype(numpy.int32) // 50
            I[:] = 0
            Q[:] = 0
            y += 2

    def chroma_from_luma(self, yiq: numpy.ndarray, field: int, fieldno: int, subcarrier_amplitude: int):
        _, height, width = yiq.shape
        fY, fI, fQ = yiq
        rows_Y = fY[field::2]
        rows_I = fI[field::2]
        rows_Q = fQ[field::2]

        # Build y2 (Y shifted left 2) and yd4 (Y shifted right 2) for all rows at once
        y2 = numpy.zeros_like(rows_Y)
        y2[:, :-2] = rows_Y[:, 2:]
        yd4 = numpy.zeros_like(rows_Y)
        yd4[:, 2:] = rows_Y[:, :-2]

        # Prefix-sum accumulation (vectorized over all rows)
        row_init = (rows_Y[:, 0] + rows_Y[:, 1]).astype(numpy.int32)
        sums = (y2 - yd4).astype(numpy.int32)
        sums0 = numpy.concatenate([row_init[:, None], sums], axis=1)
        acc = numpy.cumsum(sums0, axis=1)[:, 1:]
        acc4 = acc // 4
        chroma_all = (y2 - acc4).astype(numpy.int32)
        fY[field::2] = acc4

        # Compute xi for each scanline (small loop over unique phase values)
        y_vals = numpy.arange(field, height, 2)
        xi_vals = numpy.array(
            [self._chroma_luma_xi(fieldno, int(y)) for y in y_vals],
            dtype=numpy.int32,
        )

        # Sign flip: flip positions (x+2)%4 and (x+3)%4 where x = (4 - xi) & 3
        x_vals = (4 - xi_vals) & 3
        col_idx = numpy.arange(width, dtype=numpy.int32)
        col_phase = col_idx % 4
        phase2 = (x_vals[:, None] + 2) % 4
        phase3 = (x_vals[:, None] + 3) % 4
        flip = (col_phase[None, :] == phase2) | (col_phase[None, :] == phase3)
        chroma_all[flip] *= -1

        # Scale
        chroma_scaled = (chroma_all * (50.0 / subcarrier_amplitude))

        # Decode I and Q — group rows by xi value (only 4 possible values)
        half_w = width // 2
        for xi in range(4):
            row_mask = xi_vals == xi
            if not numpy.any(row_mask):
                continue
            ch = chroma_scaled[row_mask]
            s_i = (-ch[:, xi::2]).astype(numpy.int32)
            s_q = (-ch[:, xi + 1::2]).astype(numpy.int32)
            buf_i = numpy.zeros((s_i.shape[0], half_w), dtype=numpy.int32)
            buf_q = numpy.zeros((s_q.shape[0], half_w), dtype=numpy.int32)
            buf_i[:, :s_i.shape[1]] = s_i
            buf_q[:, :s_q.shape[1]] = s_q
            rows_I[row_mask, ::2] = buf_i
            rows_Q[row_mask, ::2] = buf_q

        # Interpolate odd pixels and zero out last two columns
        rows_I[:, 1:width - 2:2] = (rows_I[:, :width - 2:2] + rows_I[:, 2::2]) >> 1
        rows_Q[:, 1:width - 2:2] = (rows_Q[:, :width - 2:2] + rows_Q[:, 2::2]) >> 1
        rows_I[:, width - 2:] = 0
        rows_Q[:, width - 2:] = 0

    def vhs_luma_lowpass(self, yiq: numpy.ndarray, field: int, luma_cut: float):
        fY = yiq[0]
        rows = fY[field::2]
        lp = lowpassFilters(cutoff=luma_cut, reset=16.0)
        alpha = lp[0].alpha
        # Vectorized 3-stage lowpass for all scanlines at once
        f2 = _apply_lfilter_3stage(rows, alpha, reset=16.0)
        # Sharpening: highpass = f2 - lowpass(f2); pre uses same alpha and reset
        b = [alpha]
        a = [1.0, -(1.0 - alpha)]
        zi_1d = scipy.signal.lfiltic(b, a, [16.0])
        n_rows = rows.shape[0]
        zi = numpy.tile(zi_1d[None, :], (n_rows, 1))
        lp_f2, _ = lfilter(b, a, f2, axis=1, zi=zi)
        highpass = f2 - lp_f2
        fY[field::2] = (f2 + highpass * 1.6).astype(numpy.int32)

    def vhs_chroma_lowpass(self, yiq: numpy.ndarray, field: int, chroma_cut: float, chroma_delay: int):
        _, height, width = yiq.shape
        fY, fI, fQ = yiq
        alpha = lowpassFilters(cutoff=chroma_cut, reset=0.0)[0].alpha
        # Vectorized: process all chroma scanlines at once for both U and V
        for P in (fI, fQ):
            rows = P[field::2]
            result = _apply_lfilter_3stage(rows, alpha, reset=0.0)
            P[field::2, :width - chroma_delay] = result.astype(numpy.int32)[:, chroma_delay:]

    # VHS decks also vertically smear the chroma subcarrier using a delay line
    # to add the previous line's color subcarrier to the current line's color subcarrier.
    # note that phase changes in NTSC are compensated for by the VHS deck to make the
    # phase line up per scanline (else summing the previous line's carrier would
    # cancel it out).
    def vhs_chroma_vert_blend(self, yiq: numpy.ndarray, field: int):
        _, height, width = yiq.shape
        fY, fI, fQ = yiq
        U2 = fI[field + 2::2, ]
        V2 = fQ[field + 2::2, ]
        delayU = numpy.pad(U2[:-1, ], [[1, 0], [0, 0]])
        delayV = numpy.pad(V2[:-1, ], [[1, 0], [0, 0]])
        fI[field + 2::2, ] = (delayU + U2 + 1) >> 1
        fQ[field + 2::2, ] = (delayV + V2 + 1) >> 1

    def vhs_sharpen(self, yiq: numpy.ndarray, field: int, luma_cut: float):
        fY = yiq[0]
        rows = fY[field::2]
        alpha = lowpassFilters(cutoff=luma_cut * 4, reset=0.0)[0].alpha
        # Vectorized: all scanlines at once
        ts = _apply_lfilter_3stage(rows, alpha, reset=0.0)
        fY[field::2] = (rows + (rows.astype(numpy.float64) - ts) * self._vhs_out_sharpen * 2.0).astype(numpy.int32)

    # http://www.michaeldvd.com.au/Articles/VideoArtefacts/VideoArtefactsColourBleeding.html
    # https://bavc.github.io/avaa/artifacts/yc_delay_error.html
    def color_bleed(self, yiq: numpy.ndarray, field: int):
        _, height, width = yiq.shape
        fY, fI, fQ = yiq

        field_ = fI[field::2]
        h, w = field_.shape
        fI[field::2] = numpy.pad(field_, ((self._color_bleed_vert, 0), (self._color_bleed_horiz, 0)))[0:h, 0:w]

        field_ = fQ[field::2]
        h, w = field_.shape
        fQ[field::2] = numpy.pad(field_, ((self._color_bleed_vert, 0), (self._color_bleed_horiz, 0)))[0:h, 0:w]

    def vhs_edge_wave(self, yiq: numpy.ndarray, field: int):
        _, height, width = yiq.shape
        fY, fI, fQ = yiq
        rnds = self.random.nextIntArray(height // 2, 0, self._vhs_edge_wave)
        lp = LowpassFilter(Ntsc.NTSC_RATE, self._output_vhs_tape_speed.luma_cut,
                           0)  # no real purpose to initialize it with ntsc values
        rnds = lp.lowpass_array(rnds).astype(numpy.int32)

        for y, Y in enumerate(fY[field::2]):
            if rnds[y] != 0:
                shift = rnds[y]
                Y[:] = numpy.pad(Y, (shift, 0))[:-shift]
        for y, I in enumerate(fI[field::2]):
            if rnds[y] != 0:
                shift = rnds[y]
                I[:] = numpy.pad(I, (shift, 0))[:-shift]
        for y, Q in enumerate(fQ[field::2]):
            if rnds[y] != 0:
                shift = rnds[y]
                Q[:] = numpy.pad(Q, (shift, 0))[:-shift]

    def vhs_chroma_loss(self, yiq: numpy.ndarray, field: int, video_chroma_loss: int):
        _, height, width = yiq.shape
        fY, fI, fQ = yiq
        for y in range(field, height, 2):
            U = fI[y]
            V = fQ[y]
            if self.rand() % 100000 < video_chroma_loss:
                U[:] = 0
                V[:] = 0

    def emulate_vhs(self, yiq: numpy.ndarray, field: int, fieldno: int):
        vhs_speed = self._output_vhs_tape_speed
        if self._vhs_edge_wave != 0:
            self.vhs_edge_wave(yiq, field)

        self.vhs_luma_lowpass(yiq, field, vhs_speed.luma_cut)

        self.vhs_chroma_lowpass(yiq, field, vhs_speed.chroma_cut, vhs_speed.chroma_delay)

        if self._vhs_chroma_vert_blend and self._output_ntsc:
            self.vhs_chroma_vert_blend(yiq, field)

        if True:  # TODO: make option
            self.vhs_sharpen(yiq, field, vhs_speed.luma_cut)

        if not self._vhs_svideo_out:
            self.chroma_into_luma(yiq, field, fieldno, self._subcarrier_amplitude)
            self.chroma_from_luma(yiq, field, fieldno, self._subcarrier_amplitude)

    def composite_layer(self, dst: numpy.ndarray, src: numpy.ndarray, field: int, fieldno: int):
        assert dst.shape == src.shape, "dst and src images must be of same shape"

        if self._black_line_cut:
            cut_black_line_border(src)

        yiq = bgr2yiq(src)
        if self._color_bleed_before and (self._color_bleed_vert != 0 or self._color_bleed_horiz != 0):
            self.color_bleed(yiq, field)

        if self._composite_in_chroma_lowpass:
            composite_lowpass(yiq, field, fieldno)

        if self._ringing != 1.0:
            self.ringing(yiq, field)

        self.chroma_into_luma(yiq, field, fieldno, self._subcarrier_amplitude)

        if self._composite_preemphasis != 0.0 and self._composite_preemphasis_cut > 0:
            composite_preemphasis(yiq, field, self._composite_preemphasis, self._composite_preemphasis_cut)

        if self._video_noise != 0:
            self.video_noise(yiq, field, self._video_noise)

        if self._vhs_head_switching:
            self.vhs_head_switching(yiq, field)

        if not self._nocolor_subcarrier:
            self.chroma_from_luma(yiq, field, fieldno, self._subcarrier_amplitude_back)

        if self._video_chroma_noise != 0:
            self.video_chroma_noise(yiq, field, self._video_chroma_noise)

        if self._video_chroma_phase_noise != 0:
            self.video_chroma_phase_noise(yiq, field, self._video_chroma_phase_noise)

        if self._emulating_vhs:
            self.emulate_vhs(yiq, field, fieldno)

        if self._video_chroma_loss != 0:
            self.vhs_chroma_loss(yiq, field, self._video_chroma_loss)

        if self._composite_out_chroma_lowpass:
            if self._composite_out_chroma_lowpass_lite:
                composite_lowpass_tv(yiq, field, fieldno)
            else:
                composite_lowpass(yiq, field, fieldno)

        if not self._color_bleed_before and (self._color_bleed_vert != 0 or self._color_bleed_horiz != 0):
            self.color_bleed(yiq, field)

        # if self._ringing != 1.0:
        #     self.ringing(yiq, field)

        Y, I, Q = yiq

        # simulate 2x less bandwidth for chroma components, just like yuv420
        I[field::2] = self._blur_chroma(I[field::2])
        Q[field::2] = self._blur_chroma(Q[field::2])

        return yiq2bgr(yiq)

    def _blur_chroma(self, chroma: numpy.ndarray) -> numpy.ndarray:
        h, w = chroma.shape
        down2 = cv2.resize(chroma.astype(numpy.float32), (w // 2, h // 2), interpolation=cv2.INTER_LANCZOS4)
        return cv2.resize(down2, (w, h), interpolation=cv2.INTER_LANCZOS4).astype(numpy.int32)

    def ringing(self, yiq: numpy.ndarray, field: int):
        Y, I, Q = yiq
        sz = self._freq_noise_size
        amp = self._freq_noise_amplitude
        shift = self._ringing_shift
        if not self._enable_ringing2:
            Y[field::2] = ringing(Y[field::2], self._ringing, noiseSize=sz, noiseValue=amp, clip=False)
            I[field::2] = ringing(I[field::2], self._ringing, noiseSize=sz, noiseValue=amp, clip=False)
            Q[field::2] = ringing(Q[field::2], self._ringing, noiseSize=sz, noiseValue=amp, clip=False)
        else:
            Y[field::2] = ringing2(Y[field::2], power=self._ringing_power, shift=shift, clip=False)
            I[field::2] = ringing2(I[field::2], power=self._ringing_power, shift=shift, clip=False)
            Q[field::2] = ringing2(Q[field::2], power=self._ringing_power, shift=shift, clip=False)


def random_ntsc(seed=None) -> Ntsc:
    rnd = random.Random(seed)
    ntsc = Ntsc(random=NumpyRandom(seed))
    ntsc._composite_preemphasis = rnd.triangular(0, 8, 0)
    ntsc._vhs_out_sharpen = rnd.triangular(1, 5, 1.5)
    ntsc._composite_in_chroma_lowpass = rnd.random() < 0.8  # lean towards default value
    ntsc._composite_out_chroma_lowpass = rnd.random() < 0.8  # lean towards default value
    ntsc._composite_out_chroma_lowpass_lite = rnd.random() < 0.8  # lean towards default value
    ntsc._video_chroma_noise = int(rnd.triangular(0, 16384, 2))
    ntsc._video_chroma_phase_noise = int(rnd.triangular(0, 50, 2))
    ntsc._video_chroma_loss = int(rnd.triangular(0, 800, 10))
    ntsc._video_noise = int(rnd.triangular(0, 4200, 2))
    ntsc._emulating_vhs = rnd.random() < 0.2  # lean towards default value
    ntsc._vhs_edge_wave = int(rnd.triangular(0, 5, 0))
    ntsc._video_scanline_phase_shift = rnd.choice([0, 90, 180, 270])
    ntsc._video_scanline_phase_shift_offset = rnd.randint(0, 3)
    ntsc._output_vhs_tape_speed = rnd.choice([VHSSpeed.VHS_SP, VHSSpeed.VHS_LP, VHSSpeed.VHS_EP])
    enable_ringing = rnd.random() < 0.8
    if enable_ringing:
        ntsc._ringing = rnd.uniform(0.3, 0.7)
        enable_freq_noise = rnd.random() < 0.8
        if enable_freq_noise:
            ntsc._freq_noise_size = rnd.uniform(0.5, 0.99)
            ntsc._freq_noise_amplitude = rnd.uniform(0.5, 2.0)
        ntsc._enable_ringing2 = rnd.random() < 0.5
        ntsc._ringing_power = rnd.randint(2, 7)
    ntsc._color_bleed_before = 1 == rnd.randint(0, 1)
    ntsc._color_bleed_horiz = int(rnd.triangular(0, 8, 0))
    ntsc._color_bleed_vert = int(rnd.triangular(0, 8, 0))
    return ntsc


def lowpassFilters(cutoff: float, reset: float, rate: float = Ntsc.NTSC_RATE) -> List[LowpassFilter]:
    return [LowpassFilter(rate, cutoff, reset) for x in range(0, 3)]