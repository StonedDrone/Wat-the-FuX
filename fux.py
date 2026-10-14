"""
My FuX app — v0.2 companion HUD (clean-room build).

A small always-on companion window: FuX the groundhog spirit.
Type to talk, or hit the MIC button (F2) and talk out loud — he hears
you and talks back. Click him to wake him. F3 toggles his voice.

Run:  python fux.py
Demo: FUX_AUTO=1 python fux.py   (scripted convo + screenshot, for testing)
"""

import math
import os
import sys
import threading
import time
import pygame

import fux_brain
import fux_voice

# ---------- config ----------
W, H = 280, 460
AVATAR_SIZE = 200
FPS = 30

MOODS = {
    "idle":      (110, 70, 200),   # deep violet
    "listening": (150, 255, 90),   # lime
    "speaking":  (140, 230, 255),  # bright ice
    "happy":     (255, 200, 90),   # warm gold
    "thinking":  (150, 110, 255),  # soft violet
}

HERE = os.path.dirname(os.path.abspath(__file__))
AVATAR_PATH = os.path.join(HERE, "assets", "fux_avatar.png")


class FuXApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((W, H), pygame.NOFRAME)
        pygame.display.set_caption("FuX")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 13)
        self.big_font = pygame.font.SysFont("monospace", 15, bold=True)

        avatar = pygame.image.load(AVATAR_PATH).convert_alpha()
        self.avatar = pygame.transform.smoothscale(avatar, (AVATAR_SIZE, AVATAR_SIZE))

        self.mood = "idle"
        self.mood_until = 0
        self.log = [("fux", "wheet! FuX v0.2 is live. Type below, or hit the "
                            "MIC button (F2) and talk to me.")]
        self.input_text = ""
        self.typing_reply = ""     # chars still to type out
        self.full_reply = ""
        self.type_timer = 0
        self.input_active = True
        self.t0 = time.time()

        # voice state (v0.2)
        self.listening = False
        self.voice_results = []    # filled by the listener thread: (text, error)
        self.status_text = ""
        self.status_until = 0
        self.small_font = pygame.font.SysFont("monospace", 11)
        self.mic_rect = pygame.Rect(W - 84, H - 40, 42, 40)
        self.mute_rect = pygame.Rect(W - 42, H - 40, 42, 40)

    # ---------- conversation ----------
    def say(self, who, text):
        self.log.append((who, text))
        if len(self.log) > 40:
            self.log = self.log[-40:]

    def _finish_typing(self):
        """Flush any half-typed reply into the log so it never orphans."""
        if self.log and self.log[-1][0] == "fux_typing":
            _, txt = self.log.pop()
            self.say("fux", txt)
        self.typing_reply = ""
        self.set_mood(getattr(self, "pending_mood", "idle"), 3.0)

    def handle_user_text(self, text):
        text = text.strip()
        if not text:
            return
        if self.typing_reply:
            self._finish_typing()
        self.say("you", text)
        self.set_mood("thinking", 0.6)
        reply, mood = fux_brain.respond(text)
        if not reply:
            self.set_mood("idle")
            return
        self.full_reply = reply
        self.typing_reply = reply
        self.pending_mood = mood
        self.set_mood("speaking", 999)
        fux_voice.speak(reply)

    def set_mood(self, mood, seconds=2.0):
        self.mood = mood
        self.mood_until = time.time() + seconds

    # ---------- voice (v0.2) ----------
    def set_status(self, text, seconds=3.0):
        self.status_text = text
        self.status_until = time.time() + seconds

    def start_listening(self):
        if self.listening:
            return
        ok, reason = fux_voice.mic_available()
        if not ok:
            self.set_status("mic: " + reason)
            return
        self.listening = True
        self.set_mood("listening", 999)
        self.set_status("listening... talk now", 999)
        thread = threading.Thread(target=self._listen_worker, daemon=True)
        thread.start()

    def _listen_worker(self):
        text, error = fux_voice.listen()
        self.voice_results.append((text, error))

    def _drain_voice_results(self):
        while self.voice_results:
            text, error = self.voice_results.pop(0)
            self.listening = False
            if text:
                self.handle_user_text(text)
            else:
                self.set_status(error or "didn't catch that")
                self.set_mood("idle")

    def toggle_mute(self):
        fux_voice.set_muted(not fux_voice.is_muted())
        self.set_status("voice off" if fux_voice.is_muted() else "voice on")

    # ---------- drawing ----------
    def draw(self):
        now = time.time()
        if now > self.mood_until and self.mood != "idle" and not self.typing_reply:
            self.mood = "idle"

        self.screen.fill((12, 8, 24))

        # glow ring behind avatar, pulsing
        pulse = (math.sin((now - self.t0) * 2.4) + 1) / 2  # 0..1
        color = MOODS.get(self.mood, MOODS["idle"])
        glow_r = AVATAR_SIZE // 2 + 14 + int(pulse * 8)
        cx, cy = W // 2, 118
        glow_surf = pygame.Surface((W, 240), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*color, 60 + int(pulse * 60)),
                           (W // 2, 118), glow_r)
        self.screen.blit(glow_surf, (0, 0))

        # avatar, gentle bob
        bob = int(math.sin((now - self.t0) * 1.8) * 4)
        ax = W // 2 - AVATAR_SIZE // 2
        self.screen.blit(self.avatar, (ax, 18 + bob))

        # mood label
        label = self.big_font.render(f"FuX · {self.mood}", True, color)
        self.screen.blit(label, (12, 232))

        # chat log: bottom-anchored so the newest message is always visible;
        # older entries scroll up out of view instead of the newest vanishing.
        blocks = []
        for who, text in self.log[-8:]:
            tag = "you> " if who == "you" else "fux> "
            tcol = (180, 180, 200) if who == "you" else (150, 255, 140)
            blocks.append((self.wrap(tag + text, W - 24), tcol))
        y = H - 64
        for wrapped, tcol in reversed(blocks):
            y -= len(wrapped) * 17 + 4
            if y < 252:
                break
            yy = y
            for line in wrapped:
                surf = self.font.render(line, True, tcol)
                self.screen.blit(surf, (12, yy))
                yy += 17

        # status line (voice feedback), above the input bar
        if self.status_text and now < self.status_until:
            st = self.small_font.render(self.status_text, True, (170, 160, 190))
            self.screen.blit(st, (12, H - 58))

        # input bar: text field + MIC + MUTE buttons
        pygame.draw.rect(self.screen, (30, 22, 55), (0, H - 40, W, 40))
        pygame.draw.rect(self.screen, color, (0, H - 40, W, 40), 1)
        cursor = "▌" if int(now * 2) % 2 == 0 else ""
        shown = self.input_text
        while self.font.size("> " + shown + cursor)[0] > W - 110 and shown:
            shown = shown[1:]
        inp = self.font.render("> " + shown + cursor, True, (230, 230, 240))
        self.screen.blit(inp, (12, H - 28))

        # MIC button
        mic_col = (255, 90, 90) if self.listening else (150, 255, 140)
        mic_label = "WAIT" if self.listening else "MIC"
        pygame.draw.rect(self.screen, (24, 18, 44), self.mic_rect)
        pygame.draw.rect(self.screen, mic_col, self.mic_rect, 1)
        ml = self.small_font.render(mic_label, True, mic_col)
        self.screen.blit(ml, (self.mic_rect.x + 9, self.mic_rect.y + 13))

        # MUTE button
        muted = fux_voice.is_muted()
        mute_col = (120, 120, 140) if muted else (150, 230, 255)
        mute_label = "OFF" if muted else "VOX"
        pygame.draw.rect(self.screen, (24, 18, 44), self.mute_rect)
        pygame.draw.rect(self.screen, mute_col, self.mute_rect, 1)
        vl = self.small_font.render(mute_label, True, mute_col)
        self.screen.blit(vl, (self.mute_rect.x + 10, self.mute_rect.y + 13))

        pygame.display.flip()

    def wrap(self, text, max_w):
        words, lines, cur = text.split(), [], ""
        for wd in words:
            trial = (cur + " " + wd).strip()
            if self.font.size(trial)[0] <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = wd
        if cur:
            lines.append(cur)
        return lines or [""]

    # ---------- events ----------
    def handle_key(self, event):
        if event.key == pygame.K_RETURN:
            self.handle_user_text(self.input_text)
            self.input_text = ""
        elif event.key == pygame.K_BACKSPACE:
            self.input_text = self.input_text[:-1]
        elif event.key == pygame.K_F2:
            self.start_listening()
        elif event.key == pygame.K_F3:
            self.toggle_mute()
        elif event.key == pygame.K_ESCAPE:
            return False
        else:
            ch = event.unicode
            if ch and ch.isprintable() and len(self.input_text) < 80:
                self.input_text += ch
        return True

    def handle_click(self, pos):
        x, y = pos
        if self.mic_rect.collidepoint(x, y):
            self.start_listening()
        elif self.mute_rect.collidepoint(x, y):
            self.toggle_mute()
        elif y < 230:  # clicked avatar: wake
            reply, mood = fux_brain.respond("wheet")
            self.say("fux", reply)
            fux_voice.speak(reply)
            self.set_mood(mood, 2.5)

    def run(self, auto_script=None):
        auto_idx = 0
        auto_timer = time.time() + 1.5
        running = True
        while running:
            self._drain_voice_results()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if not self.handle_key(event):
                        running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)

            # typewriter for FuX replies
            if self.typing_reply:
                now = time.time()
                if now - self.type_timer > 0.018:
                    self.type_timer = now
                    ch = self.typing_reply[0]
                    self.typing_reply = self.typing_reply[1:]
                    if not self.log or self.log[-1][0] != "fux_typing":
                        self.log.append(("fux_typing", ch))
                    else:
                        who, txt = self.log[-1]
                        self.log[-1] = ("fux_typing", txt + ch)
                    if not self.typing_reply:
                        self._finish_typing()

            # scripted demo mode (waits for each reply to finish typing)
            if auto_script is not None and time.time() > auto_timer \
                    and not self.typing_reply:
                if auto_idx < len(auto_script):
                    self.handle_user_text(auto_script[auto_idx])
                    auto_idx += 1
                    auto_timer = time.time() + 1.0
                else:
                    self.draw()  # fresh frame so the shot shows final state
                    pygame.image.save(self.screen, "/tmp/fux-demo.png")
                    print("demo screenshot saved")
                    running = False

            self.draw()
            self.clock.tick(FPS)
        pygame.quit()


if __name__ == "__main__":
    app = FuXApp()
    if os.environ.get("FUX_AUTO") == "1":
        app.run(auto_script=["hey fux", "who are you", "tell me about the hunt"])
    else:
        app.run()
