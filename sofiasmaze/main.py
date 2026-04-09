import random
import sys
from dataclasses import dataclass

import pygame

# -----------------------------
# Game configuration
# -----------------------------
WINDOW_W, WINDOW_H = 1000, 700
FPS = 60

TILES = 20                 # tiles on the path
OVERSHOOT_WINS = True      # allowed per your spec
WRONG_ANSWER_PENALTY = 1   # move back 1 tile

# Pink theme colors
PINK_BG = (255, 214, 232)
PINK_PANEL = (255, 170, 210)
PINK_BUTTON = (255, 120, 180)
PINK_BUTTON_HOVER = (255, 140, 190)
WHITE = (255, 255, 255)
BLACK = (30, 30, 30)
PURPLE = (150, 90, 190)

# Player colors (tokens / accents)
P1_COLOR = (255, 80, 160)   # bright pink
P2_COLOR = (120, 120, 255)  # periwinkle / blue-purple

TITLE = "Sofia's Maze"


# -----------------------------
# Simple UI helpers
# -----------------------------
@dataclass
class Button:
    rect: pygame.Rect
    text: str
    bg: tuple
    hover_bg: tuple
    text_color: tuple = WHITE
    disabled: bool = False

    def draw(self, surface, font, mouse_pos):
        if self.disabled:
            bg = (200, 200, 200)
            tc = (90, 90, 90)
        else:
            bg = self.hover_bg if self.rect.collidepoint(mouse_pos) else self.bg
            tc = self.text_color

        pygame.draw.rect(surface, bg, self.rect, border_radius=16)
        pygame.draw.rect(surface, WHITE, self.rect, width=3, border_radius=16)
        label = font.render(self.text, True, tc)
        surface.blit(label, label.get_rect(center=self.rect.center))

    def clicked(self, event):
        if self.disabled:
            return False
        return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos)


# -----------------------------
# Questions (built-in)
# -----------------------------
def build_questions():
    # 6-year-old general knowledge: simple, friendly, multiple choice
    # Each question: (question, [choices], correct_index)
    return [
        ("What color is the sky on a sunny day?", ["Blue", "Green", "Purple"], 0),
        ("How many legs does a spider have?", ["6", "8", "10"], 1),
        ("Which animal says 'meow'?", ["Dog", "Cat", "Cow"], 1),
        ("What do we use to see?", ["Ears", "Eyes", "Elbows"], 1),
        ("Which one is a fruit?", ["Apple", "Carrot", "Bread"], 0),
        ("What shape is a ball?", ["Square", "Round", "Triangle"], 1),
        ("How many days are in a week?", ["5", "7", "10"], 1),
        ("What do we call a baby dog?", ["Kitten", "Puppy", "Chick"], 1),
        ("Which is the biggest?", ["Elephant", "Ant", "Ladybug"], 0),
        ("What do bees make?", ["Milk", "Honey", "Ice"], 1),
        ("Which one can fly?", ["Bird", "Fish", "Turtle"], 0),
        ("What do we drink when we are thirsty?", ["Water", "Sand", "Socks"], 0),
        ("Which season is usually cold?", ["Winter", "Summer", "Spring"], 0),
        ("How many wheels does a bicycle have?", ["1", "2", "4"], 1),
        ("What do we use to hear?", ["Nose", "Ears", "Knees"], 1),
        ("What is 2 + 2?", ["3", "4", "5"], 1),
        ("Which is a color?", ["Banana", "Pink", "Table"], 1),
        ("What do we wear on our feet?", ["Shoes", "Gloves", "Hats"], 0),
        ("Which one is a planet?", ["Earth", "Pizza", "Pencil"], 0),
        ("What do horses like to eat (a common treat)?", ["Carrots", "Candy", "Soap"], 0),
    ]


# -----------------------------
# Maze / board path
# -----------------------------
def build_path_positions(board_rect: pygame.Rect, tiles: int):
    """
    Build 20 positions in a maze-ish "snaking" path inside board_rect.
    This is a deterministic path: left->right, then right->left, etc.
    """
    cols = 5
    rows = (tiles + cols - 1) // cols  # for 20 tiles = 4 rows
    cell_w = board_rect.width // cols
    cell_h = board_rect.height // rows

    positions = []
    tile_index = 0
    for r in range(rows):
        row_positions = []
        for c in range(cols):
            if tile_index >= tiles:
                break
            x = board_rect.left + c * cell_w + cell_w // 2
            y = board_rect.top + r * cell_h + cell_h // 2
            row_positions.append((x, y))
            tile_index += 1

        # snake rows: even row left->right, odd row right->left
        if r % 2 == 1:
            row_positions.reverse()
        positions.extend(row_positions)

    return positions, cols, rows, cell_w, cell_h


