from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class RenderConfig:
    """Runtime configuration for the Shorts generator."""

    input_video: Path
    input_audio: Path | None = None
    output_video: Path = Path("output_final.mp4")

    fps: int = 30
    target_width: int = 1080
    target_height: int = 1920

    beat_sensitivity: float = 1.25
    strong_beat_percentile: float = 88.0
    min_beat_interval_sec: float = 0.18

    zoom_factor: float = 1.18
    zoom_duration_sec: float = 0.22
    high_motion_quantile: float = 0.9

    motion_blur_kernel: int = 13
    motion_blur_strength: float = 0.9
    impact_flash_duration_sec: float = 0.08

    subtitle_font_scale: float = 1.2
    subtitle_thickness: int = 2

    bitrate: str = "14M"
    preset: str = "medium"

    max_preview_frames: int | None = None

    @classmethod
    def from_args(cls, args: dict) -> "RenderConfig":
        input_video = Path(args["input_video"]).expanduser().resolve()
        input_audio = args.get("input_audio")
        if input_audio:
            input_audio = Path(input_audio).expanduser().resolve()
        output_video = Path(args.get("output", "output_final.mp4")).expanduser().resolve()
        return cls(input_video=input_video, input_audio=input_audio, output_video=output_video)
