"""MeetFlow - Streamlit UI.

Run with:  streamlit run app.py

Highlights
- Accessible light themes: every button/text pair meets WCAG AA (>= 4.5:1).
- Real, step-by-step progress from the pipeline (falls back gracefully if
  your main.py has no `on_progress` support).
- Safe navigation (callbacks), escaped HTML, friendly errors, per-meeting chat.
"""

from __future__ import annotations

import html
import inspect
import re
import tempfile
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from main import run_pipeline

try:  # present in the improved main.py
    from main import PipelineError
except ImportError:  # older main.py
    PipelineError = Exception  # type: ignore[assignment,misc]

try:
    from main import answer_question
except ImportError:
    from core.rag_engine import ask_question as answer_question

load_dotenv()

SUPPORTS_PROGRESS = "on_progress" in inspect.signature(run_pipeline).parameters


# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="MeetFlow | AI Meeting Assistant",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------
# THEMES
# --------------------------------------------------
# primary / primary_hover : button + active colours. Dark enough for white text
#                           (contrast >= 5.5:1).
# accent                  : the original soft colour, used only for decoration.
# muted                   : secondary text, >= 5:1 on every surface.
# border_strong           : input outlines, >= 3:1 against white.

THEMES = {
    "Sage": {
        "primary": "#4F6F5F",
        "primary_hover": "#435E50",
        "accent": "#648C78",
        "background": "#F4F7F3",
        "sidebar": "#EAF0E9",
        "surface": "#FFFFFF",
        "surface_alt": "#EEF4EF",
        "border": "#DCE6DD",
        "border_strong": "#7D9487",
        "text": "#26372E",
        "muted": "#5C6861",
        "user_bubble": "#E3EEE6",
        "assistant_bubble": "#FFFFFF",
        "accent_soft": "#E7F0E8",
    },
    "Soft Blue": {
        "primary": "#506B86",
        "primary_hover": "#445B72",
        "accent": "#6486A8",
        "background": "#F3F7FA",
        "sidebar": "#E9F0F5",
        "surface": "#FFFFFF",
        "surface_alt": "#EDF3F8",
        "border": "#DCE6EE",
        "border_strong": "#7B91A6",
        "text": "#263746",
        "muted": "#596774",
        "user_bubble": "#E3EDF5",
        "assistant_bubble": "#FFFFFF",
        "accent_soft": "#E8F0F7",
    },
    "Lavender": {
        "primary": "#6E618D",
        "primary_hover": "#5E5378",
        "accent": "#8878AE",
        "background": "#F7F5FA",
        "sidebar": "#EFEBF5",
        "surface": "#FFFFFF",
        "surface_alt": "#F1EDF7",
        "border": "#E5DEED",
        "border_strong": "#9185AD",
        "text": "#352F40",
        "muted": "#686171",
        "user_bubble": "#EEE9F5",
        "assistant_bubble": "#FFFFFF",
        "accent_soft": "#F0EBF6",
    },
    "Warm Sand": {
        "primary": "#836246",
        "primary_hover": "#6E523A",
        "accent": "#B1845E",
        "background": "#FAF7F2",
        "sidebar": "#F2ECE3",
        "surface": "#FFFFFF",
        "surface_alt": "#F6F0E7",
        "border": "#E9DFD2",
        "border_strong": "#A08C78",
        "text": "#40372F",
        "muted": "#6D6257",
        "user_bubble": "#F2E9DD",
        "assistant_bubble": "#FFFFFF",
        "accent_soft": "#F5EEE4",
    },
}

STARTER_QUESTIONS = [
    "What are the main takeaways?",
    "What decisions were made?",
    "List the action items.",
    "Explain the main topic step by step.",
]


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

DEFAULTS = {
    "meeting": None,
    "current_meeting_id": None,
    "chat_history": [],
    "meeting_history": [],
    "selected_theme": "Sage",
    "active_page": "New Meeting",
    "pending_question": None,
    "flash": None,
}

