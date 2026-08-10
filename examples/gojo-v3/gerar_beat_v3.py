#!/usr/bin/env python3
"""Instrumental v3: trap cinematografico a 95 BPM, sem samples externos."""

from __future__ import annotations

import math
import wave
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "voz_v3" / "beat.wav"
SR = 48_000
BPM = 95.0
BEAT = 60.0 / BPM
BAR = BEAT * 4
DURATION = 30.0
N = round(DURATION * SR)
rng = np.random.default_rng(5160)
mix = np.zeros((N, 2), dtype=np.float64)


def add(sig: np.ndarray, at: float, gain: float = 1.0, pan: float = 0.0) -> None:
    pos = max(0, round(at * SR))
    if pos >= N:
        return
    if sig.ndim == 1:
        l = math.sqrt((1.0 - pan) / 2.0)
        r = math.sqrt((1.0 + pan) / 2.0)
        sig = np.column_stack((sig * l, sig * r))
    end = min(N, pos + len(sig))
    mix[pos:end] += sig[: end - pos] * gain


def adsr(t: np.ndarray, attack: float, release: float, decay: float = 0.0) -> np.ndarray:
    env = np.minimum(1.0, t / max(attack, 1e-5))
    if decay:
        env *= np.exp(-t * decay)
    env *= np.clip((t[-1] - t) / max(release, 1e-5), 0, 1)
    return env


def kick(dur: float = 0.38) -> np.ndarray:
    t = np.arange(round(dur * SR)) / SR
    freq = 43 + 128 * np.exp(-t * 31)
    phase = 2 * np.pi * np.cumsum(freq) / SR
    body = np.sin(phase) * np.exp(-t * 8.4)
    knock = 0.25 * np.sin(2 * np.pi * 118 * t) * np.exp(-t * 23)
    click = rng.normal(0, 1, len(t)) * np.exp(-t * 480) * 0.19
    return np.tanh((body + knock + click) * 1.85) * 0.95


def snare(dur: float = 0.34) -> np.ndarray:
    t = np.arange(round(dur * SR)) / SR
    noise = rng.normal(0, 1, len(t))
    noise = np.diff(np.r_[0.0, noise])
    tone = 0.42 * np.sin(2 * np.pi * 192 * t) + 0.19 * np.sin(2 * np.pi * 344 * t)
    tail = np.exp(-t * 15.5)
    return (0.34 * noise + tone) * tail


def clap(dur: float = 0.23) -> np.ndarray:
    t = np.arange(round(dur * SR)) / SR
    noise = np.diff(np.r_[0.0, rng.normal(0, 1, len(t))])
    env = np.zeros_like(t)
    for delay, amp in ((0.0, 1.0), (0.012, 0.78), (0.025, 0.56), (0.041, 0.34)):
        d = np.maximum(0, t - delay)
        env += amp * np.exp(-d * 36) * (t >= delay)
    return noise * env * 0.22


def hat(opened: bool = False) -> np.ndarray:
    dur = 0.17 if opened else 0.055
    t = np.arange(round(dur * SR)) / SR
    noise = rng.normal(0, 1, len(t))
    for _ in range(3):
        noise = np.diff(np.r_[0.0, noise])
    return noise * np.exp(-t * (19 if opened else 88)) * (0.060 if opened else 0.046)


def sub(freq: float, dur: float, glide: float = 1.0) -> np.ndarray:
    t = np.arange(round(dur * SR)) / SR
    f = freq * (glide + (1.0 - glide) * np.exp(-t * 8.5))
    phase = 2 * np.pi * np.cumsum(f) / SR
    sig = np.sin(phase) + 0.28 * np.sin(2 * phase) + 0.08 * np.sin(3 * phase)
    env = np.minimum(1.0, t / 0.012) * np.exp(-t / max(0.18, dur * 1.7))
    return np.tanh(sig * 1.32) * env * 0.62


def piano(freq: float, dur: float = 0.78) -> np.ndarray:
    t = np.arange(round(dur * SR)) / SR
    sig = np.zeros_like(t)
    for harmonic, amp, detune in ((1, 1.0, 0), (2, 0.46, 0.13), (3, 0.22, -0.19), (5, 0.09, 0.08)):
        sig += amp * np.sin(2 * np.pi * (freq * harmonic + detune) * t + 0.1 * harmonic)
    hammer = rng.normal(0, 1, len(t)) * np.exp(-t * 90) * 0.08
    return (sig / 1.77 + hammer) * adsr(t, 0.004, 0.13, 4.6) * 0.34


def glass(freq: float, dur: float = 0.48) -> np.ndarray:
    t = np.arange(round(dur * SR)) / SR
    sig = (
        np.sin(2 * np.pi * freq * t)
        + 0.38 * np.sin(2 * np.pi * freq * 2.006 * t)
        + 0.16 * np.sin(2 * np.pi * freq * 3.98 * t)
    )
    return sig * np.exp(-t * 7.5) * 0.17


def pad(freqs: tuple[float, ...], dur: float, strength: float) -> np.ndarray:
    t = np.arange(round(dur * SR)) / SR
    left = np.zeros_like(t)
    right = np.zeros_like(t)
    for f in freqs:
        for octave, amp in ((0.5, 0.35), (1.0, 1.0), (2.0, 0.18)):
            left += amp * np.sin(2 * np.pi * (f * octave - 0.43) * t + rng.uniform(0, 6.2))
            right += amp * np.sin(2 * np.pi * (f * octave + 0.43) * t + rng.uniform(0, 6.2))
    env = np.minimum(1, t / 0.55) * np.clip((dur - t) / 0.7, 0, 1)
    breath = 0.92 + 0.08 * np.sin(2 * np.pi * 0.36 * t)
    return np.column_stack((left, right)) / (len(freqs) * 1.53) * env[:, None] * breath[:, None] * strength


