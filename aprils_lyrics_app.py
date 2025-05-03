# lyrics_chords_app/main.py

[previous code preserved...]

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