for _key, _value in DEFAULTS.items():
    if _key not in st.session_state:
        st.session_state[_key] = _value

theme = THEMES[st.session_state.selected_theme]


# --------------------------------------------------
# CSS
# --------------------------------------------------
# Colours come from CSS variables, so the stylesheet below is plain CSS.

THEME_VARS = (
    ":root{"
    + ";".join(f"--mf-{k.replace('_', '-')}:{v}" for k, v in theme.items())
    + "}"
)

BASE_CSS = """
:root { color-scheme: light; }

.stApp { background: var(--mf-background); color: var(--mf-text); }
[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 2.4rem; padding-bottom: 5rem; max-width: 1100px; }

[data-testid="stSidebar"] {
    background: var(--mf-sidebar);
    border-right: 1px solid var(--mf-border);
}

/* ---------- Cards (see card() in app.py) ---------- */
[data-testid="stVerticalBlock"]:has(> .element-container .mf-card-marker),
[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .mf-card-marker) {
    background: var(--mf-surface) !important;
    border: 1px solid var(--mf-border) !important;
    border-radius: 16px !important;
    padding: 6px 8px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, .04);
}
.element-container:has(.mf-card-marker), [data-testid="stElementContainer"]:has(.mf-card-marker) { display: none; }

/* ---------- Text ---------- */
.stApp :is(h1, h2, h3, h4, h5, h6) { color: var(--mf-text); }
[data-testid="stMarkdownContainer"] :is(p, li, span, strong, em, td, th, h1, h2, h3, h4) {
    color: var(--mf-text);
}
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] *, label { color: var(--mf-text) !important; }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * {
    color: var(--mf-muted) !important;
}

.brand-title { font-size: 28px; font-weight: 800; letter-spacing: -1px; color: var(--mf-text); }
.brand-subtitle { color: var(--mf-muted); font-size: 13px; margin-top: -3px; }
.side-label {
    color: var(--mf-muted); font-size: 11px; font-weight: 700;
    letter-spacing: .12em; margin: 4px 0 6px;
}
.small-muted { color: var(--mf-muted); font-size: 12px; line-height: 1.6; }
.page-title { font-size: 34px; font-weight: 780; letter-spacing: -1px; color: var(--mf-text); margin-bottom: 2px; }
.page-subtitle { color: var(--mf-muted); font-size: 15px; margin-bottom: 22px; }

/* ---------- Cards ---------- */
.meeting-banner {
    background: var(--mf-accent-soft);
    border: 1px solid var(--mf-border);
    border-left: 5px solid var(--mf-accent);
    border-radius: 16px;
    padding: 20px 22px;
    margin-bottom: 18px;
}
.meeting-banner-title { color: var(--mf-text); font-size: 22px; font-weight: 750; }
.meeting-banner-caption { color: var(--mf-muted); font-size: 13px; margin-top: 5px; }

[data-testid="stMetric"] {
    background: var(--mf-surface);
    border: 1px solid var(--mf-border);
    border-radius: 14px;
    padding: 12px 16px;
}
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] * { color: var(--mf-muted) !important; }
[data-testid="stMetricValue"], [data-testid="stMetricValue"] * { color: var(--mf-text) !important; }

[data-testid="stExpander"] details {
    background: var(--mf-surface);
    border: 1px solid var(--mf-border);
    border-radius: 14px;
}
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary * { color: var(--mf-text) !important; }

.swatch-row { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 6px; }
.swatch-chip {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 6px 12px; border-radius: 999px;
    background: var(--mf-surface); border: 1px solid var(--mf-border);
    color: var(--mf-text); font-size: 13px; font-weight: 600;
}
.swatch { width: 14px; height: 14px; border-radius: 50%; border: 1px solid rgba(0,0,0,.15); }

/* ---------- Buttons (primary = white on dark, secondary = dark on white) ---------- */
[data-testid^="stBaseButton-"], .stButton > button, .stDownloadButton > button {
    border-radius: 10px !important;
    min-height: 42px;
    font-weight: 600 !important;
    transition: background .15s ease, border-color .15s ease;
}

[data-testid^="stBaseButton-primary"], button[kind="primary"] {
    background-color: var(--mf-primary) !important;
    border: 1px solid var(--mf-primary) !important;
    color: #FFFFFF !important;
}
[data-testid^="stBaseButton-primary"] *, button[kind="primary"] * {
    color: #FFFFFF !important;
    fill: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}
[data-testid^="stBaseButton-primary"]:hover:not(:disabled), button[kind="primary"]:hover:not(:disabled) {
    background-color: var(--mf-primary-hover) !important;
    border-color: var(--mf-primary-hover) !important;
}

[data-testid^="stBaseButton-secondary"], button[kind="secondary"] {
    background-color: var(--mf-surface) !important;
    border: 1px solid var(--mf-border-strong) !important;
    color: var(--mf-text) !important;
}
[data-testid^="stBaseButton-secondary"] *, button[kind="secondary"] * {
    color: var(--mf-text) !important;
    fill: var(--mf-text) !important;
    -webkit-text-fill-color: var(--mf-text) !important;
}
[data-testid^="stBaseButton-secondary"]:hover:not(:disabled), button[kind="secondary"]:hover:not(:disabled) {
    background-color: var(--mf-surface-alt) !important;
    border-color: var(--mf-primary) !important;
}

[data-testid^="stBaseButton-"]:focus-visible, button:focus-visible {
    outline: 3px solid var(--mf-primary) !important;
    outline-offset: 2px !important;
}
[data-testid^="stBaseButton-"]:disabled, button:disabled {
    background-color: var(--mf-surface-alt) !important;
    border-color: var(--mf-border) !important;
    cursor: not-allowed;
}
[data-testid^="stBaseButton-"]:disabled *, button:disabled * {
    color: var(--mf-muted) !important;
    -webkit-text-fill-color: var(--mf-muted) !important;
}

/* ---------- Inputs ---------- */
.stTextInput input, .stTextArea textarea, [data-testid="stChatInput"] textarea {
    background: var(--mf-surface) !important;
    color: var(--mf-text) !important;
    -webkit-text-fill-color: var(--mf-text) !important;
    border-radius: 10px;
}
.stTextInput [data-baseweb="input"], .stTextArea [data-baseweb="textarea"] {
    background: var(--mf-surface) !important;
    border: 1px solid var(--mf-border-strong) !important;
    border-radius: 10px !important;
}
.stTextInput [data-baseweb="input"]:focus-within, .stTextArea [data-baseweb="textarea"]:focus-within {
    border-color: var(--mf-primary) !important;
    box-shadow: 0 0 0 1px var(--mf-primary) !important;
}
::placeholder { color: var(--mf-muted) !important; opacity: 1 !important; -webkit-text-fill-color: var(--mf-muted) !important; }

[data-testid="stChatInput"] {
    background: var(--mf-surface) !important;
    border: 1px solid var(--mf-border-strong) !important;
    border-radius: 14px;
}
[data-testid="stBottom"], [data-testid="stBottom"] > div { background: var(--mf-background) !important; }
[data-testid="stChatInput"] > div, [data-testid="stChatInput"] [data-baseweb="textarea"] { background: var(--mf-surface) !important; }

/* Selectbox: new markup (stSelectbox > [role=group]) and the older baseweb markup */
[data-testid="stSelectbox"] [role="group"],
div[data-baseweb="select"] > div, div[data-baseweb="select"] > div > div {
    background: var(--mf-surface) !important;
    border-radius: 10px !important;
}
[data-testid="stSelectbox"] [role="group"], div[data-baseweb="select"] > div {
    border: 1px solid var(--mf-border-strong) !important;
}
[data-testid="stSelectbox"] input, [data-testid="stSelectbox"] [role="group"] *,
div[data-baseweb="select"] * { color: var(--mf-text) !important; -webkit-text-fill-color: var(--mf-text) !important; }
[data-testid="stSelectbox"] svg, div[data-baseweb="select"] svg { fill: var(--mf-text) !important; }

/* Open option list (rendered in a popover outside the page flow) */
[data-baseweb="popover"] ul, [data-baseweb="popover"] [data-baseweb="menu"],
[role="listbox"] { background: var(--mf-surface) !important; }
[data-baseweb="popover"] li, [role="option"] { background: var(--mf-surface) !important; color: var(--mf-text) !important; }
[data-baseweb="popover"] li *, [role="option"] * { color: var(--mf-text) !important; }
[data-baseweb="popover"] li:hover, [role="option"]:hover,
[data-baseweb="popover"] li[aria-selected="true"], [role="option"][aria-selected="true"] {
    background: var(--mf-surface-alt) !important;
}

[data-testid="stFileUploaderDropzone"] {
    background: var(--mf-surface-alt);
    border: 1px dashed var(--mf-border-strong);
    border-radius: 13px;
}
[data-testid="stFileUploaderDropzone"] * { color: var(--mf-text); }
[data-testid="stFileUploaderDropzone"] small { color: var(--mf-muted) !important; }

/* ---------- Chat ---------- */
[data-testid="stChatMessage"] {
    border: 1px solid var(--mf-border);
    border-radius: 15px;
    padding: 12px 14px;
    margin-bottom: 10px;
    background: var(--mf-assistant-bubble);
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]),
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background: var(--mf-user-bubble);
}

/* ---------- Tabs ---------- */
[data-baseweb="tab-list"] { gap: 8px; }
[data-baseweb="tab"], [data-baseweb="tab"] * { color: var(--mf-muted) !important; font-weight: 600; }
[aria-selected="true"][data-baseweb="tab"], [aria-selected="true"][data-baseweb="tab"] * {
    color: var(--mf-primary) !important;
}
[data-baseweb="tab-highlight"] { background-color: var(--mf-primary) !important; }

/* ---------- Radio (sidebar nav) ---------- */
[data-testid="stRadio"] label { padding: 2px 0; }
"""

