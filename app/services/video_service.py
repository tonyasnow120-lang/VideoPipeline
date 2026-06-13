import shutil
import subprocess
from pathlib import Path

from app.config import MUSIC_DIR
from app.models import Series

CAPTION_STYLES = {
    "bold_white":     {"Fontname": "Arial",  "Fontsize": 90,  "PrimaryColour": "&H00FFFFFF", "Bold": 1, "Outline": 4, "Shadow": 0, "Alignment": 2, "MarginV": 200},
    "yellow_impact":  {"Fontname": "Impact", "Fontsize": 100, "PrimaryColour": "&H0000FFFF", "Bold": 0, "Outline": 5, "Shadow": 0, "Alignment": 2, "MarginV": 200},
    "minimal":        {"Fontname": "Arial",  "Fontsize": 75,  "PrimaryColour": "&H00FFFFFF", "Bold": 0, "Outline": 2, "Shadow": 0, "Alignment": 2, "MarginV": 180},
    "tiktok_classic": {"Fontname": "Arial",  "Fontsize": 88,  "PrimaryColour": "&H00FFFFFF", "Bold": 1, "Outline": 3, "Shadow": 2, "Alignment": 2, "MarginV": 200},
    "outline_black":  {"Fontname": "Arial",  "Fontsize": 85,  "PrimaryColour": "&H00FFFFFF", "Bold": 1, "Outline": 6, "Shadow": 0, "Alignment": 2, "MarginV": 200},
}


def _run_ffmpeg(cmd: list):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg error: {result.stderr[-500:]}")
    return result


def _seconds_to_ass_time(s: float) -> str:
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = int(s % 60)
    cs = int((s % 1) * 100)
    return f"{h}:{m:02d}:{sec:02d}.{cs:02d}"


def _build_ass(scenes: list, caption_style: str, ass_path: Path):
    style = CAPTION_STYLES.get(caption_style, CAPTION_STYLES["bold_white"])

    header = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        "PlayResX: 1080\n"
        "PlayResY: 1920\n"
        "ScaledBorderAndShadow: yes\n"
        "\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
        "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Default,{Fontname},{Fontsize},{PrimaryColour},&H000000FF,&H00000000,"
        "&H00000000,{Bold},0,0,0,100,100,0,0,1,{Outline},{Shadow},{Alignment},60,60,{MarginV},1\n"
        "\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    ).format(**style)

    dialogue_lines = []
    cumulative = 0.0
    for scene in scenes:
        words = scene.narration.split()
        if not words:
            cumulative += scene.actual_duration
            continue
        time_per_word = scene.actual_duration / len(words)
        for i, word in enumerate(words):
            start = cumulative + i * time_per_word
            end = cumulative + (i + 1) * time_per_word
            start_ass = _seconds_to_ass_time(start)
            end_ass = _seconds_to_ass_time(end)
            dialogue_lines.append(
                f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{word.upper()}"
            )
        cumulative += scene.actual_duration

    ass_path.write_text(header + "\n".join(dialogue_lines) + "\n", encoding="utf-8")


def _ass_path_for_filter(ass_path: Path) -> str:
    # Escape the path for use inside an ffmpeg filter argument.
    p = str(ass_path)
    p = p.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
    return p


def assemble_video(
    scenes: list,
    audio_paths: list,
    image_paths: list,
    series: Series,
    output_path: Path,
    workspace_dir: Path,
    log_fn,
) -> float:
    total = len(scenes)

    clip_paths = []
    for idx, scene in enumerate(scenes):
        n = scene.scene_number
        image_path = image_paths[idx]
        audio_path = audio_paths[idx]

        # Step A — scale image to 1080x1920 portrait fill.
        bg_path = workspace_dir / f"scene_{n}_bg.png"
        _run_ffmpeg([
            "ffmpeg", "-i", str(image_path),
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1",
            "-y", str(bg_path),
        ])

        # Step B — Ken Burns clip per scene.
        duration_frames = max(1, int(scene.actual_duration * 30))
        clip_path = workspace_dir / f"scene_{n}_clip.mp4"
        filter_complex = (
            "[0:v]scale=1188:2112,"
            "zoompan=z='min(zoom+0.0015,1.1)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={duration_frames}:s=1080x1920:fps=30,"
            "setpts=PTS-STARTPTS[v];"
            "[1:a]asetpts=PTS-STARTPTS[a]"
        )
        _run_ffmpeg([
            "ffmpeg", "-loop", "1", "-i", str(bg_path), "-i", str(audio_path),
            "-filter_complex", filter_complex,
            "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "192k",
            "-t", str(scene.actual_duration),
            "-y", str(clip_path),
        ])
        clip_paths.append(clip_path)

        pct = 71 + int((idx + 1) / total * 19)
        log_fn("progress", f"Rendered scene {n} clip", pct)

    # Step C — concatenate scene clips.
    concat_list = workspace_dir / "concat_list.txt"
    concat_list.write_text(
        "".join(f"file '{p.resolve()}'\n" for p in clip_paths), encoding="utf-8"
    )
    raw_concat = workspace_dir / "raw_concat.mp4"
    _run_ffmpeg([
        "ffmpeg", "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-y", str(raw_concat),
    ])
    log_fn("info", "Scene clips concatenated", 90)

    # Step D — generate ASS captions.
    captions_ass = workspace_dir / "captions.ass"
    _build_ass(scenes, series.caption_style, captions_ass)
    ass_filter_path = _ass_path_for_filter(captions_ass)

    # Step E — final composite.
    music_path = None
    if series.music_track:
        candidate = MUSIC_DIR / series.music_track
        if candidate.exists():
            music_path = candidate
        else:
            log_fn("info", f"Music file not found: {series.music_track}, skipping music")

    if music_path is not None:
        filter_complex = (
            "[0:a]volume=1.0[voice];"
            f"[1:a]volume={series.music_volume}[music];"
            "[voice][music]amix=inputs=2:duration=first[aout];"
            f"[0:v]ass={ass_filter_path}[vout]"
        )
        _run_ffmpeg([
            "ffmpeg", "-i", str(raw_concat),
            "-stream_loop", "-1", "-i", str(music_path),
            "-filter_complex", filter_complex,
            "-map", "[vout]", "-map", "[aout]",
            "-c:v", "libx264", "-preset", "fast", "-crf", "22",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            "-y", str(output_path),
        ])
    else:
        _run_ffmpeg([
            "ffmpeg", "-i", str(raw_concat),
            "-vf", f"ass={ass_filter_path}",
            "-c:v", "libx264", "-preset", "fast", "-crf", "22",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            "-y", str(output_path),
        ])
    log_fn("info", "Captions burned in", 95)

    # Step F — cleanup (only on success).
    shutil.rmtree(workspace_dir, ignore_errors=True)

    return sum(scene.actual_duration for scene in scenes)
