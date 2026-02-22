from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import cv2
import numpy as np
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.io.ffmpeg_writer import FFMPEG_VideoWriter
from moviepy.video.io.VideoFileClip import VideoFileClip

from beat_detection import detect_beats
from config import RenderConfig
from effects import FrameEffects, TimelineEvents
from subtitles import SubtitleRenderer


def parse_args() -> dict:
    parser = argparse.ArgumentParser(description="AI Viral Editor - GPU Shorts generator")
    parser.add_argument("input_video", help="Path to raw gameplay video")
    parser.add_argument("--input-audio", dest="input_audio", default=None, help="Optional external music/audio path")
    parser.add_argument("--subtitles", dest="subtitles", default=None, help="Optional subtitle text file (start|end|text)")
    parser.add_argument("--output", dest="output", default="output_final.mp4", help="Output path")
    return vars(parser.parse_args())


def extract_audio_if_needed(cfg: RenderConfig) -> Path:
    if cfg.input_audio is not None:
        return cfg.input_audio
    temp_audio = Path(tempfile.gettempdir()) / "ai_viral_editor_audio.wav"
    with VideoFileClip(str(cfg.input_video)) as clip:
        clip.audio.write_audiofile(str(temp_audio), logger=None)
    return temp_audio


def detect_high_motion_times(video_path: Path, fps: int, quantile: float) -> np.ndarray:
    cap = cv2.VideoCapture(str(video_path))
    ok, prev = cap.read()
    if not ok:
        cap.release()
        return np.array([])

    prev_g = cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY)
    motions = []
    idx = 1
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(gray, prev_g)
        motions.append((idx / fps, float(diff.mean())))
        prev_g = gray
        idx += 1
    cap.release()

    if not motions:
        return np.array([])

    scores = np.array([m[1] for m in motions], dtype=np.float32)
    threshold = np.quantile(scores, quantile)
    times = np.array([t for t, s in motions if s >= threshold], dtype=np.float32)

    if len(times) < 2:
        return times

    filtered = [times[0]]
    for t in times[1:]:
        if t - filtered[-1] >= 0.25:
            filtered.append(t)
    return np.array(filtered)


def merge_event_times(beat_times: np.ndarray, motion_times: np.ndarray) -> np.ndarray:
    if beat_times.size == 0:
        return motion_times
    if motion_times.size == 0:
        return beat_times
    merged = np.concatenate([beat_times, motion_times])
    merged.sort()
    dedup = [merged[0]]
    for t in merged[1:]:
        if t - dedup[-1] > 0.12:
            dedup.append(t)
    return np.array(dedup)


def render(cfg: RenderConfig, subtitle_path: str | None = None) -> Path:
    audio_path = extract_audio_if_needed(cfg)
    beat_info = detect_beats(
        str(audio_path),
        sensitivity=cfg.beat_sensitivity,
        strong_percentile=cfg.strong_beat_percentile,
        min_interval_sec=cfg.min_beat_interval_sec,
    )

    motion_times = detect_high_motion_times(cfg.input_video, cfg.fps, cfg.high_motion_quantile)
    zoom_times = merge_event_times(beat_info.beat_times, motion_times)

    effects = FrameEffects(cfg)

    with VideoFileClip(str(cfg.input_video)) as src_clip:
        duration = src_clip.duration
        subtitles = SubtitleRenderer.from_txt(subtitle_path, duration)
        audio_clip = AudioFileClip(str(audio_path)).subclipped(0, duration)

        writer = FFMPEG_VideoWriter(
            filename=str(cfg.output_video),
            size=(cfg.target_width, cfg.target_height),
            fps=cfg.fps,
            codec="libx264",
            audiofile=str(audio_path),
            preset=cfg.preset,
            bitrate=cfg.bitrate,
            ffmpeg_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart", "-profile:v", "high"],
        )

        events = TimelineEvents(
            beat_times=beat_info.beat_times,
            strong_beat_times=beat_info.strong_beats,
            zoom_times=zoom_times,
        )

        center_x = src_clip.w / 2
        frame_count = int(duration * cfg.fps)
        if cfg.max_preview_frames:
            frame_count = min(frame_count, cfg.max_preview_frames)

        for i in range(frame_count):
            t = i / cfg.fps
            frame_rgb = src_clip.get_frame(t)
            frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

            processed, center_x = effects.process_frame(frame_bgr, t, center_x, events)
            processed = subtitles.draw(processed, t)
            out_rgb = cv2.cvtColor(processed, cv2.COLOR_BGR2RGB)
            writer.write_frame(out_rgb)

        writer.close()
        audio_clip.close()

    return cfg.output_video


def main() -> None:
    args = parse_args()
    cfg = RenderConfig.from_args(args)
    output = render(cfg, subtitle_path=args.get("subtitles"))
    print(f"Done: {output}")


if __name__ == "__main__":
    main()