st.markdown(f"<style>{THEME_VARS}{BASE_CSS}</style>", unsafe_allow_html=True)


# --------------------------------------------------
# HELPERS
# --------------------------------------------------


def html_block(markup: str) -> str:
    """Collapse whitespace so Streamlit's markdown never treats indented HTML as code."""
    return " ".join(markup.split())


def as_markdown(value, empty: str, demote: bool = False) -> str:
    """The pipeline may return a string or a list - render both."""
    if value is None:
        return empty
    if isinstance(value, (list, tuple)):
        text = "\n".join(f"- {item}" for item in value)
    else:
        text = str(value)
    text = text.strip()
    if demote:
        text = demote_headings(text)
    return text or empty


def safe_filename(title: str) -> str:
    cleaned = "".join(c if c.isalnum() or c in "-_ " else "" for c in title).strip()
    return (cleaned.replace(" ", "_") or "meeting")[:60]


def build_report(entry: dict) -> str:
    result = entry["result"]
    return (
        f"# {result.get('title') or 'Untitled meeting'}\n\n"
        f"*Generated by MeetFlow · {entry['created_at']}*\n\n"
        f"## Summary\n{as_markdown(result.get('summary'), 'No summary was generated.')}\n\n"
        f"## Action items\n{as_markdown(result.get('action_items'), 'No action items found.')}\n\n"
        f"## Key decisions\n{as_markdown(result.get('key_decisions'), 'No decisions found.')}\n\n"
        f"## Open questions\n{as_markdown(result.get('open_questions'), 'No open questions found.')}\n\n"
        f"## Transcript\n{result.get('transcript', '')}\n"
    )


