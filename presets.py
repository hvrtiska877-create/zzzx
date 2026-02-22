from __future__ import annotations

import cv2
import numpy as np


def cinematic_grade(frame_bgr: np.ndarray) -> np.ndarray:
    """Fast cinematic look: mild teal-orange split + contrast + vignette."""

    frame = frame_bgr.astype(np.float32) / 255.0
    b, g, r = cv2.split(frame)

    shadows = np.clip(1.0 - cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), 0.0, 1.0)
    highlights = np.clip(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), 0.0, 1.0)

    b = np.clip(b + 0.08 * shadows, 0.0, 1.0)
    g = np.clip(g + 0.03 * shadows, 0.0, 1.0)
    r = np.clip(r + 0.06 * highlights, 0.0, 1.0)

    graded = cv2.merge((b, g, r))

    graded = np.clip((graded - 0.5) * 1.16 + 0.5, 0.0, 1.0)

    h, w = graded.shape[:2]
    y, x = np.ogrid[:h, :w]
    cx, cy = w / 2, h / 2
    dist = np.sqrt(((x - cx) / (w / 2)) ** 2 + ((y - cy) / (h / 2)) ** 2)
    vignette = np.clip(1.0 - 0.28 * dist, 0.62, 1.0).astype(np.float32)
    graded *= vignette[..., None]

    return (graded * 255.0).clip(0, 255).astype(np.uint8)
