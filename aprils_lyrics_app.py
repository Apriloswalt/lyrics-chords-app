# lyrics_chords_app/main.py

import streamlit as st
import numpy as np
import os
import json
import time
from datetime import datetime
import soundfile as sf
from fpdf import FPDF

CHORDS = ["C", "D", "E", "F", "G", "A", "B"]
CHORD_ALTER = ["#", "b", "m", "7", "maj", "min", "sus", "dim", "aug"]
NOTE_ORDER = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

st.set_page_config(layout="wide")

# Dummy session init (replace with real load logic as needed)
if "selected_song" not in st.session_state:
    st.session_state["selected_song"] = "Demo"
    st.session_state["songs"] = {
        "Demo": "Verse 1\n[C]Hello [G]world\n[F]This is a [C]song\nChorus\n[C]Sing it [G]loud\n[F]Sing it [C]proud"
    }
    st.session_state["section_order"] = {"order_Demo": ["Verse 1", "Chorus"]}
    st.session_state["section_rename"] = {"rename_Demo": {"Verse 1": "Verse", "Chorus": "Chorus"}}
    st.session_state["section_notes"] = {"notes_Demo": {"Verse 1": "Start soft.", "Chorus": "Sing strong."}}

# --- Transposition ---
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

# --- Display & Print Preview ---
if st.session_state.get("selected_song"):
    st.subheader("Song Preview")
    song_key = st.session_state["selected_song"]
    order = st.session_state["section_order"].get(f"order_{song_key}", [])
    renames = st.session_state["section_rename"].get(f"rename_{song_key}", {})
    notes = st.session_state["section_notes"].get(f"notes_{song_key}", {})
    raw_text = st.session_state["songs"][song_key].splitlines()

    sections = {}
    current = "Intro"
    for line in raw_text:
        if any(header in line for header in ["Verse", "Chorus", "Bridge"]):
            current = line.strip()
            sections[current] = []
        else:
            sections.setdefault(current, []).append(line)

    for sec in order:
        st.markdown(f"### {renames.get(sec, sec)}")
        if notes.get(sec):
            st.markdown(f"*{notes[sec]}*")
        for line in sections.get(sec, []):
            style = "font-family:monospace;font-size:18px"
            if "[" in line and "]" in line:
                parts = line.split("[")
                new_line = parts[0]
                for chunk in parts[1:]:
                    chord, *rest = chunk.split("]", 1)
                    rest_text = rest[0] if rest else ""
                    chord_display = chord if show_original else transpose_chord(chord, transpose_shift)
                    new_line += f"<b style='color:red'>[{chord_display}]</b>{rest_text}"
                st.markdown(f"<div style='{style};background:#f5f5f5;padding:2px'>{new_line}</div>", unsafe_allow_html=True)
            else:
                words = line.split()
                if any(w[0] in CHORDS for w in words):
                    line_type = "chord"
                else:
                    line_type = "lyric"
                transposed = [w if show_original else transpose_chord(w, transpose_shift) for w in words]
                color = "#f5f5f5" if line_type == "lyric" else "#eef"
                st.markdown(f"<div style='{style};background:{color};padding:2px'>{' '.join(transposed)}</div>", unsafe_allow_html=True)

    st.subheader("Print Layout Preview")
    for sec in order:
        st.markdown(f"### {renames.get(sec, sec)}")
        if notes.get(sec):
            st.markdown(f"*{notes[sec]}*")
        for line in sections.get(sec, []):
            if "[" in line and "]" in line:
                parts = line.split("[")
                rendered = parts[0]
                for chunk in parts[1:]:
                    chord, *rest = chunk.split("]", 1)
                    rest_text = rest[0] if rest else ""
                    chord_display = chord if show_original else transpose_chord(chord, transpose_shift)
                    rendered += f"[{chord_display}]{rest_text}"
                st.code(rendered)
            else:
                words = line.split()
                transposed = [w if show_original else transpose_chord(w, transpose_shift) for w in words]
                st.code(" ".join(transposed))