def build_chat_export(messages: list[dict]) -> str:
    return "\n".join(
        f"**{'You' if m['role'] == 'user' else 'MeetFlow'}:** {m['content']}\n"
        for m in messages
    )


def find_entry(meeting_id):
    for entry in st.session_state.meeting_history:
        if entry["id"] == meeting_id:
            return entry
    return None


def sync_chat_history() -> None:
    entry = find_entry(st.session_state.current_meeting_id)
    if entry is not None:
        entry["chat_history"] = list(st.session_state.chat_history)


def save_upload(uploaded_file) -> str:
    suffix = Path(uploaded_file.name).suffix or ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        return tmp.name


def find_snippets(transcript: str, query: str) -> list[str]:
    needle = query.strip()
    if not needle:
        return []
    sentences = re.split(r"(?<=[.!?])\s+|\n+", transcript)
    pattern = re.compile(re.escape(needle), re.IGNORECASE)
    return [
        pattern.sub(lambda m: f"**{m.group(0)}**", s)
        for s in sentences
        if pattern.search(s)
    ]


@contextmanager
def card():
    """A bordered container we can style reliably (a hidden marker tags it for CSS)."""
    with st.container(border=True):
        st.markdown('<span class="mf-card-marker"></span>', unsafe_allow_html=True)
        yield