def draw_board(surface, board_rect, positions, cols, rows, cell_w, cell_h):
    # board background
    pygame.draw.rect(surface, (255, 235, 245), board_rect, border_radius=24)
    pygame.draw.rect(surface, WHITE, board_rect, width=4, border_radius=24)

    # draw subtle grid and tile circles
    # We'll draw tiles as circles with numbers
    for idx, (x, y) in enumerate(positions):
        # alternating tile colors
        fill = (255, 200, 225) if idx % 2 == 0 else (255, 185, 215)
        pygame.draw.circle(surface, fill, (x, y), 38)
        pygame.draw.circle(surface, WHITE, (x, y), 3, width=3)

    # draw path lines between tiles
    for i in range(len(positions) - 1):
        pygame.draw.line(surface, (255, 150, 200), positions[i], positions[i + 1], width=8)


def draw_tile_numbers(surface, positions, font_small):
    for idx, (x, y) in enumerate(positions):
        label = font_small.render(str(idx + 1), True, BLACK)
        surface.blit(label, label.get_rect(center=(x, y)))


# -----------------------------
# Cute "rider on horse" token drawing (simple vector art)
# -----------------------------
def draw_rider_token(surface, center, accent_color, name, font_tiny):
    """
    Simple cartoon: horse body + head + legs + rider circle.
    """
    cx, cy = center

    # shadow
    pygame.draw.ellipse(surface, (0, 0, 0, 35), pygame.Rect(cx - 32, cy + 22, 64, 16))

    # horse body
    body = pygame.Rect(cx - 30, cy - 12, 60, 28)
    pygame.draw.ellipse(surface, (210, 160, 110), body)  # tan
    pygame.draw.ellipse(surface, WHITE, body, width=2)

    # horse head
    head = pygame.Rect(cx + 20, cy - 22, 26, 18)
    pygame.draw.ellipse(surface, (210, 160, 110), head)
    pygame.draw.ellipse(surface, WHITE, head, width=2)

    # ear
    pygame.draw.polygon(surface, (210, 160, 110), [(cx + 28, cy - 26), (cx + 34, cy - 34), (cx + 38, cy - 24)])
    pygame.draw.polygon(surface, WHITE, [(cx + 28, cy - 26), (cx + 34, cy - 34), (cx + 38, cy - 24)], width=2)

    # legs
    for lx in (-18, -4, 10, 24):
        pygame.draw.rect(surface, (170, 120, 80), pygame.Rect(cx + lx, cy + 10, 6, 20), border_radius=3)

    # mane / tail accent
    pygame.draw.arc(surface, accent_color, pygame.Rect(cx - 32, cy - 26, 40, 40), 1.6, 3.2, width=4)
    pygame.draw.arc(surface, accent_color, pygame.Rect(cx - 50, cy - 10, 30, 30), 1.9, 3.6, width=4)

    # rider (girl) head
    pygame.draw.circle(surface, (255, 220, 200), (cx - 4, cy - 28), 10)
    pygame.draw.circle(surface, WHITE, (cx - 4, cy - 28), 2, width=2)

    # rider hair (accent)
    pygame.draw.arc(surface, accent_color, pygame.Rect(cx - 16, cy - 40, 28, 24), 0.3, 3.2, width=6)

    # small name tag
    tag = font_tiny.render(name, True, BLACK)
    surface.blit(tag, tag.get_rect(center=(cx, cy - 56)))


