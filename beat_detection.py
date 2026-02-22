from __future__ import annotations

from dataclasses import dataclass

import librosa
import numpy as np


@dataclass(slots=True)
class BeatInfo:
    beat_times: np.ndarray
    strong_beats: np.ndarray
    tempo: float


def detect_beats(
    audio_path: str,
    sensitivity: float = 1.25,
    strong_percentile: float = 88.0,
    min_interval_sec: float = 0.18,
) -> BeatInfo:
    y, sr = librosa.load(audio_path, sr=None, mono=True)
    y = librosa.util.normalize(y)

    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    tempo, beat_frames = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)

    if beat_times.size == 0:
        return BeatInfo(beat_times=np.array([]), strong_beats=np.array([]), tempo=float(tempo))

    keep = [0]
    for i in range(1, len(beat_times)):
        if beat_times[i] - beat_times[keep[-1]] >= min_interval_sec:
            keep.append(i)
    beat_times = beat_times[np.array(keep)]

    beat_strength = np.interp(
        beat_times,
        librosa.times_like(onset_env, sr=sr),
        onset_env,
        left=0,
        right=0,
    )

    threshold = np.percentile(beat_strength, strong_percentile) * sensitivity
    strong_beats = beat_times[beat_strength >= threshold]

    return BeatInfo(beat_times=beat_times, strong_beats=strong_beats, tempo=float(tempo))
