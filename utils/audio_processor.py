import yt_dlp
import os
import subprocess

DOWNLOAD_DIR = "downloads"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def download_youtube_audio(url: str) -> str:
    output_path = os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "noplaylist": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
            }
        ],
        "quiet": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:

        info = ydl.extract_info(url, download=True)

        # Get the original filenames
        filename = ydl.prepare_filename(info)

        # Get the converted WAV filename
        filename = os.path.splitext(filename)[0] + ".wav"

        if not os.path.exists(filename):
            raise FileNotFoundError(f"Audio file was not created: {filename}")

        return filename


def convert_to_wav(input_path: str) -> str:
    """Converts any audio/video file to WAV format using FFmpeg."""

    # Check whether input file exists
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"File not found: {input_path}")

    # Generate output filename
    output_path = os.path.splitext(input_path)[0] + "_converted.wav"

    # Convert file to WAV
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            input_path,
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "pcm_s16le",
            output_path,
        ],
        check=True,
    )

    return output_path


def chunk_audio(wav_path: str, chunk_minutes: int = 10) -> list:
    """Splits a WAV audio file into smaller chunks using FFmpeg."""

    chunk_seconds = chunk_minutes * 60

    output_pattern = os.path.splitext(wav_path)[0] + "_chunk_%03d.wav"

    subprocess.run(
        [
            "ffmpeg",
            "-i",
            wav_path,
            "-f",
            "segment",
            "-segment_time",
            str(chunk_seconds),
            "-c",
            "copy",
            output_pattern,
        ],
        check=True,
    )

    chunks = []

    i = 0
    while True:
        chunk_path = output_pattern.replace("%03d", f"{i:03d}")

        if not os.path.exists(chunk_path):
            break

        chunks.append(chunk_path)
        i += 1

    return chunks


def process_input(source: str) -> list:
    if source.startswith("http://") or source.startswith("https://"):
        print("Detected Youtube URL. Downloading audio...")
        wav_path = download_youtube_audio(source)
    else:
        print("Detected local file. Converting to WAV...")
        wav_path = convert_to_wav(source)

    print("Chunking audio...")
    chunks = chunk_audio(wav_path)
    print(f"Audio ready - {len(chunks)} chunk(s) created.")
    return chunks
