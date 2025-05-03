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

SETTINGS_FILE = "user_settings.json"
SESSION_FILE = "session_data.json"

# --- Initialization ---
if "songs" not in st.session_state:
    st.session_state.songs = {}
if "playlist" not in st.session_state:
    st.session_state.playlist = []
if "playlists" not in st.session_state:
    st.session_state.playlists = {}
if "selected_song" not in st.session_state:
    st.session_state.selected_song = None
if "section_order" not in st.session_state:
    st.session_state.section_order = {}
if "section_rename" not in st.session_state:
    st.session_state.section_rename = {}
if "section_notes" not in st.session_state:
    st.session_state.section_notes = {}

# --- Sidebar: Playlist Manager ---
st.sidebar.title("🎵 Playlist Manager")
playlist_name = st.sidebar.text_input("New Playlist Name")
if st.sidebar.button("➕ Create Playlist") and playlist_name:
    st.session_state.playlists[playlist_name] = []
selected_playlist = st.sidebar.selectbox("Select Playlist", list(st.session_state.playlists.keys()) or ["None"])
if selected_playlist != "None":
    songs_to_add = st.sidebar.multiselect("Add Songs to Playlist", list(st.session_state.songs.keys()))
    if st.sidebar.button("📥 Update Playlist"):
        st.session_state.playlists[selected_playlist] = songs_to_add

# --- PDF Upload + Classification ---
st.title("Lyrics & Chords Manager")
uploaded = st.file_uploader("Upload PDF with Lyrics/Chords", type="pdf")
if uploaded:
    text = ""
    with fitz.open(stream=uploaded.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    lines = text.splitlines()
    current = "Intro"
    chords = {}
    lyrics = []
    for line in lines:
        if any(k in line.lower() for k in ["verse", "chorus", "intro", "bridge", "outro", "interlude"]):
            current = line.strip().title()
            continue
        if all(token.strip().isalpha() and len(token.strip()) <= 4 for token in line.split()):
            chords.setdefault(current, []).append(line)
        else:
            lyrics.append(line)

    st.session_state["classified_chords"] = chords
    st.session_state["classified_lyrics"] = lyrics

# --- Editable Chord & Lyrics Sections ---
if "classified_chords" in st.session_state:
    st.subheader("🎼 Edit Chord Sections")
    for sec, lines in st.session_state["classified_chords"].items():
        raw = "\n".join(lines)
        edited = st.text_area(f"{sec} Chords", value=raw, height=100)
        st.session_state["classified_chords"][sec] = edited.splitlines()

if "classified_lyrics" in st.session_state:
    st.subheader("📝 Edit Lyrics")
    raw = "\n".join(st.session_state["classified_lyrics"])
    edited = st.text_area("Lyrics", value=raw, height=200)
    st.session_state["classified_lyrics"] = edited.splitlines()

if st.button("📦 Build Song from Sections"):
    final = []
    for sec, lines in st.session_state["classified_chords"].items():
        final.append(f"## {sec}")
        final.extend(lines)
    final.append("## Lyrics")
    final.extend(st.session_state["classified_lyrics"])
    song_key = f"song_{datetime.now().strftime('%H%M%S')}"
    st.session_state["songs"][song_key] = "\n".join(final)
    st.session_state["playlist"].append(song_key)
    st.session_state["selected_song"] = song_key

# --- Playback Tools ---
st.sidebar.subheader("Tempo & Scroll")
if "tap_times" not in st.session_state:
    st.session_state.tap_times = []
if st.sidebar.button("🖱️ Tap Tempo"):
    st.session_state.tap_times.append(time.time())
    if len(st.session_state.tap_times) >= 2:
        intervals = np.diff(st.session_state.tap_times[-5:])
        bpm = 60 / np.mean(intervals)
        st.session_state["bpm"] = int(bpm)
if st.sidebar.button("🔄 Reset Tap"):
    st.session_state.tap_times = []

bpm = st.sidebar.number_input("BPM", min_value=40, max_value=240, value=st.session_state.get("bpm", 100))
scroll = st.sidebar.checkbox("Auto-scroll with BPM")
if scroll:
    st.markdown(f"<meta http-equiv='refresh' content='{60/bpm}'>", unsafe_allow_html=True)

# --- Export ---
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
