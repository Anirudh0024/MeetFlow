# MeetFlow – AI Meeting Assistant

MeetFlow is an AI-powered meeting assistant built with Python that converts meeting recordings and YouTube videos into structured, searchable meeting notes.

It uses speech-to-text models to transcribe conversations, Large Language Models (LLMs) to generate meaningful insights, and Retrieval-Augmented Generation (RAG) to let users ask questions about their meetings.

Instead of manually reviewing lengthy recordings, MeetFlow helps you quickly understand what was discussed, what decisions were made, and what actions need to be taken.

---

## Features

- **Multiple Input Sources:** Upload local audio/video files or provide a YouTube video URL.
- **Audio Processing:** Extracts and processes audio using FFmpeg.
- **Speech-to-Text:** Transcribes meeting recordings using OpenAI Whisper.
- **Multilingual Support:** Supports English and Hinglish transcription using Whisper and Sarvam AI.
- **AI-Generated Meeting Title:** Automatically generates a suitable title for each meeting.
- **Meeting Summarization:** Creates concise summaries of lengthy conversations.
- **Action Item Extraction:** Identifies tasks and their responsibilities from meeting discussions.
- **Decision Extraction:** Extracts important decisions made during meetings.
- **Open Questions:** Identifies unanswered questions and pending discussion points.
- **RAG-Based Chat:** Ask questions about your meeting transcript using natural language.
- **Vector Search:** Stores transcript embeddings in ChromaDB for semantic retrieval.
- **Interactive Dashboard:** Provides a Streamlit interface to view summaries, transcripts, and chat with your meeting.
- **Download Transcript:** Download the generated transcript for future reference.

---

## Tech Stack

| Category               | Technologies                                         |
| ---------------------- | ---------------------------------------------------- |
| Programming Language   | Python                                               |
| Frontend               | Streamlit                                            |
| Speech Recognition     | OpenAI Whisper, Sarvam AI                            |
| LLM                    | Groq – GPT-OSS 120B                                  |
| LLM Framework          | LangChain                                            |
| Embeddings             | HuggingFace – sentence-transformers/all-MiniLM-L6-v2 |
| Vector Database        | ChromaDB                                             |
| Audio Processing       | FFmpeg                                               |
| Video Downloading      | yt-dlp                                               |
| Environment Management | uv                                                   |
| Environment Variables  | python-dotenv                                        |

---

## Project Architecture

```text
                 ┌─────────────────────────┐
                 │       User Input        │
                 │                         │
                 │  YouTube URL / File     │
                 └────────────┬────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │     Audio Processing    │
                 │                         │
                 │  yt-dlp / FFmpeg        │
                 │  Audio Extraction       │
                 │  Audio Chunking         │
                 └────────────┬────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │     Transcription       │
                 │                         │
                 │  Whisper / Sarvam AI    │
                 │  English / Hinglish     │
                 └────────────┬────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │   Transcript Processing│
                 │                         │
                 │  Title Generation       │
                 │  Meeting Summary        │
                 │  Action Items           │
                 │  Key Decisions          │
                 │  Open Questions         │
                 └────────────┬────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │       RAG Pipeline      │
                 │                         │
                 │  Text Splitting         │
                 │  HuggingFace Embeddings │
                 │  ChromaDB Vector Store  │
                 │  Semantic Retrieval     │
                 └────────────┬────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │      Streamlit UI       │
                 │                         │
                 │  Meeting Overview       │
                 │  Transcript             │
                 │  Ask Your Meeting       │
                 └─────────────────────────┘
```

---

## Project Structure

```text
MeetFlow/
│
├── core/
│   ├── transcriber.py       # Audio transcription
│   ├── summarize.py         # Title generation and summarization
│   ├── extractor.py         # Action items, decisions, questions
│   └── rag_engine.py        # RAG pipeline and question answering
│
├── utils/
│   └── audio_processor.py   # Audio extraction and chunking
│
├── documentloaders/         # Input documents, if used
│
├── app.py                   # Streamlit application
├── main.py                  # Main processing pipeline
│
├── .env                     # API keys and configuration
├── .gitignore
├── pyproject.toml            # Project dependencies
├── uv.lock                  # Dependency lock file
└── README.md
```

