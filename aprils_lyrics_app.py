# lyrics_chords_app/main.py

import streamlit as st
import numpy as np
import soundfile as sf
from fpdf import FPDF
import fitz
import os
from datetime import datetime
import time

st.set_page_config(layout="wide")

# Initialize session state
defaults = {
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
    "transposition": 0,
    "lyrics_field": "",
    "chord_fields": {},
    "load_into_editors": False
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Sidebar
st.sidebar.title("🎵 Playlist & Performance")
playlist_name = st.sidebar.text_input("New Playlist Name")
if st.sidebar.button("➕ Create Playlist") and playlist_name:
    st.session_state.playlists[playlist_name] = []
selected_playlist = st.sidebar.selectbox("Select Playlist", list(st.session_state.playlists.keys()) or ["None"])
if selected_playlist != "None":
    songs_to_add = st.sidebar.multiselect("Add Songs to Playlist", list(st.session_state.songs.keys()))
    if st.sidebar.button("📥 Update Playlist"):
        st.session_state.playlists[selected_playlist] = songs_to_add

st.sidebar.subheader("⏱️ Tempo Tools")
if st.sidebar.button("🖱️ Tap Tempo"):
    st.session_state.tap_times.append(time.time())
    if len(st.session_state.tap_times) >= 2:
        intervals = np.diff(st.session_state.tap_times[-5:])
        st.session_state["bpm"] = int(60 / np.mean(intervals))
if st.sidebar.button("🔄 Reset Tap"):
    st.session_state.tap_times = []
st.session_state["bpm"] = st.sidebar.number_input("BPM", 40, 240, st.session_state["bpm"])
if st.sidebar.checkbox("Auto-scroll with BPM"):
    st.markdown(f"<meta http-equiv='refresh' content='{60/st.session_state['bpm']}'>", unsafe_allow_html=True)

st.sidebar.subheader("🎼 View Settings")
st.session_state["transposition"] = st.sidebar.slider("Transpose", -6, 6, 0)
if st.sidebar.checkbox("Enable Rehearsal Countdown"):
    count = st.sidebar.number_input("Countdown Seconds", 1, 10, 3)
    if st.sidebar.button("▶ Start Rehearsal"):
        for i in reversed(range(count)):
            st.warning(f"Starting in {i+1}...")
            time.sleep(1)
        st.success("🎶 Go!")
fullscreen = st.sidebar.checkbox("Fullscreen Mode")
dark = st.sidebar.checkbox("Dark Theme")
font_scale = st.sidebar.slider("Font Scale %", 50, 200, 100)

# Upload PDF
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
    st.session_state["lyrics_field"] = "\n".join(lyrics)
    st.session_state["chord_fields"] = {sec: "\n".join(lines) for sec, lines in chords.items()}
    st.session_state["load_into_editors"] = True

# Chords UI
if "classified_chords" in st.session_state:
    st.subheader("🪕 Chord Sections")
    for sec in st.session_state["classified_chords"]:
        if st.session_state["load_into_editors"]:
            st.session_state[f"{sec}_text"] = st.session_state["chord_fields"].get(sec, "")
        val = st.session_state.get(f"{sec}_text", st.session_state["chord_fields"].get(sec, ""))
        edited = st.text_area(f"{sec} Chords", value=val, height=100, key=f"{sec}_text")
        st.session_state["classified_chords"][sec] = edited.splitlines()
        st.session_state["chord_fields"][sec] = edited
        note = st.text_input(f"Note for {sec}", value=st.session_state["section_notes"].get(sec, ""), key=f"{sec}_note")
        st.session_state["section_notes"][sec] = note

# Lyrics UI
if "classified_lyrics" in st.session_state:
    if st.session_state["load_into_editors"]:
        st.session_state["lyrics_box"] = st.session_state["lyrics_field"]
    val = st.session_state.get("lyrics_box", st.session_state["lyrics_field"])
    edited = st.text_area("🎤 Lyrics", value=val, height=200, key="lyrics_box")
    st.session_state["classified_lyrics"] = edited.splitlines()
    st.session_state["lyrics_field"] = edited

st.session_state["load_into_editors"] = False

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

# Export
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

# Web Import Stub
st.sidebar.subheader("🔍 Web Import (Stub)")
st.sidebar.text_input("Search for song")

# Fullscreen Theme
if fullscreen or dark:
    st.markdown(
        f"<style>body {{ background: black; color: white; font-size: {font_scale}%; }}</style>",
        unsafe_allow_html=True,
    )
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

# Initialize session state defaults
defaults = {
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
    "transposition": 0,
    "lyrics_field": "",
    "chord_fields": {},
    "loaded_from_pdf": False
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Sidebar Settings
st.sidebar.title("🎵 Playlist & Tools")
playlist_name = st.sidebar.text_input("New Playlist Name")
if st.sidebar.button("➕ Create Playlist") and playlist_name:
    st.session_state.playlists[playlist_name] = []
selected_playlist = st.sidebar.selectbox("Select Playlist", list(st.session_state.playlists.keys()) or ["None"])
if selected_playlist != "None":
    songs_to_add = st.sidebar.multiselect("Add Songs to Playlist", list(st.session_state.songs.keys()))
    if st.sidebar.button("📥 Update Playlist"):
        st.session_state.playlists[selected_playlist] = songs_to_add

st.sidebar.subheader("⏱️ Tempo + Scroll")
if st.sidebar.button("🖱️ Tap Tempo"):
    st.session_state.tap_times.append(time.time())
    if len(st.session_state.tap_times) >= 2:
        intervals = np.diff(st.session_state.tap_times[-5:])
        bpm = 60 / np.mean(intervals)
        st.session_state["bpm"] = int(bpm)
if st.sidebar.button("🔄 Reset Tap"):
    st.session_state.tap_times = []
st.session_state["bpm"] = st.sidebar.number_input("BPM", 40, 240, st.session_state["bpm"])
if st.sidebar.checkbox("Auto-scroll with BPM"):
    st.markdown(f"<meta http-equiv='refresh' content='{60/st.session_state['bpm']}'>", unsafe_allow_html=True)

st.sidebar.subheader("🎼 Transpose + View")
st.session_state["transposition"] = st.sidebar.slider("Transpose", -6, 6, 0)
if st.sidebar.checkbox("Enable Rehearsal Countdown"):
    count = st.sidebar.number_input("Countdown Seconds", 1, 10, 3)
    if st.sidebar.button("▶ Start Rehearsal"):
        for i in reversed(range(count)):
            st.warning(f"Starting in {i+1}...")
            time.sleep(1)
        st.success("🎶 Go!")

fullscreen = st.sidebar.checkbox("Fullscreen Mode")
dark = st.sidebar.checkbox("Dark Theme")
font_scale = st.sidebar.slider("Font Scale %", 50, 200, 100)

# PDF Upload
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
    st.session_state["lyrics_field"] = "\n".join(lyrics)
    st.session_state["chord_fields"] = {sec: "\n".join(lines) for sec, lines in chords.items()}
    st.session_state["loaded_from_pdf"] = True

# Chords Display
if "classified_chords" in st.session_state:
    st.subheader("🪕 Chord Sections")
    for sec in st.session_state["classified_chords"]:
        if st.session_state["loaded_from_pdf"]:
            st.session_state[f"{sec}_text"] = st.session_state["chord_fields"].get(sec, "")
        value = st.session_state.get(f"{sec}_text", st.session_state["chord_fields"].get(sec, ""))
        edited = st.text_area(f"{sec} Chords", value=value, height=100, key=f"{sec}_text")
        st.session_state["classified_chords"][sec] = edited.splitlines()
        st.session_state["chord_fields"][sec] = edited
        note = st.text_input(f"Note for {sec}", value=st.session_state["section_notes"].get(sec, ""), key=f"{sec}_note")
        st.session_state["section_notes"][sec] = note

# Lyrics Display
if "classified_lyrics" in st.session_state:
    if st.session_state["loaded_from_pdf"]:
        st.session_state["lyrics_box"] = st.session_state["lyrics_field"]
    value = st.session_state.get("lyrics_box", st.session_state["lyrics_field"])
    edited = st.text_area("🎤 Lyrics", value=value, height=200, key="lyrics_box")
    st.session_state["classified_lyrics"] = edited.splitlines()
    st.session_state["lyrics_field"] = edited

# Reset flag after first load
st.session_state["loaded_from_pdf"] = False

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

# Export
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

# Web Stub
st.sidebar.subheader("🔍 Web Import (Stub)")
st.sidebar.text_input("Search site for chords")

# Fullscreen Theme Styling
if fullscreen or dark:
    st.markdown(
        f"<style>body {{ background: black; color: white; font-size: {font_scale}%; }}</style>",
        unsafe_allow_html=True,
    )
