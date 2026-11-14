import os
import subprocess
from pathlib import Path

import yt_dlp

# ==========================================
# CONFIGURATION
# ==========================================

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

CHUNK_MINUTES = 10


# ==========================================
# YOUTUBE AUDIO DOWNLOAD
# ==========================================


def download_youtube_audio(url: str) -> str:
    """
    Download publicly accessible YouTube audio
    and convert it to WAV.
    """

    output_path = str(DOWNLOAD_DIR / "%(id)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "noplaylist": True,
        # Convert downloaded audio to WAV
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
            }
        ],
        # Download reliability
        "retries": 5,
        "fragment_retries": 5,
        "socket_timeout": 30,
        # JavaScript challenge support
        "js_runtimes": {"node": {}},
        "remote_components": ["ejs:github"],
        # IMPORTANT:
        # Do not force a specific YouTube player client.
        # Let yt-dlp select available clients automatically.
        "quiet": False,
        "no_warnings": False,
    }

    try:
        print("Connecting to YouTube...")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(url, download=True)

            if not info:
                raise RuntimeError("Could not retrieve YouTube video information.")

            filename = ydl.prepare_filename(info)

            # Get the WAV output path
            wav_path = str(Path(filename).with_suffix(".wav"))

            if not os.path.isfile(wav_path):
                raise FileNotFoundError(f"Audio file was not created: {wav_path}")

            if os.path.getsize(wav_path) == 0:
                raise RuntimeError("Downloaded audio file is empty.")

            print("YouTube audio downloaded successfully.")

            return wav_path

    except Exception as e:

        error_message = str(e)

        if "Sign in to confirm" in error_message:
            raise RuntimeError(
                "YouTube requires sign-in verification. "
                "The server may be restricted by YouTube. "
                "Please upload the audio/video file directly."
            ) from e

        if "HTTP Error 403" in error_message:
            raise RuntimeError(
                "YouTube rejected the download request (HTTP 403). "
                "This may be caused by hosting IP restrictions "
                "or player access restrictions. "
                "Please try uploading the audio/video file directly."
            ) from e

        raise RuntimeError(f"YouTube download failed: {error_message}") from e


# ==========================================
# LOCAL AUDIO / VIDEO CONVERSION
# ==========================================


def convert_to_wav(input_path: str) -> str:
    """
    Convert local audio/video files to WAV using FFmpeg.
    """

    input_path = Path(input_path)

    if not input_path.is_file():
        raise FileNotFoundError(f"File not found: {input_path}")

    output_path = input_path.with_name(input_path.stem + "_converted.wav")

    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(input_path),
                "-vn",
                "-ac",
                "1",
                "-ar",
                "16000",
                "-c:a",
                "pcm_s16le",
                str(output_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFmpeg conversion failed: {e.stderr}") from e

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError("FFmpeg did not create a valid WAV file.")

    print(f"Audio converted successfully: {output_path}")

    return str(output_path)


# ==========================================
# AUDIO CHUNKING
# ==========================================


def chunk_audio(wav_path: str, chunk_minutes: int = CHUNK_MINUTES) -> list:
    """
    Split WAV audio into smaller chunks using FFmpeg.
    """

    wav_path = Path(wav_path)

    if not wav_path.is_file():
        raise FileNotFoundError(f"Audio file not found: {wav_path}")

    if chunk_minutes <= 0:
        raise ValueError("chunk_minutes must be greater than zero.")

    chunk_seconds = chunk_minutes * 60

    output_pattern = str(wav_path.with_name(wav_path.stem + "_chunk_%03d.wav"))

    # Remove previous chunks to avoid stale files
    for old_chunk in wav_path.parent.glob(wav_path.stem + "_chunk_*.wav"):
        old_chunk.unlink()

    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(wav_path),
                "-f",
                "segment",
                "-segment_time",
                str(chunk_seconds),
                "-c:a",
                "pcm_s16le",
                output_pattern,
            ],
            check=True,
            capture_output=True,
            text=True,
        )

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Audio chunking failed: {e.stderr}") from e

    chunks = sorted(wav_path.parent.glob(wav_path.stem + "_chunk_*.wav"))

    chunks = [str(chunk) for chunk in chunks if chunk.stat().st_size > 0]

    if not chunks:
        raise RuntimeError("No audio chunks were created.")

    print(f"Created {len(chunks)} audio chunks.")

    return chunks


# ==========================================
# MAIN INPUT PROCESSOR
# ==========================================


def process_input(source: str) -> list:
    """
    Process YouTube URLs or local audio/video files.

    Returns:
        List of WAV audio chunk paths.
    """

    if not source or not source.strip():
        raise ValueError("Please provide a valid input source.")

    source = source.strip()

    if source.startswith(("http://", "https://")):

        print("Detected YouTube URL.")

        wav_path = download_youtube_audio(source)

    else:

        print("Detected local audio/video file.")

        wav_path = convert_to_wav(source)

    print("Starting audio chunking...")

    chunks = chunk_audio(wav_path)

    print(f"Audio processing completed. " f"{len(chunks)} chunk(s) created.")

    return chunks
