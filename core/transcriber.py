import whisper
import os
import requests
import subprocess
import tempfile
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


# Configuration
SARVAM_PIECE_SECONDS = 25

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
SARVAM_STT_TRANSLATE_URL = os.getenv(
    "SARVAM_STT_TRANSLATE_URL", "https://api.sarvam.ai/speech-to-text-translate"
)
SARVAM_MODEL = os.getenv("SARVAM_STT_MODEL", "saaras:v2.5")

_model = None


def load_model():

    global _model

    if _model is None:
        print(f"Loading Whisper model: {WHISPER_MODEL} ...")

        _model = whisper.load_model(WHISPER_MODEL)

        print("Whisper model loaded.")

    return _model


def transcribe_chunk_whisper(chunk_path: str) -> str:

    model = load_model()

    result = model.transcribe(chunk_path, task="transcribe")

    return result["text"]


def _split_audio_into_pieces(chunk_path: str, output_dir: str) -> list:
    """Split audio into 25-second WAV pieces using FFmpeg."""

    output_pattern = os.path.join(output_dir, "piece_%03d.wav")

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            chunk_path,
            "-f",
            "segment",
            "-segment_time",
            str(SARVAM_PIECE_SECONDS),
            "-c:a",
            "pcm_s16le",
            output_pattern,
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    pieces = sorted(Path(output_dir).glob("piece_*.wav"))

    return [str(piece) for piece in pieces]


def _send_to_sarvam(piece_path: str) -> str:
    """Send one WAV piece to Sarvam and return the English transcript."""

    if not SARVAM_API_KEY:
        raise RuntimeError("SARVAM_API_KEY is not set in .env")

    headers = {"api-subscription-key": SARVAM_API_KEY}

    with open(piece_path, "rb") as f:

        files = {"file": (os.path.basename(piece_path), f, "audio/wav")}

        data = {"model": SARVAM_MODEL, "with_diarization": "false"}

        response = requests.post(
            SARVAM_STT_TRANSLATE_URL,
            headers=headers,
            files=files,
            data=data,
            timeout=120,
        )

    if not response.ok:
        print(f"Sarvam returned {response.status_code}")
        print(f"Response body: {response.text}")
        response.raise_for_status()

    return response.json().get("transcript", "")


def transcribe_chunk_sarvam(chunk_path: str) -> str:
    """
    Split audio into 25-second pieces,
    send each piece to Sarvam,
    and combine the English transcripts.
    """

    if not SARVAM_API_KEY:
        raise RuntimeError("SARVAM_API_KEY is not set in .env")

    full_text = ""

    with tempfile.TemporaryDirectory() as temp_dir:

        pieces = _split_audio_into_pieces(chunk_path, temp_dir)

        total_pieces = len(pieces)

        for i, piece_path in enumerate(pieces):

            print(f"  → Sarvam piece {i + 1}/{total_pieces} ...")

            text = _send_to_sarvam(piece_path)

            full_text += text + " "

    return full_text.strip()


def transcribe_chunk(chunk_path: str, language: str = "english") -> str:
    """
    Route one chunk to Whisper or Sarvam.

    english  → Whisper
    hinglish → Sarvam AI
    """

    if language.lower() == "hinglish":
        return transcribe_chunk_sarvam(chunk_path)

    return transcribe_chunk_whisper(chunk_path)


def transcribe_all(chunks: list, language: str = "english") -> str:

    full_transcript = ""

    engine = "Sarvam AI" if language.lower() == "hinglish" else "Whisper"

    print(f"Using {engine} for transcription.")

    for i, chunk in enumerate(chunks):

        print(f"Transcribing chunk {i + 1}/{len(chunks)}...")

        text = transcribe_chunk(chunk, language=language)

        full_transcript += text + " "

    print("Transcription complete.")

    return full_transcript.strip()
