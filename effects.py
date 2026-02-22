from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np
import torch
import torch.nn.functional as F

from config import RenderConfig
from presets import cinematic_grade


@dataclass(slots=True)
class TimelineEvents:
    beat_times: np.ndarray
    strong_beat_times: np.ndarray
    zoom_times: np.ndarray


class FrameEffects:
    def __init__(self, cfg: RenderConfig):
        self.cfg = cfg
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._motion_kernel = self._make_motion_kernel(cfg.motion_blur_kernel, cfg.motion_blur_strength)

    def _make_motion_kernel(self, size: int, strength: float) -> torch.Tensor:
        size = max(3, int(size) | 1)
        kernel = np.zeros((size, size), dtype=np.float32)
        kernel[size // 2, :] = 1.0
        kernel = cv2.GaussianBlur(kernel, (0, 0), sigmaX=max(0.5, size / 4))
        kernel /= max(kernel.sum(), 1e-6)
        kernel = (1.0 - strength) * np.eye(size, dtype=np.float32) / size + strength * kernel
        tensor = torch.from_numpy(kernel).to(self.device)
        return tensor.view(1, 1, size, size)

    def apply_motion_blur(self, frame_bgr: np.ndarray) -> np.ndarray:
        if self.device.type != "cuda":
            return cv2.filter2D(frame_bgr, -1, self._motion_kernel.squeeze().cpu().numpy())

        frame = torch.from_numpy(frame_bgr).to(self.device, dtype=torch.float32)
        frame = frame.permute(2, 0, 1).unsqueeze(0)
        channels = []
        for c in range(3):
            ch = frame[:, c : c + 1]
            blurred = F.conv2d(ch, self._motion_kernel, padding=self._motion_kernel.shape[-1] // 2)
            channels.append(blurred)
        out = torch.cat(channels, dim=1).squeeze(0).permute(1, 2, 0)
        return out.clamp(0, 255).byte().cpu().numpy()

    def crop_vertical_track(self, frame_bgr: np.ndarray, center_x: float) -> tuple[np.ndarray, float]:
        h, w = frame_bgr.shape[:2]
        target_ratio = self.cfg.target_width / self.cfg.target_height
        crop_w = int(h * target_ratio)
        crop_w = min(crop_w, w)

        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 80, 180)
        x_weights = edges.sum(axis=0).astype(np.float32)
        if x_weights.sum() > 0:
            tracked_x = float(np.dot(np.arange(w), x_weights) / x_weights.sum())
            center_x = 0.8 * center_x + 0.2 * tracked_x

        half = crop_w // 2
        center_x = float(np.clip(center_x, half, w - half))
        x0 = int(center_x - half)
        x1 = x0 + crop_w

        crop = frame_bgr[:, x0:x1]
        out = cv2.resize(crop, (self.cfg.target_width, self.cfg.target_height), interpolation=cv2.INTER_CUBIC)
        return out, center_x

    def apply_zoom(self, frame_bgr: np.ndarray, amount: float) -> np.ndarray:
        if amount <= 1.001:
            return frame_bgr
        h, w = frame_bgr.shape[:2]
        zh, zw = int(h / amount), int(w / amount)
        y0 = (h - zh) // 2
        x0 = (w - zw) // 2
        cropped = frame_bgr[y0 : y0 + zh, x0 : x0 + zw]
        return cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)

    def apply_impact_flash(self, frame_bgr: np.ndarray, intensity: float) -> np.ndarray:
        if intensity <= 0:
            return frame_bgr
        white = np.full_like(frame_bgr, 255)
        return cv2.addWeighted(frame_bgr, 1.0 - intensity, white, intensity, 0)

    def process_frame(
        self,
        frame_bgr: np.ndarray,
        t: float,
        center_x: float,
        events: TimelineEvents,
    ) -> tuple[np.ndarray, float]:
        frame, center_x = self.crop_vertical_track(frame_bgr, center_x)
        frame = cinematic_grade(frame)
        frame = self.apply_motion_blur(frame)

        zoom_strength = _pulse_intensity(t, events.zoom_times, self.cfg.zoom_duration_sec)
        frame = self.apply_zoom(frame, 1.0 + (self.cfg.zoom_factor - 1.0) * zoom_strength)

        flash = _pulse_intensity(t, events.strong_beat_times, self.cfg.impact_flash_duration_sec)
        frame = self.apply_impact_flash(frame, 0.45 * flash)
        return frame, center_x


def _pulse_intensity(t: float, times: np.ndarray, duration: float) -> float:
    if times.size == 0:
        return 0.0
    idx = np.searchsorted(times, t)
    candidates = []
    if idx < len(times):
        candidates.append(times[idx])
    if idx > 0:
        candidates.append(times[idx - 1])
    if not candidates:
        return 0.0

    d = min(abs(t - c) for c in candidates)
    if d > duration:
        return 0.0
    return float(np.cos((d / duration) * np.pi / 2) ** 2)
