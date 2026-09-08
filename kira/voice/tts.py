import pyttsx3
import speech_recognition as sr
from config_loader import ENABLE_TTS, ENABLE_SPEECH

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False

# Callback to capture output
_output_callback = None

def set_voice_output_callback(callback):
    global _output_callback
    _output_callback = callback

def print_output(message):
    if _output_callback:
        _output_callback(message)
    else:
        print(message)

def speak(audio: str):
    if not ENABLE_TTS or not PYTTSX3_AVAILABLE:
        return
    try:
        import pythoncom
        pythoncom.CoInitialize()
    except Exception:
        pass
    local_engine = pyttsx3.init("sapi5")
    voices = local_engine.getProperty("voices")
    if voices:
        local_engine.setProperty("voice", voices[0].id)
    local_engine.say(audio)
    local_engine.runAndWait()

def takeCommand() -> str:
    if not ENABLE_SPEECH or not SR_AVAILABLE:
        return "None"
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print_output("Listening...")
        r.pause_threshold = 1
        try:
            audio = r.listen(source, timeout=8, phrase_time_limit=8)
        except sr.WaitTimeoutError:
            return "None"
    try:
        print_output("Recognizing...")
        query = r.recognize_google(audio, language="en-in")
        print_output(f"User said: {query}")
        return query
    except sr.UnknownValueError:
        speak("Say that again please...")
        return "None"
    except Exception as e:
        print_output(f"[ERROR] takeCommand: {e}")
        speak("Say that again please...")
        return "None"
