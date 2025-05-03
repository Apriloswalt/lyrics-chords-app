# lyrics_chords_app/main.py

import streamlit as st
import numpy as np
import os
import json
import time
from datetime import datetime
import soundfile as sf
from fpdf import FPDF
import fitz  # PyMuPDF

CHORDS = ["C", "D", "E", "F", "G", "A", "B"]
CHORD_ALTER = ["#", "b", "m", "7", "maj", "min", "sus", "dim", "aug"]
NOTE_ORDER = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

st.set_page_config(layout="wide")

SETTINGS_FILE = "user_settings.json"
SESSION_FILE = "session_data.json"

def load_session():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, 'r') as f:
            st.session_state.update(json.load(f))

def save_session():
    data = {k: v for k, v in st.session_state.items() if isinstance(v, (dict, list, str, int, float))}
    with open(SESSION_FILE, 'w') as f:
        json.dump(data, f)

load_session()

if "songs" not in st.session_state:
    st.session_state["songs"] = {}
if "playlist" not in st.session_state:
    st.session_state["playlist"] = []
if "selected_song" not in st.session_state:
    st.session_state["selected_song"] = None
if "section_order" not in st.session_state:
    st.session_state["section_order"] = {}
if "section_rename" not in st.session_state:
    st.session_state["section_rename"] = {}
if "section_notes" not in st.session_state:
    st.session_state["section_notes"] = {}
if "tap_times" not in st.session_state:
    st.session_state["tap_times"] = []

# --- PDF Upload ---
def extract_text_from_pdf(uploaded_file):
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    return "\n".join(page.get_text() for page in doc)

uploaded = st.sidebar.file_uploader("Upload Song PDF", type=["pdf"])
if uploaded:
    song_name = uploaded.name.replace(".pdf", "")
    raw = extract_text_from_pdf(uploaded)
    st.session_state["songs"][song_name] = raw
    st.session_state["playlist"].append(song_name)
    st.session_state["selected_song"] = song_name
    save_session()

st.sidebar.text_input("Search for lyrics online", placeholder="Not yet implemented")

if st.session_state["playlist"]:
    st.sidebar.selectbox("Select Song", st.session_state["playlist"], key="selected_song")

def transpose_chord(chord, shift):
    base = chord
    for alt in CHORD_ALTER:
        if alt in chord:
            base = chord.split(alt)[0]
            suffix = chord[len(base):]
            break
    else:
        suffix = ""
    if base not in NOTE_ORDER:
        return chord
    idx = (NOTE_ORDER.index(base) + shift) % 12
    return NOTE_ORDER[idx] + suffix

transpose_shift = st.sidebar.slider("Transpose Key", -6, 6, 0)
show_original = st.sidebar.checkbox("Show Original Chords", value=False)

bpm_key = "bpm_input"
if bpm_key not in st.session_state:
    st.session_state[bpm_key] = 120
col1, col2 = st.sidebar.columns(2)
if col1.button("Tap Tempo"):
    now = time.time()
    st.session_state["tap_times"].append(now)
    if len(st.session_state["tap_times"]) >= 2:
        intervals = np.diff(st.session_state["tap_times"][-5:])
        if len(intervals) > 0:
            new_bpm = int(60.0 / np.mean(intervals))
            st.session_state[bpm_key] = new_bpm
            st.sidebar.success(f"Estimated BPM: {new_bpm}")
if col2.button("Reset Taps"):
    st.session_state["tap_times"] = []

