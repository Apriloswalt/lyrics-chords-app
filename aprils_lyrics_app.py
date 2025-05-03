# lyrics_chords_app/main.py

import matplotlib.pyplot as plt
import numpy as np
import librosa
import librosa.display
import soundfile as sf
from matplotlib.widgets import Cursor
import streamlit.components.v1 as components
import streamlit as st
import time
from datetime import datetime
import json
import os

SETTINGS_FILE = "user_settings.json"
SESSION_FILE = "session_data.json"
UNDO_STACK = "undo_stack.json"
REDO_STACK = "redo_stack.json"


def generate_metronome(bpm: int, duration: int, output_path: str):
    frequency = 1000
    click_len = 0.05
    sample_rate = 44100
    interval = 60.0 / bpm
    total_clicks = int(duration / interval)

    click = (np.sin(2 * np.pi * frequency * np.linspace(0, click_len, int(sample_rate * click_len))) * 0.5).astype(np.float32)
    silence = np.zeros(int(sample_rate * (interval - click_len)), dtype=np.float32)
    metronome = np.concatenate([np.concatenate([click, silence]) for _ in range(total_clicks)])

    sf.write(output_path, metronome, sample_rate)


def play_metronome(bpm: int, duration: int):
    output_path = "/tmp/metronome.wav"
    generate_metronome(bpm, duration, output_path)
    with open(output_path, "rb") as f:
        audio_data = f.read()
    st.audio(audio_data, format="audio/wav")


# Example Streamlit usage
st.title("Metronome Example")
bpm = st.number_input("BPM", min_value=30, max_value=300, value=120)
duration = st.number_input("Duration (s)", min_value=1, max_value=60, value=10)
if st.button("Play Metronome"):
    play_metronome(bpm, duration)
