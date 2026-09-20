import sys
import subprocess
import os

# ---------------------------------------------------------
# SAFE AUTO-RUNNER (PREVENTS REPEATED TAB OPENING)
# ---------------------------------------------------------
if __name__ == "__main__" and "STREAMLIT_RUNNING" not in os.environ:
    os.environ["STREAMLIT_RUNNING"] = "1"
    subprocess.run([sys.executable, "-m", "streamlit", "run", __file__])
    sys.exit()

import logging
import json
import random
import io

# Suppress Streamlit bare-mode warnings
logging.getLogger("streamlit.runtime.scriptrunner_utils.script_run_context").setLevel(logging.ERROR)

import nltk
import streamlit as st
import speech_recognition as sr
from gtts import gTTS
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline

# ---------------------------------------------------------
# 1. DOWNLOAD NLTK DATA & INITIALIZE PREPROCESSING
# ---------------------------------------------------------
@st.cache_resource
def setup_nltk():
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
    nltk.download('wordnet', quiet=True)

setup_nltk()
lemmatizer = WordNetLemmatizer()

def preprocess_text(text):
    tokens = nltk.word_tokenize(text.lower())
    clean_tokens = [lemmatizer.lemmatize(token) for token in tokens if token.isalnum()]
    return clean_tokens

# ---------------------------------------------------------
# 2. CREATE DEFAULT DATASET (intents.json) IF MISSING
# ---------------------------------------------------------
INTENTS_FILE = 'intents.json'

def create_default_intents():
    default_data = {
        "intents": [
            {
                "tag": "greeting",
                "patterns": ["Hi", "Hello", "Hey", "Good day", "What's up?", "Howdy"],
                "responses": ["Hello! How can I help you today?", "Hey there! What can I do for you?", "Hi! Nice to meet you."]
            },
            {
                "tag": "goodbye",
                "patterns": ["Bye", "See you later", "Goodbye", "Have a good day", "Catch you later"],
                "responses": ["Goodbye! Have a great day.", "Talk to you later!", "Bye! Feel free to reach out anytime."]
            },
            {
                "tag": "thanks",
                "patterns": ["Thanks", "Thank you", "That helps", "Awesome thanks", "Appreciate it"],
                "responses": ["You're welcome!", "Happy to help!", "Anytime! Let me know if you need more help."]
            },
            {
                "tag": "about_bot",
                "patterns": ["Who are you?", "What is your name?", "What can you do?", "Tell me about yourself"],
                "responses": ["I am an AI Chat Assistant built using Python, NLP, and Streamlit!", "I'm a rule-and-intent based AI designed to assist with your queries."]
            },
            {
                "tag": "help",
                "patterns": ["Help me", "I need support", "Can you help me?", "What should I ask?"],
                "responses": ["Sure! You can ask me about my background, say hi, or test my intent classification."]
            }
        ]
    }
    with open(INTENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(default_data, f, indent=4)

if not os.path.exists(INTENTS_FILE):
    create_default_intents()

# ---------------------------------------------------------
# 3. TRAIN INTENT CLASSIFICATION MODEL
# ---------------------------------------------------------
@st.cache_resource
def train_model():
    with open(INTENTS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    X, y = [], []
    for intent in data['intents']:
        for pattern in intent['patterns']:
            X.append(pattern)
            y.append(intent['tag'])

    pipeline = make_pipeline(
        TfidfVectorizer(tokenizer=preprocess_text, token_pattern=None),
        MultinomialNB()
    )
    pipeline.fit(X, y)
    return pipeline, data['intents']

model, intents_data = train_model()

# ---------------------------------------------------------
# 4. RESPONSE LOGIC & SPEECH HELPERS
# ---------------------------------------------------------
def get_bot_response(user_input):
    if not user_input.strip():
        return "Please enter a valid message."
    
    predicted_tag = model.predict([user_input])[0]
    
    for intent in intents_data:
        if intent['tag'] == predicted_tag:
            return random.choice(intent['responses'])
            
    return "I'm sorry, I didn't quite understand that."

def transcribe_audio(audio_bytes):
    """Converts recorded audio bytes into text using SpeechRecognition."""
    recognizer = sr.Recognizer()
    try:
        audio_file = sr.AudioFile(io.BytesIO(audio_bytes))
        with audio_file as source:
            audio_data = recognizer.record(source)
        return recognizer.recognize_google(audio_data)
    except Exception:
        return None

def text_to_speech(text):
    """Converts text response to an MP3 audio bytes stream."""
    tts = gTTS(text=text, lang='en')
    audio_fp = io.BytesIO()
    tts.write_to_fp(audio_fp)
    audio_fp.seek(0)
    return audio_fp

# ---------------------------------------------------------
# 5. STREAMLIT WEB GUI
# ---------------------------------------------------------
st.set_page_config(page_title="AI Voice Assistant", page_icon="🎙️")

st.title("🎙️ AI Voice & Text Chat Assistant")
st.caption("Powered by Python, NLTK, Scikit-Learn, Streamlit & gTTS")

with st.sidebar:
    st.header("Controls")
    enable_speech = st.checkbox("Enable Voice Responses (TTS)", value=True)
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am your AI assistant. Speak to me or type your message below!"}
    ]

# Render chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "audio" in message:
            st.audio(message["audio"], format="audio/mp3")

# Microphone Input Widget
audio_recording = st.audio_input("Record your voice message")

user_prompt = None

# Check audio input
if audio_recording:
    recorded_bytes = audio_recording.read()
    transcribed_text = transcribe_audio(recorded_bytes)
    if transcribed_text:
        user_prompt = transcribed_text
    else:
        st.error("Could not recognize speech. Please speak clearly and try again.")

# Text Input
text_prompt = st.chat_input("Or type your message here...")
if text_prompt:
    user_prompt = text_prompt

# Process prompt
if user_prompt:
    # 1. Display user message
    with st.chat_message("user"):
        st.markdown(user_prompt)
    st.session_state.messages.append({"role": "user", "content": user_prompt})

    # 2. Get bot reply
    bot_reply = get_bot_response(user_prompt)

    # 3. Generate voice output if enabled
    message_data = {"role": "assistant", "content": bot_reply}
    
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
        if enable_speech:
            audio_stream = text_to_speech(bot_reply)
            st.audio(audio_stream, format="audio/mp3", autoplay=True)
            message_data["audio"] = audio_stream

    st.session_state.messages.append(message_data)