# -----------------------------
# Game state
# -----------------------------
@dataclass
class QuestionState:
    active: bool = False
    q_text: str = ""
    choices: list = None
    correct_idx: int = 0
    chosen_idx: int = -1
    feedback: str = ""


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        self.clock = pygame.time.Clock()

        self.font_title = pygame.font.SysFont("Arial Rounded MT Bold", 44) or pygame.font.SysFont("Arial", 44, bold=True)
        self.font_ui = pygame.font.SysFont("Arial Rounded MT Bold", 28) or pygame.font.SysFont("Arial", 28, bold=True)
        self.font_small = pygame.font.SysFont("Arial Rounded MT Bold", 22) or pygame.font.SysFont("Arial", 22, bold=True)
        self.font_tiny = pygame.font.SysFont("Arial", 16)

        # Layout
        self.board_rect = pygame.Rect(40, 80, 620, 560)
        self.side_rect = pygame.Rect(690, 80, 270, 560)

        self.positions, self.cols, self.rows, self.cell_w, self.cell_h = build_path_positions(self.board_rect, TILES)

        # Players
        self.players = [
            {"name": "Player 1", "pos": 0, "color": P1_COLOR},
            {"name": "Player 2", "pos": 0, "color": P2_COLOR},
        ]
        self.current_player = 0
        self.last_roll = None
        self.winner = None

        # Questions
        self.questions = build_questions()
        random.shuffle(self.questions)

        self.question_state = QuestionState(active=False)

        # UI buttons
        self.btn_roll = Button(
            rect=pygame.Rect(self.side_rect.left + 35, self.side_rect.top + 80, 200, 60),
            text="ROLL DICE",
            bg=PINK_BUTTON,
            hover_bg=PINK_BUTTON_HOVER,
        )

        self.btn_restart = Button(
            rect=pygame.Rect(self.side_rect.left + 35, self.side_rect.top + 500, 200, 52),
            text="RESTART",
            bg=PURPLE,
            hover_bg=(170, 110, 210),
        )

        # Answer buttons (created dynamically)
        self.answer_buttons = []

        # Animation / movement
        self.moving = False
        self.move_steps_remaining = 0
        self.move_target = 0

    def restart(self):
        for p in self.players:
            p["pos"] = 0
        self.current_player = 0
        self.last_roll = None
        self.winner = None
        self.question_state = QuestionState(active=False)
        self.answer_buttons = []
        self.moving = False
        self.move_steps_remaining = 0
        self.move_target = 0

    def start_question(self):
        q, choices, correct = random.choice(self.questions)
        self.question_state = QuestionState(
            active=True,
            q_text=q,
            choices=choices,
            correct_idx=correct,
            chosen_idx=-1,
            feedback="Pick the best answer!",
        )
        self.build_answer_buttons()

    def build_answer_buttons(self):
        self.answer_buttons = []
        base_y = self.side_rect.top + 260
        for i, text in enumerate(self.question_state.choices):
            r = pygame.Rect(self.side_rect.left + 25, base_y + i * 68, 220, 54)
            self.answer_buttons.append(
                Button(rect=r, text=text, bg=(255, 110, 170), hover_bg=(255, 130, 180))
            )

    def roll_and_move(self):
        if self.winner is not None:
            return
        if self.question_state.active:
            return
        if self.moving:
            return

        roll = random.randint(1, 6)
        self.last_roll = roll

        p = self.players[self.current_player]
        start = p["pos"]
        target = start + roll

        if OVERSHOOT_WINS and target >= (TILES - 1):
            # We still animate the steps but winner will be set after movement ends
            target = min(target, TILES - 1)

        self.move_target = target
        self.move_steps_remaining = max(0, target - start)
        self.moving = self.move_steps_remaining > 0

        if not self.moving:
            # If no movement (shouldn't happen with dice), just ask question
            self.start_question()

    def finish_turn_after_question(self):
        # switch player
        self.current_player = (self.current_player + 1) % len(self.players)

    def apply_wrong_answer_penalty(self):
        p = self.players[self.current_player]
        p["pos"] = max(0, p["pos"] - WRONG_ANSWER_PENALTY)

    def update_movement(self):
        if not self.moving:
            return
        if self.move_steps_remaining > 0:
            self.players[self.current_player]["pos"] += 1
            self.move_steps_remaining -= 1
        if self.move_steps_remaining <= 0:
            self.moving = False

            # Check win (overshoot allowed; we clamp animation target, but real win check uses last_roll)
            if self.last_roll is not None:
                # Determine if player reached/passed final tile on this roll
                # We can compute raw position as current pos (clamped) vs final tile.
                if self.players[self.current_player]["pos"] >= (TILES - 1):
                    self.winner = self.current_player
                    self.question_state.active = False
                    self.answer_buttons = []
                    return

            # Start question on landing tile
            self.start_question()

    def handle_answer(self, idx):
        if not self.question_state.active:
            return

        self.question_state.chosen_idx = idx
        if idx == self.question_state.correct_idx:
            self.question_state.feedback = "Correct! Great job."
            # End question and switch turns
            self.question_state.active = False
            self.answer_buttons = []
            self.finish_turn_after_question()
        else:
            self.question_state.feedback = "Oops! Move back 1 tile."
            self.apply_wrong_answer_penalty()
            # End question and switch turns
            self.question_state.active = False
            self.answer_buttons = []
            self.finish_turn_after_question()

    def draw_header(self):
        title = self.font_title.render("Sofia’s Maze", True, (160, 40, 120))
        self.screen.blit(title, (40, 20))

        subtitle = self.font_small.render("Pink maze board • Dice roll • Answer questions!", True, (120, 30, 100))
        self.screen.blit(subtitle, (42, 58))

    def draw_side_panel(self, mouse_pos):
        pygame.draw.rect(self.screen, PINK_PANEL, self.side_rect, border_radius=24)
        pygame.draw.rect(self.screen, WHITE, self.side_rect, width=4, border_radius=24)

        # Turn indicator
        cp = self.players[self.current_player]
        turn_text = self.font_ui.render(f"Turn: {cp['name']}", True, BLACK)
        self.screen.blit(turn_text, (self.side_rect.left + 20, self.side_rect.top + 20))

        # Dice info
        dice_text = f"Dice: {self.last_roll}" if self.last_roll is not None else "Dice: -"
        dice_label = self.font_ui.render(dice_text, True, BLACK)
        self.screen.blit(dice_label, (self.side_rect.left + 20, self.side_rect.top + 140))

        # Roll button
        self.btn_roll.disabled = self.question_state.active or self.moving or (self.winner is not None)
        self.btn_roll.draw(self.screen, self.font_ui, mouse_pos)

        # Winner banner
        if self.winner is not None:
            win = self.players[self.winner]["name"]
            msg = self.font_ui.render(f"{win} wins!", True, (110, 30, 90))
            self.screen.blit(msg, (self.side_rect.left + 20, self.side_rect.top + 210))
            hint = self.font_small.render("Click RESTART", True, BLACK)
            self.screen.blit(hint, (self.side_rect.left + 20, self.side_rect.top + 245))
        else:
            # Question panel
            if self.question_state.active:
                qwrap = wrap_text(self.question_state.q_text, self.font_small, 240)
                y = self.side_rect.top + 200
                for line in qwrap:
                    surf = self.font_small.render(line, True, BLACK)
                    self.screen.blit(surf, (self.side_rect.left + 20, y))
                    y += 24

                fb = self.font_small.render(self.question_state.feedback, True, (90, 20, 70))
                self.screen.blit(fb, (self.side_rect.left + 20, self.side_rect.top + 235))

                for b in self.answer_buttons:
                    b.draw(self.screen, self.font_small, mouse_pos)
            else:
                hint = self.font_small.render("Roll the dice!", True, BLACK)
                self.screen.blit(hint, (self.side_rect.left + 20, self.side_rect.top + 210))

        # Restart
        self.btn_restart.draw(self.screen, self.font_ui, mouse_pos)

        # Player positions
        y = self.side_rect.top + 370
        for i, p in enumerate(self.players):
            label = self.font_small.render(f"{p['name']}: Tile {p['pos'] + 1}", True, BLACK)
            self.screen.blit(label, (self.side_rect.left + 20, y))
            # color dot
            pygame.draw.circle(self.screen, p["color"], (self.side_rect.left + 230, y + 12), 10)
            pygame.draw.circle(self.screen, WHITE, (self.side_rect.left + 230, y + 12), 10, width=2)
            y += 36

    def draw_players(self):
        # Draw tokens slightly offset if both on same tile
        tile_to_players = {}
        for i, p in enumerate(self.players):
            tile_to_players.setdefault(p["pos"], []).append(i)

        for tile, plist in tile_to_players.items():
            base = self.positions[tile]
            for offset_idx, player_idx in enumerate(plist):
                dx = -22 if offset_idx == 0 and len(plist) > 1 else (22 if offset_idx == 1 else 0)
                dy = 0
                p = self.players[player_idx]
                draw_rider_token(self.screen, (base[0] + dx, base[1] + dy), p["color"], p["name"], self.font_tiny)

    def run_frame(self):
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)

            if self.btn_restart.clicked(event):
                self.restart()

            if self.btn_roll.clicked(event):
                self.roll_and_move()

            if self.question_state.active and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, b in enumerate(self.answer_buttons):
                    if b.clicked(event):
                        self.handle_answer(i)
                        break

        self.update_movement()

        # Draw
        self.screen.fill(PINK_BG)
        self.draw_header()

        draw_board(self.screen, self.board_rect, self.positions, self.cols, self.rows, self.cell_w, self.cell_h)
        draw_tile_numbers(self.screen, self.positions, self.font_small)
        self.draw_players()

        self.draw_side_panel(mouse_pos)

        pygame.display.flip()
        self.clock.tick(FPS)


def wrap_text(text, font, max_width):
    words = text.split(" ")
    lines = []
    cur = ""
    for w in words:
        test = (cur + " " + w).strip()
        if font.size(test)[0] <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def run():
    game = Game()
    while True:
        game.run_frame()
