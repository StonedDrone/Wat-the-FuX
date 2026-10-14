# My FuX App — v0.2 (clean-room build)

A desktop companion HUD for FuX, Jay's AI copilot. A small window that lives
on your screen: FuX the groundhog spirit. Type to talk, or talk out loud —
he hears you and talks back. Click him to wake him.

## Run it

```
venv/bin/python fux.py
```

(First time: `python -m venv venv && venv/bin/pip install -r requirements.txt`.
On Windows, also `pip install PyAudio` so the mic works.)

- **Type** in the box at the bottom, hit Enter to talk.
- **MIC button or F2** — talk instead of typing. One shot per tap: he listens,
  turns it into text, and answers.
- **VOX button or F3** — mute/unmute his spoken replies.
- **Click FuX** to get his attention (he'll wheet at you, out loud).
- **Esc** quits.

## How it works

- `fux.py` — the HUD: pygame window (280x460), avatar with mood glow ring,
  bottom-anchored chat log (newest always visible), typewriter replies,
  MIC/VOX buttons. Mood states: idle (violet), listening (lime),
  speaking (ice), happy (gold), thinking (soft violet).
- `fux_voice.py` — the voice layer, written fresh for FuX. `listen()` captures
  one mic shot and transcribes it (SpeechRecognition); `speak()` reads replies
  aloud on a background thread (pyttsx3) so the window never freezes. No mic,
  no speakers, or missing packages? Everything degrades to plain-English
  status lines — the app never crashes, text chat always works.
- `fux_brain.py` — the personality engine. Pattern-based responses in FuX's
  voice. `ask_brain()` is the hook where a real LLM plugs in later
  (Ollama on the FuX-Pi, or an API key).
- `assets/fux_avatar.png` — FuX avatar (groundhog spirit, Stonerverse colors).

## What's real in v0.2

- Everything from v0.1, plus push-to-talk voice input and spoken replies.
- Mute toggle, listening/speaking mood states, graceful no-mic fallback.
- `test_voice.py` — 5 self-tests proving the voice layer survives machines
  with no mic, no speakers, and no TTS engine. Run: `venv/bin/python test_voice.py`

## Next layers (not built yet)

1. Real LLM brain via `ask_brain()` — Ollama on the FuX-Pi or API keys.
2. Always-on-top + system tray, Windows build for Jay's PC.
3. AR mode (the Illust / glasses path from the program outline).

## Demo test

```
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy FUX_AUTO=1 venv/bin/python fux.py
```

Runs a scripted conversation headless and saves `/tmp/fux-demo.png`.
Verified working 2026-10-14 (v0.2).