_The structure above describes the main modules; adjust it if your actual repository contains additional files or folders._

---

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-Anirudh0024/MeetFlow.git

cd MeetFlow
```

### 2. Install uv

If you haven't installed uv:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify the installation:

```bash
uv --version
```

### 3. Install Dependencies

Install all project dependencies:

```bash
uv sync
```

### 4. Install FFmpeg

MeetFlow uses FFmpeg for audio extraction and processing.

**macOS:**

```bash
brew install ffmpeg
```

**Ubuntu / Debian:**

```bash
sudo apt update
sudo apt install ffmpeg
```

Verify:

```bash
ffmpeg -version
```

### 5. Configure Environment Variables

Create a `.env` file in the root directory:

```env
GROQ_API_KEY=your_groq_api_key
SARVAM_API_KEY=your_sarvam_api_key

SARVAM_STT_MODEL=saaras:v2.5
SARVAM_STT_TRANSLATE_URL=https://api.sarvam.ai/speech-to-text-translate
```

Get your API keys:

- Groq: https://console.groq.com/
- Sarvam AI: https://dashboard.sarvam.ai/

**Important:** Never upload your `.env` file or expose your API keys publicly.

---

## Running the Application

Start the Streamlit application:

```bash
uv run streamlit run app.py
```

Open the local URL displayed in your terminal, usually:

```text
http://localhost:8501
```

### How to Use MeetFlow

1. Open MeetFlow in your browser.
2. Enter a YouTube video URL or upload an audio/video file.
3. Select the transcription language:
   - English
   - Hinglish
4. Click the process button.
5. Wait for the transcription and AI processing to finish.
6. Explore the generated meeting overview.
7. View the complete transcript.
8. Ask questions about the meeting using the chat interface.
9. Download the transcript when needed.

---

## How RAG Works in MeetFlow

MeetFlow uses Retrieval-Augmented Generation (RAG) to answer questions based on meeting conversations.

The process works as follows:

1. **Document Creation:** The meeting transcript is prepared as text.
2. **Text Splitting:** The transcript is divided into smaller chunks.
3. **Embedding Generation:** HuggingFace generates vector embeddings for the text chunks.
4. **Vector Storage:** The embeddings are stored in ChromaDB.
5. **Question Embedding:** A user's question is converted into a vector representation.
6. **Semantic Retrieval:** Relevant transcript chunks are retrieved from ChromaDB.
7. **Answer Generation:** Groq's GPT-OSS 120B model uses the retrieved context to generate an answer.

This allows users to search through lengthy meeting conversations without manually reading the entire transcript.

---

## Example Questions

After processing a meeting, you can ask:

- What were the main topics discussed?
- What decisions were made during the meeting?
- What tasks were assigned to the team?
- What is the deadline for the project?
- What problems were discussed?
- Were there any unanswered questions?
- Give me a summary of the discussion about the project timeline.

---

## Future Improvements

- [ ] Support more regional Indian languages.
- [ ] Add speaker diarization to identify different speakers.
- [ ] Generate downloadable meeting reports in PDF format.
- [ ] Export action items to task management platforms.
- [ ] Add persistent meeting history using a database.
- [ ] Improve conversational memory in the RAG chat.
- [ ] Add meeting analytics and insights.
- [ ] Deploy MeetFlow as a cloud-based application.
- [ ] Add user authentication and personalized dashboards.

---

## Environment and Requirements

- Python 3.10+
- FFmpeg
- uv package manager
- Groq API key
- Sarvam AI API key (for Sarvam-based transcription)

---

## Contributing

Contributions, suggestions, and improvements are welcome.

1. Fork the repository.
2. Create a new feature branch.
3. Make your changes.
4. Commit your changes.
5. Open a Pull Request.

---

## License

This project is licensed under the MIT License.

---

**MeetFlow – Turn conversations into meaningful insights.**
