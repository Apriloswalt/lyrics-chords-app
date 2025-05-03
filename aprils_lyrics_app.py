# lyrics_chords_app/main.py

# ... [unchanged imports and existing functions remain intact] ...

import matplotlib.pyplot as plt
import numpy as np
import librosa
import librosa.display
import soundfile as sf
import simpleaudio as sa
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


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f)


def save_session():
    data = {
        "annotations": st.session_state.get("annotations", {}),
        "section_order": {
            k.replace("order_", ""): v
            for k, v in st.session_state.items() if k.startswith("order_")
        },
        "songs": st.session_state.get("songs", {}),
        "playlists": st.session_state.get("playlists", {})
    }
    with open(SESSION_FILE, 'w') as f:
        json.dump(data, f)
    push_undo(data)


def load_session():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, 'r') as f:
            data = json.load(f)
            apply_session_data(data)


def apply_session_data(data):
    st.session_state["annotations"] = data.get("annotations", {})
    for song, order in data.get("section_order", {}).items():
        st.session_state[f"order_{song}"] = order
    st.session_state["songs"] = data.get("songs", {})
    st.session_state["playlists"] = data.get("playlists", {})


def push_undo(data):
    stack = []
    if os.path.exists(UNDO_STACK):
        with open(UNDO_STACK, 'r') as f:
            stack = json.load(f)
    stack.append(data)
    with open(UNDO_STACK, 'w') as f:
        json.dump(stack[-10:], f)  # keep only last 10 states
    # Clear redo stack when new change is made
    if os.path.exists(REDO_STACK):
        os.remove(REDO_STACK)


def pop_undo():
    if os.path.exists(UNDO_STACK):
        with open(UNDO_STACK, 'r') as f:
            stack = json.load(f)
        if len(stack) > 1:
            last = stack.pop()
            with open(UNDO_STACK, 'w') as f:
                json.dump(stack, f)
            push_redo(last)
            return stack[-1]
    return None


def push_redo(data):
    stack = []
    if os.path.exists(REDO_STACK):
        with open(REDO_STACK, 'r') as f:
            stack = json.load(f)
    stack.append(data)
    with open(REDO_STACK, 'w') as f:
        json.dump(stack[-10:], f)


def pop_redo():
    if os.path.exists(REDO_STACK):
        with open(REDO_STACK, 'r') as f:
            stack = json.load(f)
        if stack:
            last = stack.pop()
            with open(REDO_STACK, 'w') as f:
                json.dump(stack, f)
            push_undo(last)
            return last
    return None


# Load persistent settings
settings = load_settings()
for key, val in settings.items():
    if key not in st.session_state:
        st.session_state[key] = val

# Load full session with confirmation
if os.path.exists(SESSION_FILE):
    if st.sidebar.checkbox("Restore previous session", value=True):
        load_session()

# Undo/Redo controls
with st.sidebar.expander("🕘 History / Undo"):
    if st.button("Undo Last Change"):
        prev = pop_undo()
        if prev:
            apply_session_data(prev)
            st.experimental_rerun()
        else:
            st.warning("Nothing to undo.")
    if st.button("Redo Last Change"):
        redo = pop_redo()
        if redo:
            apply_session_data(redo)
            st.experimental_rerun()
        else:
            st.warning("Nothing to redo.")

# --- Multi-Song Session State ---
# [unchanged]