if st.session_state["selected_song"]:
    song_key = st.session_state["selected_song"]
    raw_text = st.session_state["songs"][song_key].splitlines()
    sections = {}
    current = "Intro"
    for line in raw_text:
        if any(h in line for h in ["Verse", "Chorus", "Bridge"]):
            current = line.strip()
            sections[current] = []
        else:
            sections.setdefault(current, []).append(line)

    names = list(sections.keys())
    order_key, rename_key, note_key = f"order_{song_key}", f"rename_{song_key}", f"notes_{song_key}"
    if order_key not in st.session_state["section_order"]:
        st.session_state["section_order"][order_key] = names
    if rename_key not in st.session_state["section_rename"]:
        st.session_state["section_rename"][rename_key] = {n: n for n in names}
    if note_key not in st.session_state["section_notes"]:
        st.session_state["section_notes"][note_key] = {n: "" for n in names}

    st.subheader("Arrange and Edit Sections")
    order = st.multiselect("Section Order", names, default=st.session_state["section_order"][order_key], key=order_key)
    renames = st.session_state["section_rename"][rename_key]
    notes = st.session_state["section_notes"][note_key]

    for sec in order:
        st.text_input(f"Rename '{sec}'", value=renames[sec], key=f"r_{sec}")
        st.text_area(f"Notes for '{sec}'", value=notes[sec], key=f"n_{sec}")
        renames[sec] = st.session_state[f"r_{sec}"]
        notes[sec] = st.session_state[f"n_{sec}"]

    st.subheader("Song Preview")
    for sec in order:
        st.markdown(f"### {renames[sec]}")
        if notes[sec]:
            st.markdown(f"*{notes[sec]}*")
        for line in sections[sec]:
            if "[" in line and "]" in line:
                parts = line.split("[")
                new_line = parts[0]
                for chunk in parts[1:]:
                    chord, *rest = chunk.split("]", 1)
                    chord_disp = chord if show_original else transpose_chord(chord, transpose_shift)
                    new_line += f"<b style='color:red'>[{chord_disp}]</b>{rest[0] if rest else ''}"
                st.markdown(f"<div style='font-family:monospace;font-size:18px'>{new_line}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<pre>{line}</pre>")

    save_session()

    # --- Export Buttons ---
    export_txt = st.sidebar.button("Export as .txt")
    export_pdf = st.sidebar.button("Export as PDF")

    if export_txt:
        lines = []
        for sec in order:
            lines.append(renames[sec])
            if notes[sec]:
                lines.append(f"[{notes[sec]}]")
            lines.extend(sections[sec])
            lines.append("")
        file_content = "\n".join(lines)
        st.download_button("Download .txt", data=file_content, file_name=f"{song_key}.txt")

    if export_pdf:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for sec in order:
            pdf.set_font("Arial", "B", 14)
            pdf.cell(200, 10, txt=renames[sec], ln=True)
            if notes[sec]:
                pdf.set_font("Arial", "I", 12)
                pdf.multi_cell(0, 10, txt=f"[{notes[sec]}]")
            pdf.set_font("Arial", size=12)
            for line in sections[sec]:
                pdf.multi_cell(0, 10, txt=line)
            pdf.ln()
        output_path = f"/tmp/{song_key}.pdf"
        pdf.output(output_path)
        with open(output_path, "rb") as f:
            st.download_button("Download PDF", data=f, file_name=f"{song_key}.pdf")

    # --- Auto Scroll ---
    auto_scroll = st.sidebar.checkbox("Enable Auto-Scroll")
    scroll_mode = st.sidebar.radio("Scroll Mode", ["Manual", "Sync with BPM"])
    scroll_speed = st.sidebar.slider("Scroll Speed", 10, 100, 40) if scroll_mode == "Manual" else None

    if auto_scroll:
        container = st.empty()
        bpm = st.session_state.get("bpm_input", 60)
        beat_interval = 60.0 / bpm if bpm > 0 else 1.0
        for _ in range(300):
            container.markdown("<script>window.scrollBy(0, 3);</script>", unsafe_allow_html=True)
            time.sleep(1.0 / scroll_speed if scroll_mode == "Manual" else beat_interval)

    # --- Rehearsal Mode, Fullscreen & Font Scaling ---
    font_scale = st.sidebar.slider("Font Scale %", 50, 200, 100)
    st.markdown(f"""
    <style>
    html, body, .block-container, .stMarkdown, .stText, .stCode {{
        font-size: {font_scale * 0.14}px;
    }}
    </style>
    """, unsafe_allow_html=True)

    rehearsal = st.sidebar.checkbox("Enable Rehearsal Mode")
    if rehearsal:
        countdown = st.sidebar.number_input("Countdown (sec)", 0, 60, 5)
        st.sidebar.write("Starting in:")
        counter = st.empty()
        for i in range(countdown, 0, -1):
            counter.write(f"{i}...")
            time.sleep(1)
        counter.write("Go!")
        bpm = st.session_state.get("bpm_input", 60)
        beat_interval = 60.0 / bpm if bpm > 0 else 1.0
        container = st.empty()
        for _ in range(300):
            container.markdown("<script>window.scrollBy(0, 3);</script>", unsafe_allow_html=True)
            time.sleep(beat_interval)

    if st.sidebar.checkbox("Fullscreen Lyrics View"):
        st.markdown("""
        <style>
        [data-testid="stSidebar"], [data-testid="stHeader"] {
            display: none;
        }
        .block-container {
            padding-top: 1rem;
        }
        html, body {
            background-color: #111;
            color: white;
        }
        .stText, .stMarkdown, .stCode {
            color: white;
        }
        </style>
        """, unsafe_allow_html=True)
        st.title(renames[order[0]] if order else "Lyrics")
