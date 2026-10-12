#!/usr/bin/env python3
"""Lumen Volley — neon vertical volley arcade for ElbowOS. Python 3 + pygame."""
import math, os, random, subprocess, sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv

if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/workspace/artifacts/LUMEN_VOLLEY_ElbowOS.mp4")
TITLE, HANDLE = "LUMEN VOLLEY", "x.com/ElbowOS"

# Neon palette — deep void + electric cyan / magenta / gold
VOID = (4, 6, 18)
CYAN = (0, 255, 255)
MAG = (255, 0, 180)
GOLD = (255, 200, 40)
WHITE = (240, 250, 255)
PADDLE_C = (0, 220, 255)
OPP_C = (255, 40, 160)

class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        flags = 0 if PLAY else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            self.screen = pygame.display.set_mode((W, H), pygame.HIDDEN)
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.font_big = pygame.font.SysFont("arialblack", 72, bold=True)
        self.font = pygame.font.SysFont("arial", 48, bold=True)
        self.font_sm = pygame.font.SysFont("arial", 36)
        self.reset()

    def reset(self):
        self.score = 0
        self.lives = 3
        self.frame = 0
        self.trail = []
        self.serve()

    def serve(self):
        self.ball_x = W // 2 + random.randint(-80, 80)
        self.ball_y = H // 2
        angle = random.uniform(-0.55, 0.55)
        speed = 11 + random.uniform(0, 3)
        self.vx = math.sin(angle) * speed
        self.vy = math.cos(angle) * speed * random.choice([-1, 1])
        self.paddle_x = W // 2
        self.opp_x = W // 2
        self.paddle_w = 180
        self.paddle_h = 28
        self.opp_w = 180
        self.ball_r = 18
        self.trail.clear()

    def update(self, auto=False):
        self.frame += 1
        # Player paddle
        if auto:
            # Simple AI tracking
            target = self.ball_x
            self.paddle_x += max(-18, min(18, target - self.paddle_x))
        else:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.paddle_x -= 16
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.paddle_x += 16
        self.paddle_x = max(self.paddle_w // 2, min(W - self.paddle_w // 2, self.paddle_x))

        # Opponent AI
        self.opp_x += max(-14, min(14, self.ball_x - self.opp_x))
        self.opp_x = max(self.opp_w // 2, min(W - self.opp_w // 2, self.opp_x))

        # Ball
        self.ball_x += self.vx
        self.ball_y += self.vy
        self.trail.append((int(self.ball_x), int(self.ball_y)))
        if len(self.trail) > 18:
            self.trail.pop(0)

        # Walls
        if self.ball_x < self.ball_r or self.ball_x > W - self.ball_r:
            self.vx = -self.vx
            self.ball_x = max(self.ball_r, min(W - self.ball_r, self.ball_x))
            self.vx *= 1.02

        # Bottom paddle
        paddle_top = H - 160
        if (paddle_top - self.ball_r < self.ball_y < paddle_top + self.paddle_h + self.ball_r and
            abs(self.ball_x - self.paddle_x) < self.paddle_w // 2 + self.ball_r and self.vy > 0):
            self.vy = -abs(self.vy) * 1.05
            offset = (self.ball_x - self.paddle_x) / (self.paddle_w / 2)
            self.vx += offset * 4
            self.ball_y = paddle_top - self.ball_r
            self.score += 1

        # Top paddle
        opp_bot = 160
        if (opp_bot - self.ball_r < self.ball_y < opp_bot + self.paddle_h + self.ball_r and
            abs(self.ball_x - self.opp_x) < self.opp_w // 2 + self.ball_r and self.vy < 0):
            self.vy = abs(self.vy) * 1.05
            offset = (self.ball_x - self.opp_x) / (self.opp_w / 2)
            self.vx += offset * 3
            self.ball_y = opp_bot + self.paddle_h + self.ball_r
            self.score += 1

        # Miss bottom
        if self.ball_y > H - 40:
            self.lives -= 1
            if self.lives <= 0:
                self.score = max(0, self.score - 5)
                self.lives = 3
            self.serve()
        # Miss top (rare with AI)
        if self.ball_y < 40:
            self.score += 3
            self.serve()

        # Clamp speed
        sp = math.hypot(self.vx, self.vy)
        if sp > 22:
            self.vx *= 22 / sp
            self.vy *= 22 / sp

    def draw(self, surf):
        surf.fill(VOID)
        # Court lines
        pygame.draw.line(surf, (30, 40, 70), (40, 80), (40, H - 80), 4)
        pygame.draw.line(surf, (30, 40, 70), (W - 40, 80), (W - 40, H - 80), 4)
        pygame.draw.line(surf, (50, 60, 100), (40, H // 2), (W - 40, H // 2), 2)
        # Center circle
        pygame.draw.circle(surf, (40, 50, 90), (W // 2, H // 2), 80, 3)

        # Trail
        for i, (tx, ty) in enumerate(self.trail):
            a = int(40 + 180 * (i / max(1, len(self.trail))))
            c = (CYAN[0], CYAN[1], CYAN[2]) if i % 2 == 0 else (MAG[0], MAG[1], MAG[2])
            pygame.draw.circle(surf, c, (tx, ty), max(2, self.ball_r - (len(self.trail) - i) // 2))

        # Ball
        pygame.draw.circle(surf, GOLD, (int(self.ball_x), int(self.ball_y)), self.ball_r)
        pygame.draw.circle(surf, WHITE, (int(self.ball_x), int(self.ball_y)), self.ball_r - 6)

        # Paddles
        pygame.draw.rect(surf, PADDLE_C, (self.paddle_x - self.paddle_w // 2, H - 160, self.paddle_w, self.paddle_h), border_radius=10)
        pygame.draw.rect(surf, CYAN, (self.paddle_x - self.paddle_w // 2, H - 160, self.paddle_w, self.paddle_h), 3, border_radius=10)
        pygame.draw.rect(surf, OPP_C, (self.opp_x - self.opp_w // 2, 160, self.opp_w, self.paddle_h), border_radius=10)
        pygame.draw.rect(surf, MAG, (self.opp_x - self.opp_w // 2, 160, self.opp_w, self.paddle_h), 3, border_radius=10)

        # UI
        title_s = self.font_big.render(TITLE, True, CYAN)
        surf.blit(title_s, (W // 2 - title_s.get_width() // 2, 40))
        score_s = self.font.render(f"SCORE {self.score}", True, GOLD)
        surf.blit(score_s, (W // 2 - score_s.get_width() // 2, H - 120))
        lives_s = self.font_sm.render(f"LIVES {self.lives}", True, WHITE)
        surf.blit(lives_s, (60, H - 100))
        handle_s = self.font_sm.render(HANDLE, True, MAG)
        surf.blit(handle_s, (W - handle_s.get_width() - 40, H - 100))

    def record(self):
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-vcodec", "rawvideo",
            "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS),
            "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "fast", "-movflags", "+faststart",
            OUT
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        frames = FPS * SECS
        for i in range(frames):
            self.update(auto=True)
            self.draw(self.screen)
            # Extra sparkle
            if i % 5 == 0:
                for _ in range(3):
                    pygame.draw.circle(self.screen, random.choice([CYAN, MAG, GOLD]),
                                       (random.randint(100, W-100), random.randint(200, H-200)), 2)
            raw = pygame.image.tostring(self.screen, "RGB")
            proc.stdin.write(raw)
            if i % 30 == 0:
                print(f"frame {i}/{frames}", flush=True)
        proc.stdin.close()
        err = proc.stderr.read().decode("utf-8", "ignore")
        rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed ({rc}):\n{err[-1200:]}")
        print("wrote", OUT)
        pygame.quit()

    def play_interactive(self):
        running = True
        while running:
            for e in pygame.event.get():
                if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                    running = False
                if e.type == pygame.KEYDOWN and e.key == pygame.K_r:
                    self.reset()
            self.update(auto=False)
            self.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()

def main():
    g = Game()
    if PLAY and not RECORD:
        g.play_interactive()
    else:
        g.record()

if __name__ == "__main__":
    main()
