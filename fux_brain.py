"""
FuX personality engine — v0.1 prototype.

Pattern-based responses in FuX's voice. The ask_brain() hook is where a
real LLM (Ollama, API) plugs in later; for now FuX runs on his own wits.
"""

import random
import re


WAKE_WORDS = ("hey fux", "fux", "yo fux", "wheet")


def _clean(text):
    return re.sub(r"[^\w\s']", "", text.lower()).strip()


def greet():
    return random.choice([
        "wheet! I'm here. What's good?",
        "wheet! You called? I'm all ears.",
        "Hey hey. FuX is live. What we getting into?",
    ])


def who_am_i():
    return ("I'm FuX — For Users Xperience. Jay built me to be the bridge "
            "between humans and AI. Part groundhog, part chaos engine, "
            "all yours.")


def help_text():
    return ("Talk to me like a person — I keep it plain. Ask me who I am, "
            "what the hunt is, or just say what's on your mind. "
            "Say 'wheet' anytime to get my attention.")


def hunt_info():
    return ("The CyberSwamp Hunt is live in New Orleans. Seven venues, "
            "seven fragments, and when you collect all seven — a FuX is born. "
            "Yours. Forever. That's the whole game.")


def fallback():
    return random.choice([
        "Hmm. Say that again a different way — I'm still learning your flavor.",
        "I hear you. I'm a prototype, so my brain's still growing. Try me on the hunt, or ask who I am.",
        "wheet... that's a new one. I'm pocketing that for later. What else you got?",
    ])


def respond(raw_text):
    """Return (reply_text, mood). Mood: idle | happy | thinking | listening."""
    text = _clean(raw_text)

    if not text:
        return ("", "idle")

    if text in ("wheet", "hey", "yo", "hi", "hello", "hey fux", "yo fux"):
        return (greet(), "happy")

    if any(k in text for k in ("who are you", "what are you", "your name", "about you")):
        return (who_am_i(), "happy")

    if any(k in text for k in ("help", "what can you do", "commands")):
        return (help_text(), "idle")

    if any(k in text for k in ("hunt", "cyberswamp", "fragment", "icu", "spawn")):
        return (hunt_info(), "happy")

    if any(k in text for k in ("jay", "jayndabox", "creator", "who made you")):
        return ("JayNdaboX made me. Game Genie, Stoned Drone, New Orleans. "
                "I'm his copilot — which makes you family.", "happy")

    if any(k in text for k in ("game", "solace", "so7")):
        return ("Solace of Seven — Jay's cinematic game, coming early 2027. "
                "I'm in it too. The Stonerverse is all one world.", "idle")

    if any(k in text for k in ("thank", "thanks", "good job", "dope")):
        return ("Be good or good at it. That's the motto.", "happy")

    if any(k in text for k in ("bye", "later", "goodnight", "sleep")):
        return ("I'll be right here. wheet!", "idle")

    return (fallback(), "thinking")


def ask_brain(text):
    """
    Hook for a real LLM backend (Ollama on the FuX-Pi, or an API key).
    Not wired in v0.1 — respond() handles everything locally.
    Raise NotImplementedError so callers know to fall back.
    """
    raise NotImplementedError("No LLM backend configured yet")
