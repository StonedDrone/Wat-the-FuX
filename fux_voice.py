"""
FuX voice layer — v0.2.

Written fresh for FuX (clean-room: no third-party companion code copied in;
SpeechRecognition and pyttsx3 are used as libraries, the same as pygame).

- listen(): one-shot push-to-talk capture from the mic, returns text.
- speak(): reads text aloud in a background thread so the window never freezes.
- Everything degrades gracefully: no mic / no speakers / missing packages
  never crash the app — the caller gets a plain-English reason instead.
"""

import threading

_muted = False
_speak_lock = threading.Lock()


# ---------- mute ----------
def set_muted(muted):
    global _muted
    _muted = bool(muted)


def is_muted():
    return _muted


# ---------- listening ----------
def mic_available():
    """(ok, reason): can we open a microphone right now? Never raises."""
    try:
        import speech_recognition as sr
    except ImportError:
        return False, "voice input needs the SpeechRecognition package"
    try:
        names = sr.Microphone.list_microphone_names()
    except Exception as exc:
        return False, "couldn't list microphones: %s" % exc
    if not names:
        return False, "no microphone found on this machine"
    return True, ""


def listen(timeout=6, phrase_time_limit=15):
    """
    Wait up to `timeout` seconds for speech, then transcribe it.
    Returns (text, error): text is None when nothing usable was heard.
    Blocks — call from a worker thread, never the UI thread.
    """
    try:
        import speech_recognition as sr
    except ImportError:
        return None, "voice input needs the SpeechRecognition package"

    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.4)
            audio = recognizer.listen(source, timeout=timeout,
                                      phrase_time_limit=phrase_time_limit)
    except sr.WaitTimeoutError:
        return None, "didn't hear anything — try again"
    except OSError as exc:
        return None, "mic unavailable: %s" % exc
    except Exception as exc:
        return None, "mic error: %s" % exc

    try:
        return recognizer.recognize_google(audio), ""
    except sr.UnknownValueError:
        return None, "couldn't make that out — say it again"
    except sr.RequestError:
        return None, "speech service unreachable (offline?)"
    except Exception as exc:
        return None, "transcription hiccup: %s" % exc


# ---------- speaking ----------
def speak(text):
    """
    Read text aloud in a background thread. Returns immediately.
    Silent no-op when muted, when there's no text, or when TTS is
    unavailable (no speakers / no engine) — the app keeps working.
    """
    if _muted or not text or not text.strip():
        return

    def _run():
        try:
            import pyttsx3
            with _speak_lock:
                engine = pyttsx3.init()
                try:
                    engine.setProperty("rate", 175)
                    engine.say(text)
                    engine.runAndWait()
                finally:
                    try:
                        engine.stop()
                    except Exception:
                        pass
        except Exception:
            # No TTS engine / no audio device: stay silent, keep going.
            pass

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
