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

physics_dco_pn_template:
    Build (freqs, levels) corner-point arrays from a physics-style
    parameterisation: white floor + 1/f^2 (thermal) + 1/f^3 (flicker)
    with explicit corner frequencies. Easier to teach with than the
    raw 6-corner template.
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


def physics_dco_pn_template(L_1MHz_dbchz: float = -120.0,
                            flicker_corner_hz: float = 100e3,
                            thermal_floor_dbchz: float = -150.0,
                            n_points: int = 30,
                            f_min_hz: float = 100.0,
                            f_max_hz: float = 100e6):
    """Three-region L(f): 1/f^3 (flicker) + 1/f^2 (thermal) + white floor.

    Anchored so that L(1 MHz) equals L_1MHz_dbchz (the standard data-sheet
    quote), with the 1/f^3 -> 1/f^2 transition at `flicker_corner_hz`
    and a flat thermal floor at `thermal_floor_dbchz` at high offsets.

    Returns (freqs_hz, levels_dbchz) suitable to drop into
    PLLParams.dco_pn_freqs_hz / .dco_pn_levels_dbchz.
    """
    f = np.geomspace(f_min_hz, f_max_hz, n_points)
    # 1/f^2 part: anchor at 1 MHz with given level
    S_thermal = 10.0 ** (L_1MHz_dbchz / 10.0) * (1e6 / f) ** 2
    # 1/f^3 part: connect to 1/f^2 at the flicker corner
    L_at_corner = L_1MHz_dbchz + 20.0 * np.log10(1e6 / flicker_corner_hz)
    S_flicker = 10.0 ** (L_at_corner / 10.0) * (flicker_corner_hz / f) ** 3
    # White floor
    S_floor = 10.0 ** (thermal_floor_dbchz / 10.0) * np.ones_like(f)
    # Total (each region's L stored as power); take the sum
    S_total = S_thermal + S_flicker + S_floor
    L_db = 10.0 * np.log10(S_total)
    return tuple(f.tolist()), tuple(L_db.tolist())


def physics_ref_pn_template(L_10kHz_dbchz: float = -150.0,
                            corner_hz: float = 10e3,
                            floor_dbchz: float = -160.0,
                            n_points: int = 20,
                            f_min_hz: float = 10.0,
                            f_max_hz: float = 20e6):
    """Crystal-oscillator-style template: 1/f^2 + white floor.

    Anchored at L(10 kHz) and rolls off as 1/f^2 below `corner_hz`,
    flattens at `floor_dbchz` above.
    """
    f = np.geomspace(f_min_hz, f_max_hz, n_points)
    S_main = 10.0 ** (L_10kHz_dbchz / 10.0) * (10e3 / f) ** 2
    # Bend the 1/f^2 slope so it doesn't go to +inf at low f: cap at
    # a value 30 dB above L at corner
    cap = 10.0 ** ((L_10kHz_dbchz + 30.0) / 10.0)
    S_main = np.minimum(S_main, cap)
    S_floor = 10.0 ** (floor_dbchz / 10.0) * np.ones_like(f)
    L_db = 10.0 * np.log10(S_main + S_floor)
    # Mask region above corner: stay near the floor
    _ = corner_hz
    return tuple(f.tolist()), tuple(L_db.tolist())
