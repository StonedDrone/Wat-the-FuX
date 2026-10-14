"""
Voice-layer self-test. Proves the app survives machines with no mic,
no speakers, and no TTS engine — everything must degrade gracefully.
Run:  venv/bin/python test_voice.py
"""

import time
import fux_voice


def check(name, fn):
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — a crash here IS the failure
        print("FAIL %-28s crashed: %s" % (name, exc))
        return False
    print("ok   %s" % name)
    return True


results = []

# 1. mic probe never raises, always returns a (bool, str) pair
def t_mic():
    ok, reason = fux_voice.mic_available()
    assert isinstance(ok, bool) and isinstance(reason, str), (ok, reason)
    print("     mic_available ->", ok, "|", reason or "(ready)")
results.append(check("mic_available() never crashes", t_mic))

# 2. speak() with no audio device must return instantly and silently
def t_speak():
    t0 = time.time()
    fux_voice.speak("wheet! voice test one two three")
    time.sleep(2.5)  # let the background thread attempt TTS
    assert time.time() - t0 < 10, "speak() blocked too long"
results.append(check("speak() degrades without audio", t_speak))

# 3. muted speak() does nothing at all
def t_muted():
    fux_voice.set_muted(True)
    assert fux_voice.is_muted() is True
    fux_voice.speak("you should not hear this")
    fux_voice.set_muted(False)
    assert fux_voice.is_muted() is False
results.append(check("mute toggle works", t_muted))

# 4. listen() with no usable mic returns (None, reason) — never hangs/raises
def t_listen():
    ok, _ = fux_voice.mic_available()
    t0 = time.time()
    text, error = fux_voice.listen(timeout=1, phrase_time_limit=2)
    dt = time.time() - t0
    assert text is None or isinstance(text, str)
    assert isinstance(error, str)
    assert dt < 30, "listen() hung too long: %.1fs" % dt
    print("     listen -> text=%r error=%r (%.1fs)" % (text, error, dt))
results.append(check("listen() degrades without mic", t_listen))

# 5. brain still answers (voice layer must not break text chat)
def t_brain():
    import fux_brain
    reply, mood = fux_brain.respond("who are you")
    assert reply and mood in ("idle", "happy", "thinking", "listening")
results.append(check("text brain unaffected", t_brain))

print()
print("PASS" if all(results) else "FAIL", "%d/%d voice tests" % (sum(results), len(results)))
raise SystemExit(0 if all(results) else 1)
