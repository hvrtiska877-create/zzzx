from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(slots=True)
class SubtitleSegment:
    start: float
    end: float
    text: str


class SubtitleRenderer:
    def __init__(self, segments: list[SubtitleSegment], font_scale: float = 1.2, thickness: int = 2):
        self.segments = segments
        self.font = cv2.FONT_HERSHEY_DUPLEX
        self.font_scale = font_scale
        self.thickness = thickness

    @classmethod
    def from_txt(cls, subtitle_path: str | None, duration: float) -> "SubtitleRenderer":
        if not subtitle_path:
            return cls(_fallback_segments(duration))

        segments: list[SubtitleSegment] = []
        with open(subtitle_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("|", 2)
                if len(parts) != 3:
                    continue
                start, end, text = parts
                segments.append(SubtitleSegment(float(start), float(end), text))
        if not segments:
            segments = _fallback_segments(duration)
        return cls(segments)

    def draw(self, frame_bgr: np.ndarray, t: float) -> np.ndarray:
        for seg in self.segments:
            if seg.start <= t <= seg.end:
                return _draw_caption(frame_bgr, seg.text, self.font, self.font_scale, self.thickness)
        return frame_bgr


def _draw_caption(frame: np.ndarray, text: str, font: int, font_scale: float, thickness: int) -> np.ndarray:
    h, w = frame.shape[:2]
    max_width = int(w * 0.85)
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        (tw, _), _ = cv2.getTextSize(trial, font, font_scale, thickness)
        if tw <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)

    out = frame.copy()
    y = int(h * 0.82)
    line_h = int(44 * font_scale)
    for line in lines:
        (tw, th), _ = cv2.getTextSize(line, font, font_scale, thickness)
        x = (w - tw) // 2
        cv2.rectangle(out, (x - 16, y - th - 14), (x + tw + 16, y + 14), (0, 0, 0), -1)
        cv2.putText(out, line, (x, y), font, font_scale, (255, 255, 255), thickness + 3, cv2.LINE_AA)
        cv2.putText(out, line, (x, y), font, font_scale, (60, 220, 255), thickness, cv2.LINE_AA)
        y += line_h
    return out


def _fallback_segments(duration: float) -> list[SubtitleSegment]:
    step = max(1.6, duration / 6)
    t = 0.0
    i = 1
    segments: list[SubtitleSegment] = []
    while t < duration:
        end = min(duration, t + step)
        segments.append(SubtitleSegment(t, end, f"HYPE MOMENT {i}"))
        t = end
        i += 1
    return segments
