#!/usr/bin/env python3
"""Convert WhatsApp OGG/Opus voice notes to WAV and transcribe them locally.

Dependencies: faster-whisper and imageio-ffmpeg. Audio is never uploaded.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", nargs="+", type=Path, help="Input WhatsApp OGG/Opus files")
    parser.add_argument("--model", default="small", help="faster-whisper model (default: small)")
    parser.add_argument("--language", default="es", help="Audio language code (default: es)")
    parser.add_argument("--wav-dir", type=Path, help="Optional directory to retain converted WAV files")
    return parser.parse_args()


def convert_to_wav(source: Path, target: Path, ffmpeg: str) -> None:
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        str(target),
    ]
    subprocess.run(command, check=True)


def main() -> int:
    args = parse_args()
    missing = [str(path) for path in args.audio if not path.is_file()]
    if missing:
        raise SystemExit("Audio file not found: " + ", ".join(missing))

    # Use standard HTTPS downloads in local environments where Xet transfers
    # may stall; this affects model retrieval only, never audio upload.
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")

    from faster_whisper import WhisperModel
    from imageio_ffmpeg import get_ffmpeg_exe

    model = WhisperModel(args.model, device="cpu", compute_type="int8")
    ffmpeg = get_ffmpeg_exe()

    if args.wav_dir:
        args.wav_dir.mkdir(parents=True, exist_ok=True)
        work_dir = args.wav_dir
        temporary = None
    else:
        temporary = tempfile.TemporaryDirectory(prefix="arcoenergy-whatsapp-")
        work_dir = Path(temporary.name)

    try:
        for source in args.audio:
            wav_path = work_dir / f"{source.stem}.wav"
            convert_to_wav(source, wav_path, ffmpeg)
            segments, info = model.transcribe(
                str(wav_path),
                language=args.language,
                vad_filter=True,
                beam_size=5,
            )
            print(f"\n## {source.name} (idioma detectado: {info.language})")
            for segment in segments:
                start = int(segment.start)
                end = int(segment.end)
                print(f"[{start // 60:02d}:{start % 60:02d}-{end // 60:02d}:{end % 60:02d}] {segment.text.strip()}")
    finally:
        if temporary is not None:
            temporary.cleanup()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
