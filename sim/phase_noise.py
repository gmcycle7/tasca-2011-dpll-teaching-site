"""Phase-noise utilities.

generate_pn_sequence:
    Synthesizes an excess-phase sequence phi_n[k] (rad) sampled at fs Hz
    whose one-sided SSB phase-noise PSD matches a target L(f) [dBc/Hz]
    specified at a handful of corner frequencies (log-log interpolation).

    L(f) is the single-sideband phase-noise spectrum in dBc/Hz, per the
    IEEE Std 1139 small-angle definition L(f) = S_phi_onesided(f) / 2.

estimate_psd:
    Welch estimate of L(f) from a sampled excess-phase sequence.
    Returns (f, L_dbchz) with f starting from > 0 (DC bin masked).
"""
import numpy as np
from scipy import signal


def generate_pn_sequence(n_samples: int, fs: float,
                         freqs_hz, levels_dbchz, rng=None):
    """Generate phi_n[k] in rad with the target L(f) at sample rate fs."""
    if rng is None:
        rng = np.random.default_rng(0)
    freqs = np.asarray(freqs_hz, dtype=float)
    levels = np.asarray(levels_dbchz, dtype=float)

    f = np.fft.rfftfreq(n_samples, d=1.0 / fs)
    log_f = np.log10(np.clip(f, 1.0, None))
    L_db = np.interp(log_f, np.log10(freqs), levels,
                     left=levels[0], right=levels[-1])
    # S_phi (one-sided) = 2 * 10^(L/10)  [rad^2/Hz]
    S_phi = 2.0 * 10.0 ** (L_db / 10.0)
    S_phi[0] = 0.0

    # IRFFT amplitudes for a real signal with PSD S_phi
    amps = np.sqrt(S_phi * n_samples * fs / 2.0)
    phases = rng.uniform(0.0, 2.0 * np.pi, len(f))
    X = amps * np.exp(1j * phases)
    X[0] = 0.0
    if n_samples % 2 == 0:
        X[-1] = X[-1].real
    return np.fft.irfft(X, n=n_samples)


def estimate_psd(phi_excess_rad: np.ndarray, fs: float,
                 nperseg: int = None, window: str = "hann"):
    """Return (f, L_dbchz) using Welch on the excess-phase sequence."""
    n = len(phi_excess_rad)
    if nperseg is None:
        nperseg = min(n, 1 << 14)
    f, Pxx = signal.welch(phi_excess_rad, fs=fs, nperseg=nperseg,
                          window=window, scaling="density",
                          return_onesided=True, detrend="constant")
    # Pxx is the one-sided PSD in rad^2/Hz; L(f) = S_phi_onesided / 2.
    with np.errstate(divide="ignore"):
        L = 10.0 * np.log10(np.maximum(Pxx / 2.0, 1e-300))
    return f, L