def demote_headings(text: str) -> str:
    """AI text often contains '# Heading' lines - show them as bold so they don't dwarf the card title."""
    return re.sub(
        r"^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$", r"**\1**\n", text, flags=re.MULTILINE
    )


# ----- callbacks (run before widgets are drawn, so they may change widget state) -----


def open_meeting(meeting_id: str) -> None:
    entry = find_entry(meeting_id)
    if entry is None:
        return
    st.session_state.meeting = entry["result"]
    st.session_state.current_meeting_id = meeting_id
    st.session_state.chat_history = list(entry.get("chat_history", []))
    st.session_state.pending_question = None
    st.session_state.active_page = "New Meeting"


def delete_meeting(meeting_id: str) -> None:
    st.session_state.meeting_history = [
        e for e in st.session_state.meeting_history if e["id"] != meeting_id
    ]
    if st.session_state.current_meeting_id == meeting_id:
        st.session_state.meeting = None
        st.session_state.current_meeting_id = None
        st.session_state.chat_history = []


def go_to_new_meeting() -> None:
    st.session_state.active_page = "New Meeting"


def queue_question(question: str) -> None:
    st.session_state.pending_question = question


def clear_chat() -> None:
    st.session_state.chat_history = []
    sync_chat_history()


# ----- pipeline -----


def process_meeting(source: str, language: str, label: str) -> bool:
    """Run the pipeline with live progress. Returns True on success."""
    with st.status("MeetFlow is processing your meeting...", expanded=True) as status:

        def on_progress(step: int, total: int, message: str) -> None:
            st.write(f"**Step {step} of {total}** · {message}")

        try:
            if SUPPORTS_PROGRESS:
                result = run_pipeline(source, language, on_progress=on_progress)
            else:
                st.write("Transcribing, analysing and indexing your meeting...")
                result = run_pipeline(source, language)
        except PipelineError as exc:
            status.update(
                label="We couldn't process this meeting", state="error", expanded=True
            )
            st.error(str(exc))
            return False
        except Exception as exc:  # noqa: BLE001
            status.update(
                label="Something unexpected went wrong", state="error", expanded=True
            )
            st.error(
                "We couldn't process this meeting. Please try again or use another file."
            )
            with st.expander("Technical details"):
                st.exception(exc)
            return False

        elapsed = result.get("elapsed")
        done = "Your meeting is ready" + (f" · {elapsed}s" if elapsed else "")
        status.update(label=done, state="complete", expanded=False)

    meeting_id = uuid.uuid4().hex
    st.session_state.meeting = result
    st.session_state.current_meeting_id = meeting_id
    st.session_state.chat_history = []
    st.session_state.pending_question = None
    st.session_state.meeting_history.insert(
        0,
        {
            "id": meeting_id,
            "title": result.get("title") or "Untitled meeting",
            "created_at": datetime.now().strftime("%b %d, %Y · %I:%M %p"),
            "source": label,
            "language": language,
            "summary": as_markdown(result.get("summary"), ""),
            "result": result,
            "chat_history": [],
        },
    )
    return True