def riser(dur: float = 1.45) -> np.ndarray:
    t = np.arange(round(dur * SR)) / SR
    noise = rng.normal(0, 1, len(t))
    noise = np.diff(np.r_[0.0, np.cumsum(noise) / 32])
    freq = 280 + 3200 * (t / dur) ** 2.2
    tone = np.sin(2 * np.pi * np.cumsum(freq) / SR)
    return (0.24 * noise + 0.18 * tone) * (t / dur) ** 1.8


def impact(dur: float = 1.20) -> np.ndarray:
    t = np.arange(round(dur * SR)) / SR
    boom = np.sin(2 * np.pi * (39 + 78 * np.exp(-t * 12)) * t) * np.exp(-t * 3.7)
    air = rng.normal(0, 1, len(t)) * np.exp(-t * 10.5) * 0.22
    metal = np.sin(2 * np.pi * 910 * t) * np.exp(-t * 18) * 0.08
    return (boom + air + metal) * 0.86


# F#m - D - A - E; um acorde por compasso.
progression = [
    (46.25, (185.00, 220.00, 277.18), (369.99, 440.00, 554.37, 659.25)),
    (36.71, (146.83, 185.00, 220.00), (293.66, 369.99, 440.00, 554.37)),
    (55.00, (220.00, 277.18, 329.63), (440.00, 554.37, 659.25, 739.99)),
    (41.20, (164.81, 207.65, 246.94), (329.63, 415.30, 493.88, 622.25)),
]

bars = math.ceil(DURATION / BAR)
for bar in range(bars):
    t0 = bar * BAR
    section = "intro" if bar < 1 else "verse" if bar < 6 else "chorus" if bar < 11 else "outro"
    root, chord, arp = progression[(bar - 1) % 4]
    remaining = min(BAR, DURATION - t0)
    add(pad(chord, remaining, 0.055 if section in ("intro", "outro") else 0.085 if section == "verse" else 0.12), t0)

    # Motivo harmonico: piano em colcheias, glass no contratempo do refrao.
    if section != "outro" or bar == 18:
        for j in range(8):
            freq = arp[(j + bar) % len(arp)]
            gain = 0.38 if section == "intro" else 0.48 if section == "verse" else 0.63
            add(piano(freq, 0.56), t0 + j * BEAT / 2, gain, -0.45 + 0.9 * (j % 2))
            if section == "chorus" and j % 2:
                add(glass(freq * 2, 0.36), t0 + j * BEAT / 2 + 0.018, 0.52, 0.35 if j % 4 == 1 else -0.35)

    if section in ("verse", "chorus"):
        kicks = [0.0, 1.75, 2.55]
        if bar % 2:
            kicks.append(3.45)
        if section == "chorus":
            kicks += [0.75, 3.0]
        for pos in sorted(set(kicks)):
            add(kick(), t0 + pos * BEAT, 0.95 if section == "verse" else 1.0)

        # Backbeat 2/4; claps desalinhados poucos ms para largura humana.
        for backbeat in (1.0, 3.0):
            add(snare(), t0 + backbeat * BEAT, 0.88 if backbeat == 1 else 1.0)
            add(clap(), t0 + backbeat * BEAT + 0.006, 0.86, -0.24)
            add(clap(), t0 + backbeat * BEAT + 0.021, 0.68, 0.26)
        if section == "chorus":
            add(clap(), t0 + 3.5 * BEAT, 0.30, 0.16)

        # 808 respirando entre os kicks, com glide nos fins de frase.
        add(sub(root, BEAT * 1.36, 1.0), t0 + 0.07 * BEAT, 0.95)
        add(sub(root * 1.5, BEAT * 0.72, 0.86), t0 + 2.60 * BEAT, 0.82)
        if bar % 2:
            add(sub(root, BEAT * 0.48, 1.16), t0 + 3.48 * BEAT, 0.68)

        for j in range(16):
            add(hat(opened=j == 15), t0 + j * BEAT / 4,
                0.78 if j % 4 == 0 else 0.48, -0.34 if j % 2 == 0 else 0.34)
        if bar in (5, 9, 13, 17):
            for j in range(12):
                add(hat(), t0 + 3 * BEAT + j * BEAT / 12, 0.42 + j * 0.025, (-1) ** j * 0.38)

# Estrutura e impactos na grade medida dos modelos (microhit = meio beat).
add(impact(1.25), 0.0, 0.72)
VOICE_IN = 4 * BEAT
CHORUS_IN = 24 * BEAT
SIGNATURE = 39 * BEAT
add(riser(1.45), VOICE_IN - 1.45, 0.62)
add(impact(1.35), VOICE_IN, 0.86)
add(riser(1.45), CHORUS_IN - 1.45, 0.92)
add(impact(1.55), CHORUS_IN, 1.0)
add(impact(1.20), SIGNATURE, 0.78)

# Cola e headroom para a voz. Fade final de um compasso.
mix = np.tanh(mix * 1.09)
fade = round(BAR * SR)
mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
mix *= 0.90 / max(np.max(np.abs(mix)), 1e-9)

OUT.parent.mkdir(exist_ok=True)
with wave.open(str(OUT), "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())

print(f"ok: {OUT} ({DURATION:.2f}s, {BPM:.0f} BPM, grade 315.8/631.6/1263.2 ms)")
