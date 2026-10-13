import streamlit as st
import requests
import os
import pyttsx3
from fpdf import FPDF
import tempfile
import base64
import wave
import json
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from vosk import Model, KaldiRecognizer

# -----------------------------
# Configuration
# -----------------------------
BASE_URL = "http://localhost:8000"
VOSK_MODEL_PATH = r"C:\Users\mamid\Desktop\TutorIN\models\vosk-model-small-en-us-0.15"

# -----------------------------
# Initialize Vosk Model
# -----------------------------
if not os.path.exists(VOSK_MODEL_PATH):
    raise RuntimeError(f"❌ Vosk model path does not exist: {VOSK_MODEL_PATH}")

try:
    vosk_model = Model(VOSK_MODEL_PATH)
except Exception as e:
    raise RuntimeError(f"❌ Failed to initialize Vosk model: {str(e)}")

# -----------------------------
# Initialize TTS
# -----------------------------
tts_engine = pyttsx3.init()

# -----------------------------
# Helpers
# -----------------------------
def transcribe_audio_vosk(path):
    wf = wave.open(path, "rb")
    if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
        raise ValueError("Audio must be WAV mono PCM.")
    rec = KaldiRecognizer(vosk_model, wf.getframerate())
    result = ""
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            res = json.loads(rec.Result())
            result += res.get("text", "") + " "
    res = json.loads(rec.FinalResult())
    result += res.get("text", "")
    return result.strip()

def speak_text(text, speed=150):
    tts_engine.setProperty('rate', speed)
    tts_engine.say(text)
    tts_engine.runAndWait()

def export_chat_to_pdf(chat_history):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for sender, msg in chat_history:
        who = "You" if sender == "user" else "AI"
        pdf.multi_cell(0, 10, f"{who}: {msg}")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        return tmp.name

# -----------------------------
# Main Display
# -----------------------------
def display():
    st.subheader("💬 Chatbot Assistant")
    st.markdown("Use this assistant to ask tuition-related questions or generate homework tasks.")

    tabs = st.tabs(["🎙️ Voice/Text Chat", "📝 Generate Homework"])

    # === Tab 1: Chat ===
    with tabs[0]:
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        mode = st.radio("Input Mode", ["Text", "Voice"], horizontal=True)
        speak_response = st.checkbox("🔊 Speak Response", value=False)
        voice_speed = st.slider("🗣️ Voice Speed", 100, 250, 150)
        save_audio = st.checkbox("💾 Save My Audio", value=False)

        if mode == "Voice":
            st.info("🎤 Speak your query...")

            webrtc_ctx = webrtc_streamer(
                key="voice-mode",
                mode=WebRtcMode.SENDRECV,
                media_stream_constraints={"audio": True, "video": False},
                rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
                audio_receiver_size=1024,
                async_processing=True,
            )

            if webrtc_ctx.audio_receiver:
                try:
                    audio_frames = webrtc_ctx.audio_receiver.get_frames(timeout=3)
                    audio_bytes = b"".join([f.to_ndarray().tobytes() for f in audio_frames])
                    if audio_bytes:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                            tmp.write(audio_bytes)
                            audio_path = tmp.name

                        if save_audio:
                            st.success(f"🎧 Saved: {audio_path}")

                        query = transcribe_audio_vosk(audio_path)
                        os.remove(audio_path)

                        st.session_state.chat_history.append(("user", query))
                        res = requests.post(f"{BASE_URL}/chatbot/chat", json={"query": query}, timeout=10)
                        res.raise_for_status()
                        reply = res.json().get("response", "")
                        st.session_state.chat_history.append(("bot", reply))

                        if speak_response:
                            speak_text(reply, voice_speed)

                        st.success("✅ Transcription complete")

                except Exception as e:
                    st.error(f"❌ Transcription failed: {e}")

        else:
            user_text = st.text_input("💬 Type your question:")
            if st.button("Send Text"):
                if user_text.strip():
                    st.session_state.chat_history.append(("user", user_text))
                    try:
                        res = requests.post(f"{BASE_URL}/chatbot/chat", json={"query": user_text}, timeout=10)
                        res.raise_for_status()
                        reply = res.json().get("response", "")
                        st.session_state.chat_history.append(("bot", reply))
                        if speak_response:
                            speak_text(reply, voice_speed)
                    except Exception as e:
                        st.session_state.chat_history.append(("bot", f"❌ Error: {str(e)}"))
                else:
                    st.warning("⚠️ Please enter a question.")

        # --- Show chat history ---
        for sender, msg in reversed(st.session_state.chat_history):
            st.markdown(
                f"""
                <div style='text-align: {"right" if sender == "user" else "left"};
                            background-color: {"#dcf8c6" if sender == "user" else "#f1f0f0"};
                            padding: 10px; border-radius: 10px; margin: 5px 0;'>
                    <b>{"You" if sender == "user" else "AI"}:</b> {msg}
                </div>
                """, unsafe_allow_html=True)

        if st.button("🧾 Export Chat to PDF"):
            pdf_path = export_chat_to_pdf(st.session_state.chat_history)
            with open(pdf_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
                st.markdown(
                    f'<a href="data:application/pdf;base64,{b64}" download="chat_history.pdf">📄 Download Chat PDF</a>',
                    unsafe_allow_html=True
                )

    # === Tab 2: Homework ===
    with tabs[1]:
        with st.form("homework_form"):
            subject = st.text_input("📘 Subject")
            class_level = st.number_input("🎓 Class Level", 1, 12, 6)
            score = st.slider("📊 Last Test Score", 0, 100, 80)
            generate_btn = st.form_submit_button("✨ Generate Homework")

            if generate_btn:
                if not subject.strip():
                    st.warning("⚠️ Please enter a subject.")
                else:
                    try:
                        res = requests.post(
                            f"{BASE_URL}/chatbot/generate-homework",
                            json={"subject": subject, "class_level": class_level, "score": score},
                            timeout=10
                        )
                        res.raise_for_status()
                        task = res.json().get("generated_task", "")
                        if task:
                            st.success("✅ Homework:")
                            st.info(f"📌 {task}")
                        else:
                            st.error("⚠️ No task returned.")
                    except Exception as e:
                        st.error(f"❌ Failed to generate: {str(e)}")