def ask_meeting(meeting: dict, question: str) -> str:
    """
    Answer predefined questions using extracted meeting data.
    Use RAG for other custom questions.
    """

    normalized_question = re.sub(r"[\W_]+", " ", question.lower()).strip()

    # Direct answers from the meeting analysis
    direct_answers = {
        "what are the main takeaways": ("summary", "No meeting summary was generated."),
        "what decisions were made": (
            "key_decisions",
            "No decisions were found in this meeting.",
        ),
        "list the action items": (
            "action_items",
            "No action items were found in this meeting.",
        ),
        "what questions remain open": (
            "open_questions",
            "No open questions were found in this meeting.",
        ),
    }

    # Use extracted results for predefined questions
    if normalized_question in direct_answers:

        field, fallback = direct_answers[normalized_question]

        return as_markdown(meeting.get(field), fallback)

    # Use RAG for general questions
    rag_chain = meeting.get("rag_chain")

    if rag_chain is None:
        return (
            "Chat isn't available for this meeting because "
            "its search index couldn't be built."
        )

    try:
        return str(answer_question(rag_chain, question))

    except Exception as exc:
        return f"Sorry, I couldn't answer that question: {exc}"


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:
    st.markdown('<div class="brand-title">◉ MeetFlow</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="brand-subtitle">AI Meeting Assistant</div>', unsafe_allow_html=True
    )
    st.divider()

    st.markdown('<div class="side-label">WORKSPACE</div>', unsafe_allow_html=True)
    page = st.radio(
        "Navigation",
        ["New Meeting", "Meeting History", "Settings"],
        key="active_page",
        label_visibility="collapsed",
    )
    st.caption(f"{len(st.session_state.meeting_history)} meeting(s) in this session")
    st.divider()

    st.markdown('<div class="side-label">APPEARANCE</div>', unsafe_allow_html=True)
    st.selectbox("Color theme", list(THEMES.keys()), key="selected_theme")
    st.caption("Soft light themes with high-contrast buttons and text.")
    st.divider()

    st.markdown(
        '<div class="small-muted">Whisper · Sarvam · Groq<br>HuggingFace · ChromaDB</div>',
        unsafe_allow_html=True,
    )

if st.session_state.flash:
    st.toast(st.session_state.flash, icon="✅")
    st.session_state.flash = None


# --------------------------------------------------
# NEW MEETING PAGE
# --------------------------------------------------

