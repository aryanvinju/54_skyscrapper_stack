import random
import pygame
from game.block import Block


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.block_height = 28
        self.base_width = 180

        self.font_title = pygame.font.SysFont(None, 38)
        self.font_hud = pygame.font.SysFont(None, 28)
        self.font_big = pygame.font.SysFont(None, 46)
        self.font_popup = pygame.font.SysFont(None, 34, bold=True)
        self.starfield = [
            (random.randrange(width), random.randrange(height), random.choice((1, 1, 2)))
            for _ in range(90)
        ]

        self.reset()

    def get_color(self, index):
        palette = [
            (230, 75, 75),   # Crimson
            (240, 140, 45),  # Orange
            (245, 210, 50),  # Gold
            (60, 195, 110),  # Green
            (50, 150, 240),  # Blue
            (165, 80, 225),  # Purple
        ]
        return palette[index % len(palette)]

    def reset(self):
        self.score = 0
        self.game_over = False
        self.perfect_streak = 0
        self.debris = []
        self.popups = []

        base_x = (self.width - self.base_width) // 2
        base_y = self.height - 60
        base_block = Block(base_x, base_y, self.base_width, self.block_height, self.get_color(0), speed=0)
        self.stack = [base_block]

        self.spawn_active_block()

    def spawn_active_block(self):
        top_block = self.stack[-1]
        next_y = top_block.y - self.block_height - 4
        speed = min(10.0, 4.5 + (len(self.stack) * 0.35))
        color = self.get_color(len(self.stack))

        start_x = 25 if random.choice([True, False]) else self.width - 25 - top_block.width
        self.active_block = Block(start_x, next_y, top_block.width, self.block_height, color, speed=speed)

    def drop_block(self):
        if self.game_over:
            return

        top_block = self.stack[-1]
        act = self.active_block

        left = max(act.x, top_block.x)
        right = min(act.x + act.width, top_block.x + top_block.width)
        overlap = right - left

        is_successful_drop = overlap > 0
        
        if is_successful_drop:
            perfect = abs(act.x - top_block.x) <= 3
            if perfect:
                self.perfect_streak += 1
                block_x = top_block.x
                trimmed_width = top_block.width
                self.score += 2
                self.popups.append({"text": "PERFECT!", "x": self.width / 2, "y": act.y - 12, "age": 0})
            else:
                self.perfect_streak = 0
                block_x = left
                trimmed_width = overlap
                # Keep the trimmed offcuts as independently animated debris.
                if act.x < top_block.x:
                    self._spawn_debris(act.x, act.y, top_block.x - act.x, act, -2.5)
                active_right = act.x + act.width
                stack_right = top_block.x + top_block.width
                if active_right > stack_right:
                    self._spawn_debris(stack_right, act.y, active_right - stack_right, act, 2.5)

            new_block = Block(block_x, act.y, trimmed_width, self.block_height, act.color, speed=0)
            self.stack.append(new_block)
            self.score += 1

            if self.perfect_streak >= 3:
                # Grow toward the original foundation width, centered on the tier.
                restored_width = min(self.base_width, new_block.width + 12)
                center = new_block.x + new_block.width / 2
                new_block.width = restored_width
                new_block.x = max(20, min(self.width - 20 - restored_width, center - restored_width / 2))
                self.perfect_streak = 0

            if new_block.y < 180:
                shift_amount = self.block_height + 4
                for b in self.stack:
                    b.y += shift_amount
                for piece in self.debris:
                    piece["y"] += shift_amount

            self.spawn_active_block()
        else:
            self.game_over = True

    def _spawn_debris(self, x, y, width, source, horizontal_speed):
        if width <= 0:
            return
        self.debris.append({
            "x": float(x), "y": float(y), "width": float(width),
            "height": float(self.block_height), "color": source.color,
            "vx": horizontal_speed + random.uniform(-0.8, 0.8), "vy": -2.0,
            "angle": 0.0, "spin": random.uniform(-5.0, 5.0),
        })

    def handle_event(self, event):
        if self.game_over:
            if (event.type == pygame.KEYDOWN and event.key in (pygame.K_r, pygame.K_SPACE)) or \
               (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
                self.reset()
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self.drop_block()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.drop_block()

    def update(self):
        if not self.game_over:
            self.active_block.update(self.width)
        for piece in self.debris:
            piece["x"] += piece["vx"]
            piece["y"] += piece["vy"]
            piece["vy"] += 0.28
            piece["angle"] += piece["spin"]
        self.debris = [p for p in self.debris if p["y"] < self.height + 50]
        for popup in self.popups:
            popup["age"] += 1
            popup["y"] -= 0.7
        self.popups = [p for p in self.popups if p["age"] < 65]

    def _sky_color(self):
        # Blend through altitude bands based on the climbed tower height.
        colors = [(24, 42, 68), (70, 48, 96), (27, 29, 69), (5, 8, 23)]
        progress = min(1.0, self.score / 45.0) * (len(colors) - 1)
        band = min(int(progress), len(colors) - 2)
        t = progress - band
        return tuple(round(colors[band][i] * (1 - t) + colors[band + 1][i] * t) for i in range(3))

    def render(self, screen):
        screen.fill(self._sky_color())
        if self.score >= 24:
            for sx, sy, radius in self.starfield:
                pygame.draw.circle(screen, (205, 215, 245), (sx, sy), radius)

        title_surf = self.font_title.render("Skyscraper Stack", True, (245, 245, 245))
        screen.blit(title_surf, (self.width // 2 - title_surf.get_width() // 2, 16))

        score_surf = self.font_hud.render(f"Height: {self.score}", True, (255, 220, 80))
        screen.blit(score_surf, (self.width // 2 - score_surf.get_width() // 2, 54))

        for b in self.stack:
            b.render(screen)

        for piece in self.debris:
            image = pygame.Surface((max(1, round(piece["width"])), round(piece["height"])), pygame.SRCALPHA)
            pygame.draw.rect(image, piece["color"], image.get_rect(), border_radius=3)
            pygame.draw.rect(image, (245, 245, 250), image.get_rect(), width=2, border_radius=3)
            rotated = pygame.transform.rotate(image, piece["angle"])
            screen.blit(rotated, (piece["x"] - (rotated.get_width() - image.get_width()) / 2,
                                  piece["y"] - (rotated.get_height() - image.get_height()) / 2))

        for popup in self.popups:
            label = self.font_popup.render(popup["text"], True, (255, 218, 72))
            label.set_alpha(max(0, 255 - popup["age"] * 4))
            screen.blit(label, (popup["x"] - label.get_width() / 2, popup["y"]))

        if not self.game_over:
            self.active_block.render(screen)

        if self.game_over:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 195))
            screen.blit(overlay, (0, 0))

            over_surf = self.font_big.render("TOWER COLLAPSED!", True, (240, 75, 75))
            screen.blit(over_surf, (self.width // 2 - over_surf.get_width() // 2, self.height // 2 - 40))

            final_surf = self.font_hud.render(f"Final Height: {self.score}", True, (255, 255, 255))
            screen.blit(final_surf, (self.width // 2 - final_surf.get_width() // 2, self.height // 2 + 10))

            restart_surf = self.font_hud.render("Press [Space] or [R] to Play Again", True, (200, 200, 200))
            screen.blit(restart_surf, (self.width // 2 - restart_surf.get_width() // 2, self.height // 2 + 50))
