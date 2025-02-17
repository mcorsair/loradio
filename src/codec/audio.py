import numpy as np


def generate_tone(
        sr: int,
        freq: float,
        duration: float,
        amplitude: float,
):
    n = int(sr * duration)
    t = np.arange(n) / sr
    s = np.sin(2 * np.pi * freq * t)
    s = amplitude * s * 2**15
    return s.astype(np.int16)