if page == "New Meeting":
    st.markdown('<div class="page-title">Good to see you</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Turn conversations into clear notes, decisions, and next steps.</div>',
        unsafe_allow_html=True,
    )

    with card():
        st.subheader("Create a meeting workspace")

        source_type = st.radio(
            "Choose your source",
            ["YouTube link", "Upload recording"],
            horizontal=True,
        )

        youtube_url = ""
        uploaded_file = None

        if source_type == "YouTube link":
            youtube_url = st.text_input(
                "YouTube URL",
                placeholder="Paste a YouTube meeting or video link",
            )
        else:
            uploaded_file = st.file_uploader(
                "Choose an audio or video file",
                type=["mp3", "wav", "m4a", "mp4", "mov", "mpeg", "webm"],
            )

        language = st.selectbox(
            "Meeting language",
            ["english", "hinglish"],
            format_func=lambda value: "English" if value == "english" else "Hinglish",
        )

        start_processing = st.button(
            "Process meeting", type="primary", use_container_width=True
        )

    if start_processing:
        source, label, temp_path = None, "", None

        if source_type == "YouTube link":
            url = youtube_url.strip()
            if not url:
                st.warning("Please paste a YouTube URL.")
            elif not url.lower().startswith(("http://", "https://")):
                st.warning(
                    "That doesn't look like a valid link. It should start with https://"
                )
            else:
                source, label = url, url
        elif uploaded_file is None:
            st.warning("Please choose an audio or video file.")
        else:
            temp_path = save_upload(uploaded_file)
            source, label = temp_path, uploaded_file.name

        if source:
            try:
                success = process_meeting(source, language, label)
            finally:
                if temp_path:
                    Path(temp_path).unlink(missing_ok=True)
            if success:
                st.session_state.flash = "Meeting processed successfully"
                st.rerun()

    # --------------------------------------------------
    # MEETING WORKSPACE
    # --------------------------------------------------

    meeting = st.session_state.meeting
    entry = find_entry(st.session_state.current_meeting_id)

    if meeting:
        title = meeting.get("title") or "Untitled meeting"
        transcript = str(meeting.get("transcript", ""))
        words = len(transcript.split())

        st.markdown("## Your meeting")

        meta_bits = []
        if entry:
            meta_bits += [entry["created_at"], entry["language"].title()]
        caption = " · ".join(meta_bits) or "AI-generated meeting workspace"
        st.markdown(
            html_block(f"""<div class="meeting-banner">
                <div class="meeting-banner-title">{html.escape(title)}</div>
                <div class="meeting-banner-caption">{html.escape(caption)}</div>
                </div>"""),
            unsafe_allow_html=True,
        )

        m1, m2, m3 = st.columns(3)
        m1.metric("Transcript words", f"{words:,}")
        m2.metric("Estimated read time", f"{max(1, round(words / 200))} min")
        elapsed = meeting.get("elapsed")
        m3.metric("Processed in", f"{elapsed}s" if elapsed else "—")

        for warning in meeting.get("warnings", []) or []:
            st.warning(f"Partial result · {warning}")

        st.write("")
        overview_tab, transcript_tab = st.tabs(["Overview", "Transcript"])

        with overview_tab:
            summary_col, action_col = st.columns([1.35, 1])
            with summary_col:
                with card():
                    st.subheader("Meeting summary")
                    st.markdown(
                        as_markdown(
                            meeting.get("summary"),
                            "No summary was generated.",
                            demote=True,
                        )
                    )
            with action_col:
                with card():
                    st.subheader("Action items")
                    st.markdown(
                        as_markdown(
                            meeting.get("action_items"),
                            "No action items found.",
                            demote=True,
                        )
                    )

            decision_col, question_col = st.columns(2)
            with decision_col:
                with card():
                    st.subheader("Key decisions")
                    st.markdown(
                        as_markdown(
                            meeting.get("key_decisions"),
                            "No decisions found.",
                            demote=True,
                        )
                    )
            with question_col:
                with card():
                    st.subheader("Open questions")
                    st.markdown(
                        as_markdown(
                            meeting.get("open_questions"),
                            "No open questions found.",
                            demote=True,
                        )
                    )

            if entry:
                st.download_button(
                    "Download full report",
                    data=build_report(entry),
                    file_name=f"{safe_filename(title)}_report.md",
                    mime="text/markdown",
                    key="download_report",
                )

        with transcript_tab:
            st.subheader("Meeting transcript")
            query = st.text_input(
                "Search the transcript",
                placeholder="Search for a word or phrase...",
                key=f"search_{st.session_state.current_meeting_id}",
            )
            if query.strip():
                hits = find_snippets(transcript, query)
                st.caption(f"{len(hits)} matching sentence(s)")
                for hit in hits[:40]:
                    st.markdown(f"> {hit}")
            else:
                st.text_area(
                    "Transcript",
                    value=transcript,
                    height=420,
                    label_visibility="collapsed",
                    key=f"transcript_{st.session_state.current_meeting_id}",
                )
            st.download_button(
                "Download transcript",
                data=transcript,
                file_name=f"{safe_filename(title)}_transcript.txt",
                mime="text/plain",
                key="download_transcript",
            )

        # ----- chat (kept outside the tabs so the input stays pinned) -----
        st.markdown("---")
        st.subheader("Ask your meeting")
        st.caption("Answers come from this meeting's transcript only.")

        if not st.session_state.chat_history:
            st.markdown("**Try asking**")
            prompt_cols = st.columns(2)
            for index, starter in enumerate(STARTER_QUESTIONS):
                with prompt_cols[index % 2]:
                    st.button(
                        starter,
                        key=f"starter_{index}",
                        use_container_width=True,
                        on_click=queue_question,
                        args=(starter,),
                    )

        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        typed_question = st.chat_input("Ask a follow-up question about this meeting...")
        question = typed_question or st.session_state.pending_question
        st.session_state.pending_question = None

        if question:
            st.session_state.chat_history.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)
            with st.chat_message("assistant"):
                with st.spinner("MeetFlow is thinking..."):
                    answer = ask_meeting(meeting, question)
                st.markdown(answer)
            st.session_state.chat_history.append(
                {"role": "assistant", "content": answer}
            )
            sync_chat_history()

        if st.session_state.chat_history:
            c1, c2, _ = st.columns([1, 1, 3])
            c1.button(
                "Clear chat",
                key="clear_chat",
                on_click=clear_chat,
                use_container_width=True,
            )
            c2.download_button(
                "Export chat",
                data=build_chat_export(st.session_state.chat_history),
                file_name=f"{safe_filename(title)}_chat.md",
                mime="text/markdown",
                key="export_chat",
                use_container_width=True,
            )


