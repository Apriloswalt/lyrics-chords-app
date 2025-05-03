# lyrics_chords_app/main.py

import streamlit as st
import numpy as np
import soundfile as sf
from fpdf import FPDF
import fitz
import json
import os
from datetime import datetime
import time

st.set_page_config(layout="wide")

# Session Initialization
for key, default in {
    "songs": {},
    "playlist": [],
    "playlists": {},
    "selected_song": None,
    "section_order": {},
    "section_rename": {},
    "section_notes": {},
    "tap_times": [],
    "undo_stack": [],
    "redo_stack": [],
    "bpm": 100,
    "transposition": 0
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# Sidebar Controls
st.sidebar.title("🎵 Playlist Manager & Tools")
playlist_name = st.sidebar.text_input("New Playlist Name")
if st.sidebar.button("➕ Create Playlist") and playlist_name:
    st.session_state.playlists[playlist_name] = []
selected_playlist = st.sidebar.selectbox("Select Playlist", list(st.session_state.playlists.keys()) or ["None"])
if selected_playlist != "None":
    songs_to_add = st.sidebar.multiselect("Add Songs to Playlist", list(st.session_state.songs.keys()))
    if st.sidebar.button("📥 Update Playlist"):
        st.session_state.playlists[selected_playlist] = songs_to_add

# Tap Tempo & Playback
st.sidebar.subheader("⏱️ Tempo & Scroll")
if st.sidebar.button("🖱️ Tap Tempo"):
    st.session_state.tap_times.append(time.time())
    if len(st.session_state.tap_times) >= 2:
        intervals = np.diff(st.session_state.tap_times[-5:])
        bpm = 60 / np.mean(intervals)
        st.session_state["bpm"] = int(bpm)
if st.sidebar.button("🔄 Reset Tap"):
    st.session_state.tap_times = []
st.session_state["bpm"] = st.sidebar.number_input("BPM", 40, 240, st.session_state["bpm"])
scroll = st.sidebar.checkbox("Auto-scroll with BPM")
if scroll:
    st.markdown(f"<meta http-equiv='refresh' content='{60/st.session_state['bpm']}'>", unsafe_allow_html=True)

# Transposition
st.sidebar.subheader("🎼 Transpose Chords")
st.session_state["transposition"] = st.sidebar.slider("Key Change (semitones)", -6, 6, 0)

# Rehearsal Countdown
if st.sidebar.checkbox("Enable Rehearsal Countdown"):
    count = st.sidebar.number_input("Countdown Seconds", 1, 10, 3)
    if st.sidebar.button("▶ Start Rehearsal"):
        for i in reversed(range(count)):
            st.warning(f"Starting in {i+1}...")
            time.sleep(1)
        st.success("🎶 Go!")

# Fullscreen + Dark Theme
fullscreen = st.sidebar.checkbox("🎭 Fullscreen Mode")
dark = st.sidebar.checkbox("🌙 Dark Theme")
font_scale = st.sidebar.slider("Font Scale %", 50, 200, 100)

# PDF Upload & Parsing
st.title("Lyrics & Chords Manager")
uploaded = st.file_uploader("Upload PDF", type="pdf")
if uploaded:
    with fitz.open(stream=uploaded.read(), filetype="pdf") as doc:
        text = "".join([page.get_text() for page in doc])
    lines = text.splitlines()
    current = "Intro"
    chords, lyrics = {}, []
    for line in lines:
        if any(k in line.lower() for k in ["verse", "chorus", "bridge", "intro", "outro", "interlude"]):
            current = line.strip().title()
            continue
        if all(token.strip().isalpha() and len(token.strip()) <= 4 for token in line.split()):
            chords.setdefault(current, []).append(line)
        elif line.strip():
            lyrics.append(line)
    st.session_state["classified_chords"] = chords
    st.session_state["classified_lyrics"] = lyrics

# Editable Section UI
if "classified_chords" in st.session_state:
    st.subheader("🪕 Chord Sections")
    for sec, lines in st.session_state["classified_chords"].items():
        col1, col2 = st.columns([3, 1])
        with col1:
            raw = "\n".join(lines)
            edited = st.text_area(f"{sec} Chords", value=raw, height=100)
            st.session_state["classified_chords"][sec] = edited.splitlines()
        with col2:
            note = st.text_input(f"Note for {sec}", value=st.session_state["section_notes"].get(sec, ""))
            st.session_state["section_notes"][sec] = note

if "classified_lyrics" in st.session_state:
    st.subheader("🎤 Lyrics")
    raw = "\n".join(st.session_state["classified_lyrics"])
    edited = st.text_area("Lyrics", value=raw, height=200)
    st.session_state["classified_lyrics"] = edited.splitlines()

# Undo/Redo
if st.button("Undo") and st.session_state["undo_stack"]:
    st.session_state["redo_stack"].append(st.session_state["classified_chords"])
    st.session_state["classified_chords"] = st.session_state["undo_stack"].pop()
if st.button("Redo") and st.session_state["redo_stack"]:
    st.session_state["undo_stack"].append(st.session_state["classified_chords"])
    st.session_state["classified_chords"] = st.session_state["redo_stack"].pop()

# Save Song
if st.button("📦 Save Song from Sections"):
    final = []
    for sec, lines in st.session_state.get("classified_chords", {}).items():
        final.append(f"## {sec}")
        final.extend(lines)
        if st.session_state["section_notes"].get(sec):
            final.append(f"[Note] {st.session_state['section_notes'][sec]}")
    final.append("## Lyrics")
    final.extend(st.session_state.get("classified_lyrics", []))
    song_key = f"song_{datetime.now().strftime('%H%M%S')}"
    st.session_state["songs"][song_key] = "\n".join(final)
    st.session_state["playlist"].append(song_key)
    st.session_state["selected_song"] = song_key

# Export Tools
if st.session_state.get("selected_song"):
    txt = st.session_state["songs"][st.session_state["selected_song"]]
    st.download_button("📄 Download TXT", txt, file_name="song.txt")
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in txt.splitlines():
        pdf.cell(200, 10, txt=line, ln=True)
    pdf_path = "/tmp/song.pdf"
    pdf.output(pdf_path)
    with open(pdf_path, "rb") as f:
        st.download_button("🖨️ Download PDF", f.read(), file_name="song.pdf")

# Web Search Stub
st.sidebar.subheader("🔍 Import From Web (Stub)")
st.sidebar.text_input("Search for song on Ultimate Guitar")

# Fullscreen Theme Styling
if fullscreen or dark:
    st.markdown(
        f"<style>body {{ background: black; color: white; font-size: {font_scale}%; }}</style>",
        unsafe_allow_html=True,
    )
