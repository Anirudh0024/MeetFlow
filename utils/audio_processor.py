import yt_dlp
import os
import subprocess

# Create downloads folder if it doesn't exist
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def download_youtube_audio(url: str) -> str:
    """Download YouTube audio and convert it to WAV."""

    output_path = os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s")

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
        # YouTube compatibility
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"],
            }
        },
        # JavaScript challenge support
        "js_runtimes": {"node": {}},
        "remote_components": ["ejs:github"],
        "quiet": False,
        "no_warnings": False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(url, download=True)

            filename = ydl.prepare_filename(info)

            # Change extension to WAV
            filename = os.path.splitext(filename)[0] + ".wav"

            if not os.path.exists(filename):
                raise FileNotFoundError(f"Audio file was not created: {filename}")

            return filename

    except Exception as e:
        raise RuntimeError(f"YouTube download failed: {str(e)}") from e


def convert_to_wav(input_path: str) -> str:
    """Convert local audio/video files to WAV using FFmpeg."""

    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"File not found: {input_path}")

    output_path = os.path.splitext(input_path)[0] + "_converted.wav"

    try:
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
            capture_output=True,
            text=True,
        )

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFmpeg conversion failed: {e.stderr}") from e

    return output_path


def chunk_audio(wav_path: str, chunk_minutes: int = 10) -> list:
    """Split WAV audio into smaller chunks using FFmpeg."""

    if not os.path.isfile(wav_path):
        raise FileNotFoundError(f"Audio file not found: {wav_path}")

    if chunk_minutes <= 0:
        raise ValueError("chunk_minutes must be greater than zero.")

    chunk_seconds = chunk_minutes * 60

    output_pattern = os.path.splitext(wav_path)[0] + "_chunk_%03d.wav"

    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                wav_path,
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

    chunks = []
    i = 0

    while True:
        chunk_path = output_pattern.replace("%03d", f"{i:03d}")

        if not os.path.exists(chunk_path):
            break

        chunks.append(chunk_path)
        i += 1

    if not chunks:
        raise RuntimeError("No audio chunks were created.")

    return chunks


def process_input(source: str) -> list:
    """
    Process YouTube URLs or local audio/video files.
    Returns a list of WAV audio chunk paths.
    """

    if not source or not source.strip():
        raise ValueError("Please provide a valid input source.")

    source = source.strip()

    if source.startswith(("http://", "https://")):

        print("Detected YouTube URL. Downloading audio...")

        wav_path = download_youtube_audio(source)

    else:

        print("Detected local file. Converting to WAV...")

        wav_path = convert_to_wav(source)

    print("Chunking audio...")

    chunks = chunk_audio(wav_path)

    print(f"Audio ready - {len(chunks)} chunk(s) created.")

    return chunks