# --------------------------------------------------
# MEETING HISTORY PAGE
# --------------------------------------------------

elif page == "Meeting History":
    st.markdown('<div class="page-title">Meeting history</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Reopen a meeting and continue where you left off.</div>',
        unsafe_allow_html=True,
    )

    history = st.session_state.meeting_history

    if not history:
        with card():
            st.markdown("### No meetings yet")
            st.write("Your processed meetings will appear here.")
            st.button(
                "Create your first meeting", type="primary", on_click=go_to_new_meeting
            )
    else:
        st.caption(f"{len(history)} meeting(s) saved in this session.")

        for item in history:
            with card():
                left, right = st.columns([4, 1])

                with left:
                    st.markdown(f"**{item['title']}**")
                    st.caption(f"{item['created_at']} · {item['language'].title()}")
                    preview = (
                        re.sub(r"[#*_`>]+", "", item.get("summary", ""))
                        .replace("\n", " ")
                        .strip()
                    )
                    if len(preview) > 220:
                        preview = preview[:220].rstrip() + "..."
                    st.write(preview or "No summary available.")
                    if item.get("chat_history"):
                        st.caption(
                            f"{len(item['chat_history']) // 2} question(s) asked"
                        )

                with right:
                    st.button(
                        "Open meeting",
                        key=f"open_{item['id']}",
                        type="primary",
                        use_container_width=True,
                        on_click=open_meeting,
                        args=(item["id"],),
                    )
                    st.button(
                        "Delete",
                        key=f"delete_{item['id']}",
                        use_container_width=True,
                        on_click=delete_meeting,
                        args=(item["id"],),
                    )


# --------------------------------------------------
# SETTINGS PAGE
# --------------------------------------------------

elif page == "Settings":
    st.markdown('<div class="page-title">Settings</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Personalize your MeetFlow workspace.</div>',
        unsafe_allow_html=True,
    )

    with card():
        st.subheader("Appearance")
        st.write(f"Selected theme: **{st.session_state.selected_theme}**")
        st.write(
            "Change it from the sidebar. Every theme keeps button and text contrast at WCAG AA or better."
        )
        chips = "".join(
            f'<span class="swatch-chip"><span class="swatch" style="background:{t["primary"]}"></span>'
            f'<span class="swatch" style="background:{t["background"]}"></span>{html.escape(name)}</span>'
            for name, t in THEMES.items()
        )
        st.markdown(f'<div class="swatch-row">{chips}</div>', unsafe_allow_html=True)

    with card():
        st.subheader("AI services")
        st.write("Speech transcription: Whisper / Sarvam AI")
        st.write("Language model: Groq")
        st.write("Embeddings: HuggingFace")
        st.write("Vector database: ChromaDB")

    with card():
        st.subheader("Meeting history")
        st.write(
            "History is stored in Streamlit session state, so it resets when the session "
            "is cleared or the app restarts. Database persistence can be added later."
        )
