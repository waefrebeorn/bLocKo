import arcade
import random
import time
import json
import os
import math

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800
SCREEN_TITLE = "bLocKo - The Puzzle Game"

BLOCK_SIZE = 30
GRID_WIDTH = 10
GRID_HEIGHT = 20
BUFFER_ZONE_HEIGHT = 4  # Number of rows above the visible playfield

GRID_ORIGIN_X = (SCREEN_WIDTH - GRID_WIDTH * BLOCK_SIZE) // 2
GRID_ORIGIN_Y = (SCREEN_HEIGHT - GRID_HEIGHT * BLOCK_SIZE) // 2

BACKGROUND_COLOR = arcade.color.BLACK
GRID_COLOR = arcade.color.GRAY
BLOCK_COLORS = [
    arcade.color.RED,
    arcade.color.BLUE,
    arcade.color.GREEN,
    arcade.color.YELLOW,
    arcade.color.ORANGE,
    arcade.color.PURPLE,
    arcade.color.CYAN
]
GHOST_COLOR = (255, 255, 255, 50)
FLASH_COLOR = arcade.color.WHITE

HARD_DROP_COOLDOWN = 0.5
INITIAL_DROP_INTERVAL = 1.0
MIN_DROP_INTERVAL = 0.05
LOCK_DELAY = 0.75

WALL_KICK_OFFSETS = {
    'non-I': [
        (0, 0),
        (-1, 0),
        (-1, 1),
        (0, -2),
        (-1, -2),
        (1, 0),
        (1, 1),
        (0, 2),
        (1, -2)
    ],
    'I': [
        (0, 0),
        (-2, 0),
        (+1, 0),
        (-2, -1),
        (+1, +2),
        (+2, 0),
        (-1, 0),
        (+2, +1),
        (-1, -2)
    ]
}

BLOCK_SHAPES = [
    [(0,1), (1,1), (1,0), (1,2), (2,1)],  # F
    [(0,2), (1,2), (2,2), (3,2), (4,2)],  # I
    [(0,0), (1,0), (2,0), (3,0), (3,1)],  # L
    [(0,1), (1,1), (2,1), (2,0), (3,0)],  # N
    [(0,0), (0,1), (1,0), (1,1), (2,0)],  # P
    [(0,1), (1,0), (1,1), (1,2), (2,1)],  # T
    [(0,0), (0,2), (1,0), (1,1), (1,2)],  # U
    [(0,0), (1,0), (2,0), (2,1), (2,2)],  # V
    [(0,0), (1,0), (1,1), (2,1), (2,2)],  # W
    [(0,1), (1,0), (1,1), (2,1), (3,1)],  # Y
    [(0,0), (0,1), (1,1), (1,2), (2,2)]   # Z
]

SCORE_SINGLE = 100
SCORE_DOUBLE = 300
SCORE_TRIPLE = 600
SCORE_QUADRUPLE = 1000
SCORE_BLOCKO = 1500
SCORE_SOFT_DROP = 1
SCORE_HARD_DROP = 2
SCORE_B_SPIN = 800

PARTICLE_SPEED = 2
PARTICLE_FADE_RATE = 5
PARTICLE_COUNT = 20

POWER_UP_CHANCE = 0.05
POWER_UP_TYPES = {
    "CLEAR_ROW": {"chance": 0.3, "duration": 0},
    "SLOW_TIME": {"chance": 0.3, "duration": 15},
    "AVALANCHE": {"chance": 0.2, "duration": 0},
    "BOMB": {"chance": 0.2, "duration": 0}
}

INITIAL_PRESSURE_INTERVAL = 30
MIN_PRESSURE_INTERVAL = 10
INITIAL_PRESSURE_HEIGHT = 1
MAX_PRESSURE_HEIGHT = 5
GARBAGE_BLOCK_COLOR = arcade.color.GRAY
PRESSURE_INCREASE_INTERVAL = 60

# Load sounds
MOVE_SOUND = arcade.load_sound(":resources:sounds/hit1.wav")
ROTATE_SOUND = arcade.load_sound(":resources:sounds/hit2.wav")
LOCK_SOUND = arcade.load_sound(":resources:sounds/hit3.wav")
LINE_CLEAR_SOUND = arcade.load_sound(":resources:sounds/coin1.wav")
GAME_OVER_SOUND = arcade.load_sound(":resources:sounds/gameover1.wav")
BG_MUSIC = arcade.load_sound(":resources:music/1918.mp3")

# Default key bindings
DEFAULT_KEY_BINDINGS = {
    "MOVE_LEFT": arcade.key.LEFT,
    "MOVE_RIGHT": arcade.key.RIGHT,
    "MOVE_UP": arcade.key.UP,
    "MOVE_DOWN": arcade.key.DOWN,
    "SOFT_DROP": arcade.key.DOWN,
    "HARD_DROP": arcade.key.UP,
    "ROTATE_LEFT": arcade.key.Z,
    "ROTATE_RIGHT": arcade.key.X,
    "HOLD": arcade.key.C,
    "PAUSE": arcade.key.P,
    "SELECT": arcade.key.ENTER,
    "BACK": arcade.key.ESCAPE
}

class GameMode:
    MARATHON = 0
    SPRINT = 1
    ULTRA = 2
    PRESSURE = 3

class GameState:
    MAIN_MENU = 0
    GAME_MODE_SELECT = 1
    OPTIONS = 2
    PLAYING = 3
    PAUSED = 4
    GAME_OVER = 5
    TUTORIAL = 6
    KEY_BINDING = 7

def key_to_string(key):
    key_map = {
        arcade.key.UP: "Up",
        arcade.key.DOWN: "Down",
        arcade.key.LEFT: "Left",
        arcade.key.RIGHT: "Right",
        arcade.key.ENTER: "Enter",
        arcade.key.ESCAPE: "Esc",
        arcade.key.SPACE: "Space",
        arcade.key.Z: "Z",
        arcade.key.X: "X",
        arcade.key.C: "C",
        arcade.key.P: "P"
    }
    return key_map.get(key, chr(key).upper())

class PowerUp:
    def __init__(self, type):
        self.type = type
        self.active = False
        self.start_time = None
        self.duration = POWER_UP_TYPES[type]["duration"]

    def activate(self):
        self.active = True
        self.start_time = time.time()

    def deactivate(self):
        self.active = False
        self.start_time = None

class Block:
    def __init__(self, shape, color, grid_x, grid_y, block_type='non-I'):
        self.shape = shape
        self.color = color
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.block_type = block_type
        self.rotation_state = 0

    def get_global_positions(self):
        return [(self.grid_x + x, self.grid_y + y) for x, y in self.shape]

    def move(self, dx, dy):
        self.grid_x += dx
        self.grid_y += dy

    def get_width(self):
        xs = [x for x, y in self.shape]
        return max(xs) - min(xs) + 1

    def get_height(self):
        ys = [y for _, y in self.shape]
        return max(ys) - min(ys) + 1

    def rotate(self, clockwise, game):
        original_shape = self.shape.copy()
        original_x = self.grid_x
        original_y = self.grid_y
        original_state = self.rotation_state
    
        center_x = sum(x for x, _ in self.shape) / len(self.shape)
        center_y = sum(y for _, y in self.shape) / len(self.shape)
    
        if clockwise:
            self.shape = [(round(-y + center_y + center_x), round(x - center_x + center_y)) for x, y in self.shape]
            self.rotation_state = (self.rotation_state + 1) % 4
        else:
            self.shape = [(round(y - center_y + center_x), round(-x + center_x + center_y)) for x, y in self.shape]
            self.rotation_state = (self.rotation_state - 1) % 4
    
        min_x = min(x for x, _ in self.shape)
        min_y = min(y for _, y in self.shape)
        self.shape = [(x - min_x, y - min_y) for x, y in self.shape]
    
        kick_set = WALL_KICK_OFFSETS['I' if self.block_type == 'I' else 'non-I']
        for kick in kick_set:
            test_x = self.grid_x + kick[0]
            test_y = self.grid_y + kick[1]
            if game.is_valid_position([(x + test_x, y + test_y) for x, y in self.shape]):
                self.grid_x = test_x
                self.grid_y = test_y
                return True
    
        self.shape = original_shape
        self.grid_x = original_x
        self.grid_y = original_y
        self.rotation_state = original_state
        return False

class Particle(arcade.SpriteCircle):
    def __init__(self, x, y, color):
        super().__init__(3, color)
        self.center_x = x
        self.center_y = y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1, PARTICLE_SPEED)
        self.change_x = math.cos(angle) * speed
        self.change_y = math.sin(angle) * speed
        self.fade_rate = PARTICLE_FADE_RATE

    def update(self):
        self.center_x += self.change_x
        self.center_y += self.change_y
        self.alpha -= self.fade_rate
        if self.alpha <= 0:
            self.remove_from_sprite_lists()

class BKGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(BACKGROUND_COLOR)
        self.setup()
        self.game_state = GameState.MAIN_MENU
        self.bg_music = None
        self.frame_count = 0
        self.pressed_keys = set()

    def setup(self):
        self.game_mode = GameMode.MARATHON
        self.power_ups_enabled = True
        self.difficulty = 1
        self.grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT + BUFFER_ZONE_HEIGHT)]
        self.current_block = None
        self.next_blocks = []
        self.hold_block = None
        self.can_hold = True
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.last_hard_drop_time = -HARD_DROP_COOLDOWN
        self.next_drop_time = time.time() + INITIAL_DROP_INTERVAL
        self.drop_interval = INITIAL_DROP_INTERVAL
        self.flash_lines = []
        self.is_flashing = False
        self.flash_timer = 0
        self.flash_duration = 0.1
        self.total_flashes = 0
        self.max_flashes = 4
        self.flash_visible = True
        self.lock_timer = None
        self.high_scores = self.load_high_scores()
        self.particle_list = arcade.SpriteList()
        self.start_time = None
        self.time_limit = None
        self.animated_blocks = []
        self.combo_count = 0
        self.power_ups = {ptype: PowerUp(ptype) for ptype in POWER_UP_TYPES}
        self.active_power_ups = []
        self.tutorial_step = 0
        self.combo_display_time = 0
        self.power_up_display_time = 0
        self.last_pressure_time = 0
        self.pressure_interval = INITIAL_PRESSURE_INTERVAL
        self.pressure_height = INITIAL_PRESSURE_HEIGHT
        self.pressure_level = 0
        self.lava_height = 0
        self.menu_selection = 0
        self.mode_selection = 0
        self.option_selection = 0
        self.key_bindings = self.load_key_bindings()
        self.rebinding_action = None

    def load_high_scores(self):
        if os.path.exists("high_scores.json"):
            try:
                with open("high_scores.json", "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return []
        return []

    def save_high_scores(self):
        with open("high_scores.json", "w") as f:
            json.dump(self.high_scores, f)

    def update_high_scores(self):
        self.high_scores.append({"score": self.score, "level": self.level, "lines": self.lines_cleared})
        self.high_scores.sort(key=lambda x: x["score"], reverse=True)
        self.high_scores = self.high_scores[:10]
        self.save_high_scores()

    def load_key_bindings(self):
        if os.path.exists("key_bindings.json"):
            try:
                with open("key_bindings.json", "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return DEFAULT_KEY_BINDINGS.copy()
        return DEFAULT_KEY_BINDINGS.copy()

    def save_key_bindings(self):
        with open("key_bindings.json", "w") as f:
            json.dump(self.key_bindings, f)

    def get_ghost_position(self):
        if not self.current_block:
            return []
        
        ghost_block = Block(
            self.current_block.shape.copy(),
            self.current_block.color,
            self.current_block.grid_x,
            self.current_block.grid_y,
            self.current_block.block_type
        )
        
        while self.is_valid_position([(x, y - 1) for x, y in ghost_block.get_global_positions()]):
            ghost_block.move(0, -1)
        
        return ghost_block
        
    def spawn_new_block(self):
        if len(self.next_blocks) < 3:
            self.next_blocks.extend([self.get_new_block() for _ in range(3 - len(self.next_blocks))])
        self.current_block = self.next_blocks.pop(0)
        self.next_blocks.append(self.get_new_block())
    
        # Calculate the initial position
        self.current_block.grid_x = (GRID_WIDTH - self.current_block.get_width()) // 2
        self.current_block.grid_y = GRID_HEIGHT + BUFFER_ZONE_HEIGHT - self.current_block.get_height()
    
        # Check if the initial position is valid
        if not self.is_valid_position(self.current_block.get_global_positions()):
            self.game_over()
            return False
    
        self.can_hold = True
        return True

    def get_new_block(self):
        shape = random.choice(BLOCK_SHAPES)
        color = random.choice(BLOCK_COLORS)
        block_type = 'I' if shape == [(0,2), (1,2), (2,2), (3,2), (4,2)] else 'non-I'
        return Block(shape, color, 0, 0, block_type)

    def hold_piece(self):
        if not self.can_hold:
            return

        if self.hold_block:
            self.current_block, self.hold_block = self.hold_block, self.current_block
            self.current_block.grid_x = (GRID_WIDTH - self.current_block.get_width()) // 2
            self.current_block.grid_y = GRID_HEIGHT + BUFFER_ZONE_HEIGHT - 1
        else:
            self.hold_block = self.current_block
            self.spawn_new_block()

        self.can_hold = False

    def is_valid_position(self, positions):
        for x, y in positions:
            if x < 0 or x >= GRID_WIDTH or y < 0:
                return False  # Out of bounds
            if y < GRID_HEIGHT and self.grid[int(y)][int(x)] is not None:
                return False  # Collision with existing block
        return True

    def move_block(self, dx, dy):
        if self.current_block:
            new_positions = [(x + dx, y + dy) for x, y in self.current_block.get_global_positions()]
            if self.is_valid_position(new_positions):
                self.current_block.move(dx, dy)
                if dy == -1:
                    self.score += SCORE_SOFT_DROP
                arcade.play_sound(MOVE_SOUND)
                return True
        return False

    def hard_drop(self):
        if not self.current_block:
            return
        drop_distance = 0
        while self.move_block(0, -1):
            drop_distance += 1
        self.score += SCORE_HARD_DROP * drop_distance
        self.place_block()
        arcade.play_sound(LOCK_SOUND)

    def place_block(self):
        for x, y in self.current_block.get_global_positions():
            if 0 <= y < GRID_HEIGHT and 0 <= x < GRID_WIDTH:
                self.grid[int(y)][int(x)] = self.current_block.color
        self.clear_lines()
        self.spawn_new_block()
        self.lock_timer = None
        arcade.play_sound(LOCK_SOUND)
        
    def clear_lines(self):
        lines_to_clear = []
        for y in range(GRID_HEIGHT + BUFFER_ZONE_HEIGHT):
            if all(self.grid[y][x] is not None for x in range(GRID_WIDTH)):
                lines_to_clear.append(y)

        if lines_to_clear:
            self.flash_lines = lines_to_clear.copy()
            self.is_flashing = True
            self.flash_timer = 0
            self.flash_visible = True
            self.total_flashes = 0
            arcade.play_sound(LINE_CLEAR_SOUND)
            self.create_clear_particles(lines_to_clear)
            self.update_combo(len(lines_to_clear))
            if self.power_ups_enabled:
                self.spawn_power_up_block()

            for y in sorted(lines_to_clear, reverse=True):
                del self.grid[y]
                self.grid.insert(0, [None for _ in range(GRID_WIDTH)])

            self.lines_cleared += len(lines_to_clear)
            self.score += self.calculate_score(len(lines_to_clear))
            self.update_level()

    def calculate_score(self, lines_cleared):
        base_scores = {1: SCORE_SINGLE, 2: SCORE_DOUBLE, 3: SCORE_TRIPLE, 4: SCORE_QUADRUPLE, 5: SCORE_BLOCKO}
        return base_scores.get(lines_cleared, SCORE_BLOCKO) * self.level

    def update_level(self):
        self.level = min(self.lines_cleared // 10 + 1, 15)
        self.drop_interval = max(MIN_DROP_INTERVAL, INITIAL_DROP_INTERVAL - 0.05 * (self.level - 1))

    def update_combo(self, lines_cleared):
        if lines_cleared > 0:
            self.combo_count += 1
            combo_bonus = self.combo_count * 50 * self.level
            self.score += combo_bonus
            self.combo_display_time = time.time()
            arcade.play_sound(ROTATE_SOUND)  # Use as combo sound
        else:
            self.combo_count = 0

    def create_clear_particles(self, lines):
        for y in lines:
            for x in range(GRID_WIDTH):
                if self.grid[y][x]:
                    screen_x = GRID_ORIGIN_X + x * BLOCK_SIZE + BLOCK_SIZE // 2
                    screen_y = GRID_ORIGIN_Y + (y - BUFFER_ZONE_HEIGHT) * BLOCK_SIZE + BLOCK_SIZE // 2
                    for _ in range(PARTICLE_COUNT // GRID_WIDTH):
                        particle = Particle(screen_x, screen_y, self.grid[y][x])
                        self.particle_list.append(particle)

    def spawn_power_up_block(self):
        if random.random() < POWER_UP_CHANCE:
            power_up_type = random.choices(
                list(POWER_UP_TYPES.keys()), 
                weights=[POWER_UP_TYPES[t]["chance"] for t in POWER_UP_TYPES]
            )[0]
            self.activate_power_up(power_up_type)

    def activate_power_up(self, type):
        power_up = self.power_ups[type]
        power_up.activate()
        self.active_power_ups.append(power_up)
        self.power_up_display_time = time.time()
        arcade.play_sound(ROTATE_SOUND)  # Use as power-up sound

        if type == "CLEAR_ROW":
            self.clear_random_row()
        elif type == "SLOW_TIME":
            self.drop_interval *= 1.5
        elif type == "AVALANCHE":
            self.trigger_avalanche()
        elif type == "BOMB":
            self.trigger_bomb()

    def clear_random_row(self):
        row = random.randint(0, GRID_HEIGHT - 1)
        if any(self.grid[row]):
            self.grid[row] = [None for _ in range(GRID_WIDTH)]
            self.create_clear_particles([row])

    def trigger_avalanche(self):
        self.settle_all_blocks()

    def settle_all_blocks(self):
        blocks_moved = False
        for x in range(GRID_WIDTH):
            column_settled = self.settle_column(x)
            blocks_moved = blocks_moved or column_settled

        if blocks_moved:
            self.clear_lines()

    def settle_column(self, x):
        column = [self.grid[y][x] for y in range(GRID_HEIGHT + BUFFER_ZONE_HEIGHT)]
        settled_column = [block for block in column if block is not None]
        blocks_moved = len(settled_column) != len([block for block in column if block is not None])

        settled_column = [None] * (GRID_HEIGHT + BUFFER_ZONE_HEIGHT - len(settled_column)) + settled_column

        for y in range(GRID_HEIGHT + BUFFER_ZONE_HEIGHT):
            if self.grid[y][x] != settled_column[y]:
                self.grid[y][x] = settled_column[y]

        return blocks_moved

    def trigger_bomb(self):
        bomb_x = random.randint(0, GRID_WIDTH - 1)
        bomb_y = random.randint(0, GRID_HEIGHT - 1)

        for y in range(max(0, bomb_y - 2), min(GRID_HEIGHT + BUFFER_ZONE_HEIGHT, bomb_y + 3)):
            for x in range(max(0, bomb_x - 2), min(GRID_WIDTH, bomb_x + 3)):
                if self.grid[y][x]:
                    self.grid[y][x] = None
                    self.create_explosion_particles(x, y)

        self.settle_all_blocks()

    def create_explosion_particles(self, x, y):
        screen_x = GRID_ORIGIN_X + x * BLOCK_SIZE + BLOCK_SIZE // 2
        screen_y = GRID_ORIGIN_Y + (y - BUFFER_ZONE_HEIGHT) * BLOCK_SIZE + BLOCK_SIZE // 2
        for _ in range(20):
            particle = Particle(screen_x, screen_y, arcade.color.ORANGE)
            self.particle_list.append(particle)

    def update_power_ups(self):
        current_time = time.time()
        for power_up in self.active_power_ups[:]:
            if power_up.duration > 0 and current_time - power_up.start_time > power_up.duration:
                if power_up.type == "SLOW_TIME":
                    self.drop_interval /= 1.5
                power_up.deactivate()
                self.active_power_ups.remove(power_up)

    def game_over(self):
        self.game_state = GameState.GAME_OVER
        self.stop_background_music()
        arcade.play_sound(GAME_OVER_SOUND)
        self.update_high_scores()
        
    def on_draw(self):
        arcade.start_render()
        
        if self.game_state == GameState.MAIN_MENU:
            self.draw_main_menu()
        elif self.game_state == GameState.GAME_MODE_SELECT:
            self.draw_game_mode_select()
        elif self.game_state == GameState.OPTIONS:
            self.draw_options_menu()
        elif self.game_state in [GameState.PLAYING, GameState.PAUSED]:
            self.draw_game()
            if self.game_state == GameState.PAUSED:
                self.draw_pause_screen()
        elif self.game_state == GameState.GAME_OVER:
            self.draw_game()
            self.draw_game_over_screen()
        elif self.game_state == GameState.TUTORIAL:
            self.draw_tutorial()
        elif self.game_state == GameState.KEY_BINDING:
            self.draw_key_binding_menu()
            
    def draw_game(self):
        # Draw grid and placed blocks
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                arcade.draw_rectangle_outline(
                    GRID_ORIGIN_X + x * BLOCK_SIZE + BLOCK_SIZE / 2,
                    GRID_ORIGIN_Y + y * BLOCK_SIZE + BLOCK_SIZE / 2,
                    BLOCK_SIZE, BLOCK_SIZE, GRID_COLOR
                )
                if self.grid[y][x]:
                    arcade.draw_rectangle_filled(
                        GRID_ORIGIN_X + x * BLOCK_SIZE + BLOCK_SIZE / 2,
                        GRID_ORIGIN_Y + y * BLOCK_SIZE + BLOCK_SIZE / 2,
                        BLOCK_SIZE, BLOCK_SIZE, self.grid[y][x]
                    )
    
        # Draw ghost block
        ghost_positions = self.get_ghost_position().get_global_positions()
        for x, y in ghost_positions:
            if 0 <= y < GRID_HEIGHT:
                arcade.draw_rectangle_filled(
                    GRID_ORIGIN_X + x * BLOCK_SIZE + BLOCK_SIZE / 2,
                    GRID_ORIGIN_Y + y * BLOCK_SIZE + BLOCK_SIZE / 2,
                    BLOCK_SIZE, BLOCK_SIZE, GHOST_COLOR
                )
    
        # Draw current block
        if self.current_block:
            for x, y in self.current_block.get_global_positions():
                if 0 <= y < GRID_HEIGHT + BUFFER_ZONE_HEIGHT:
                    arcade.draw_rectangle_filled(
                        GRID_ORIGIN_X + x * BLOCK_SIZE + BLOCK_SIZE / 2,
                        GRID_ORIGIN_Y + (y - BUFFER_ZONE_HEIGHT) * BLOCK_SIZE + BLOCK_SIZE / 2,
                        BLOCK_SIZE, BLOCK_SIZE, self.current_block.color
                    )
    
        # Draw particles, score, level, hold box, next pieces, and notifications
        self.particle_list.draw()
        arcade.draw_text(f"Score: {self.score}", 10, SCREEN_HEIGHT - 30, arcade.color.WHITE, 20)
        arcade.draw_text(f"Level: {self.level}", 10, SCREEN_HEIGHT - 60, arcade.color.WHITE, 20)
        arcade.draw_text(f"Lines: {self.lines_cleared}", 10, SCREEN_HEIGHT - 90, arcade.color.WHITE, 20)
        self.draw_hold_box()
        self.draw_next_pieces()
    
        # Draw combo and power-up notifications
        if time.time() - self.combo_display_time < 2:
            arcade.draw_text(f"Combo x{self.combo_count}!", 
                            SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50,
                            arcade.color.YELLOW, 24, anchor_x="center")
        if time.time() - self.power_up_display_time < 2:
            active_power_ups = [p.type for p in self.active_power_ups]
            arcade.draw_text(f"Power-up: {', '.join(active_power_ups)}", 
                            SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80,
                            arcade.color.CYAN, 20, anchor_x="center")

    def draw_hold_box(self):
        arcade.draw_rectangle_outline(
            GRID_ORIGIN_X - 100, SCREEN_HEIGHT - 100,
            80, 80, arcade.color.WHITE
        )
        arcade.draw_text("HOLD", GRID_ORIGIN_X - 100, SCREEN_HEIGHT - 50,
                         arcade.color.WHITE, 20, anchor_x="center")
        if self.hold_block:
            for x, y in self.hold_block.shape:
                arcade.draw_rectangle_filled(
                    GRID_ORIGIN_X - 100 + (x + 1) * BLOCK_SIZE,
                    SCREEN_HEIGHT - 100 + (y + 1) * BLOCK_SIZE,
                    BLOCK_SIZE, BLOCK_SIZE, self.hold_block.color
                )

    def draw_next_pieces(self):
        for i, next_block in enumerate(self.next_blocks[:3]):
            arcade.draw_rectangle_outline(
                GRID_ORIGIN_X + GRID_WIDTH * BLOCK_SIZE + 50,
                SCREEN_HEIGHT - 100 - i * 100,
                80, 80, arcade.color.WHITE
            )
            for x, y in next_block.shape:
                arcade.draw_rectangle_filled(
                    GRID_ORIGIN_X + GRID_WIDTH * BLOCK_SIZE + 50 + (x + 1) * BLOCK_SIZE,
                    SCREEN_HEIGHT - 100 - i * 100 + (y + 1) * BLOCK_SIZE,
                    BLOCK_SIZE, BLOCK_SIZE, next_block.color
                )
        arcade.draw_text("NEXT", GRID_ORIGIN_X + GRID_WIDTH * BLOCK_SIZE + 50,
                         SCREEN_HEIGHT - 50, arcade.color.WHITE, 20, anchor_x="center")

    def draw_main_menu(self):
        arcade.draw_text("bLocKo", SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100,
                         arcade.color.WHITE, 60, anchor_x="center", font_name="Arial Black")
        
        menu_items = ["Play", "Options", "Tutorial", "Quit"]
        for i, item in enumerate(menu_items):
            color = arcade.color.YELLOW if i == self.menu_selection else arcade.color.WHITE
            arcade.draw_text(item, SCREEN_WIDTH // 2, SCREEN_HEIGHT - 200 - i * 50,
                             color, 30, anchor_x="center")
        
        move_up = key_to_string(self.key_bindings['MOVE_UP'])
        move_down = key_to_string(self.key_bindings['MOVE_DOWN'])
        select = key_to_string(self.key_bindings['SELECT'])
        arcade.draw_text(f"Use {move_up}/{move_down} to navigate, {select} to select", 
                         SCREEN_WIDTH // 2, 50, arcade.color.WHITE, 20, anchor_x="center")

    def draw_game_mode_select(self):
        arcade.draw_text("Select Game Mode", SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100,
                         arcade.color.WHITE, 40, anchor_x="center")
        
        mode_items = ["Marathon", "Sprint", "Ultra", "Pressure", "Back"]
        for i, item in enumerate(mode_items):
            color = arcade.color.YELLOW if i == self.mode_selection else arcade.color.WHITE
            arcade.draw_text(item, SCREEN_WIDTH // 2, SCREEN_HEIGHT - 200 - i * 50,
                             color, 30, anchor_x="center")
        
        move_up = key_to_string(self.key_bindings['MOVE_UP'])
        move_down = key_to_string(self.key_bindings['MOVE_DOWN'])
        select = key_to_string(self.key_bindings['SELECT'])
        arcade.draw_text(f"Use {move_up}/{move_down} to navigate, {select} to select", 
                         SCREEN_WIDTH // 2, 50, arcade.color.WHITE, 20, anchor_x="center")

    def draw_options_menu(self):
        arcade.draw_text("Options", SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100,
                         arcade.color.WHITE, 40, anchor_x="center")
        
        power_ups_text = "Power-ups: ON" if self.power_ups_enabled else "Power-ups: OFF"
        difficulty_text = f"Difficulty: {self.difficulty}"
        options_items = [power_ups_text, difficulty_text, "Key Bindings", "Back"]
        for i, item in enumerate(options_items):
            color = arcade.color.YELLOW if i == self.option_selection else arcade.color.WHITE
            arcade.draw_text(item, SCREEN_WIDTH // 2, SCREEN_HEIGHT - 200 - i * 50,
                             color, 30, anchor_x="center")
        
        move_up = key_to_string(self.key_bindings['MOVE_UP'])
        move_down = key_to_string(self.key_bindings['MOVE_DOWN'])
        select = key_to_string(self.key_bindings['SELECT'])
        arcade.draw_text(f"Use {move_up}/{move_down} to navigate, {select} to select", 
                         SCREEN_WIDTH // 2, 50, arcade.color.WHITE, 20, anchor_x="center")

    def draw_pause_screen(self):
        arcade.draw_lrtb_rectangle_filled(0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, (0, 0, 0, 150))
        arcade.draw_text("PAUSED", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                         arcade.color.WHITE, 50, anchor_x="center", anchor_y="center")
        pause_key = key_to_string(self.key_bindings['PAUSE'])
        arcade.draw_text(f"Press {pause_key} to resume", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50,
                         arcade.color.WHITE, 20, anchor_x="center")

    def draw_game_over_screen(self):
        arcade.draw_lrtb_rectangle_filled(0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, (0, 0, 0, 180))
        arcade.draw_text("GAME OVER", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50,
                         arcade.color.RED, 50, anchor_x="center")
        arcade.draw_text(f"Final Score: {self.score}", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                         arcade.color.WHITE, 30, anchor_x="center")
        select = key_to_string(self.key_bindings['SELECT'])
        arcade.draw_text(f"Press {select} to return to main menu",
                         SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 50,
                         arcade.color.WHITE, 25, anchor_x="center")
        
        arcade.draw_text("High Scores:", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 100,
                         arcade.color.YELLOW, 25, anchor_x="center")
        for i, hs in enumerate(self.high_scores[:5]):
            arcade.draw_text(f"{i+1}. Score: {hs['score']} (Level {hs['level']})",
                             SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 130 - i * 30,
                             arcade.color.WHITE, 20, anchor_x="center")

    def draw_tutorial(self):
        arcade.draw_text("Tutorial", SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50,
                         arcade.color.WHITE, 40, anchor_x="center")
        
        tutorial_steps = [
            ["Welcome to bLocKo!", "Clear lines to score points and survive as long as you can!"],
            [f"Use {key_to_string(self.key_bindings['MOVE_LEFT'])} and {key_to_string(self.key_bindings['MOVE_RIGHT'])} to move blocks left and right"],
            [f"Press {key_to_string(self.key_bindings['SOFT_DROP'])} for soft drop", f"Press {key_to_string(self.key_bindings['HARD_DROP'])} for hard drop"],
            [f"Rotate blocks with {key_to_string(self.key_bindings['ROTATE_LEFT'])} and {key_to_string(self.key_bindings['ROTATE_RIGHT'])}"],
            [f"Hold a piece with {key_to_string(self.key_bindings['HOLD'])}", f"Pause the game with {key_to_string(self.key_bindings['PAUSE'])}"],
            ["Watch out for power-ups!", "They can help or challenge you"],
            ["In Pressure mode, watch out for rising blocks!", "Clear lines quickly to survive"],
            ["You're ready to play!", f"Press {key_to_string(self.key_bindings['SELECT'])} to start"]
        ]
        
        current_step = tutorial_steps[min(self.tutorial_step, len(tutorial_steps) - 1)]
        for i, line in enumerate(current_step):
            arcade.draw_text(line, SCREEN_WIDTH // 2, SCREEN_HEIGHT - 200 - i * 40,
                             arcade.color.WHITE, 20, anchor_x="center")
        
        select = key_to_string(self.key_bindings['SELECT'])
        back = key_to_string(self.key_bindings['BACK'])
        arcade.draw_text(f"Press {select} to continue, {back} to return to menu", 
                         SCREEN_WIDTH // 2, 50, arcade.color.WHITE, 20, anchor_x="center")

    def draw_key_binding_menu(self):
        arcade.draw_text("Key Bindings", SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50,
                         arcade.color.WHITE, 40, anchor_x="center")
        
        for i, (action, key) in enumerate(self.key_bindings.items()):
            color = arcade.color.YELLOW if i == self.menu_selection else arcade.color.WHITE
            text = f"{action}: {key_to_string(key)}"
            if self.rebinding_action == action:
                text += " (Press new key)"
            arcade.draw_text(text, SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100 - i * 30,
                             color, 20, anchor_x="center")
        
        if not self.rebinding_action:
            select = key_to_string(self.key_bindings['SELECT'])
            back = key_to_string(self.key_bindings['BACK'])
            arcade.draw_text(f"Press {select} to rebind, {back} to go back", 
                             SCREEN_WIDTH // 2, 50, arcade.color.WHITE, 20, anchor_x="center")

    def handle_menu_selection(self):
        if self.game_state == GameState.MAIN_MENU:
            menu_items = ["Play", "Options", "Tutorial", "Quit"]
            selected = menu_items[self.menu_selection]
            if selected == "Play":
                self.game_state = GameState.GAME_MODE_SELECT
            elif selected == "Options":
                self.game_state = GameState.OPTIONS
            elif selected == "Tutorial":
                self.game_state = GameState.TUTORIAL
                self.tutorial_step = 0
            elif selected == "Quit":
                arcade.close_window()
        elif self.game_state == GameState.GAME_MODE_SELECT:
            mode_options = ["Marathon", "Sprint", "Ultra", "Pressure", "Back"]
            selected = mode_options[self.mode_selection]
            if selected == "Back":
                self.game_state = GameState.MAIN_MENU
            else:
                if selected == "Marathon":
                    self.game_mode = GameMode.MARATHON
                elif selected == "Sprint":
                    self.game_mode = GameMode.SPRINT
                elif selected == "Ultra":
                    self.game_mode = GameMode.ULTRA
                elif selected == "Pressure":
                    self.game_mode = GameMode.PRESSURE
                self.start_game()
        elif self.game_state == GameState.OPTIONS:
            option_items = ["Power-ups", "Difficulty", "Key Bindings", "Back"]
            selected = option_items[self.option_selection]
            if selected == "Power-ups":
                self.power_ups_enabled = not self.power_ups_enabled
            elif selected == "Difficulty":
                self.difficulty = (self.difficulty % 3) + 1
            elif selected == "Key Bindings":
                self.game_state = GameState.KEY_BINDING
                self.menu_selection = 0
            elif selected == "Back":
                self.game_state = GameState.MAIN_MENU
        elif self.game_state == GameState.KEY_BINDING:
            if self.rebinding_action:
                pass  # Waiting for key press to rebind
            else:
                self.game_state = GameState.OPTIONS

    def handle_menu_back(self):
        if self.game_state in [GameState.GAME_MODE_SELECT, GameState.OPTIONS, GameState.KEY_BINDING, GameState.TUTORIAL]:
            if self.game_state == GameState.KEY_BINDING:
                self.rebinding_action = None
            self.game_state = GameState.MAIN_MENU

    def handle_menu_up(self):
        if self.game_state == GameState.MAIN_MENU:
            self.menu_selection = (self.menu_selection - 1) % 4
        elif self.game_state == GameState.GAME_MODE_SELECT:
            self.mode_selection = (self.mode_selection - 1) % 5
        elif self.game_state == GameState.OPTIONS:
            self.option_selection = (self.option_selection - 1) % 4
        elif self.game_state == GameState.KEY_BINDING:
            self.menu_selection = (self.menu_selection - 1) % len(self.key_bindings)

    def handle_menu_down(self):
        if self.game_state == GameState.MAIN_MENU:
            self.menu_selection = (self.menu_selection + 1) % 4
        elif self.game_state == GameState.GAME_MODE_SELECT:
            self.mode_selection = (self.mode_selection + 1) % 5
        elif self.game_state == GameState.OPTIONS:
            self.option_selection = (self.option_selection + 1) % 4
        elif self.game_state == GameState.KEY_BINDING:
            self.menu_selection = (self.menu_selection + 1) % len(self.key_bindings)

    def on_key_press(self, key, modifiers):
        if key not in self.pressed_keys:
            self.pressed_keys.add(key)
            self.handle_key_action(key, modifiers)

    def on_key_release(self, key, modifiers):
        if key in self.pressed_keys:
            self.pressed_keys.remove(key)

    def handle_key_action(self, key, modifiers):
        if self.game_state == GameState.MAIN_MENU:
            self.handle_main_menu_input(key)
        elif self.game_state == GameState.GAME_MODE_SELECT:
            self.handle_game_mode_select_input(key)
        elif self.game_state == GameState.OPTIONS:
            self.handle_options_input(key)
        elif self.game_state == GameState.PLAYING:
            self.handle_playing_input(key)
        elif self.game_state == GameState.PAUSED:
            if key == self.key_bindings["PAUSE"]:
                self.game_state = GameState.PLAYING
        elif self.game_state == GameState.GAME_OVER:
            self.handle_game_over_input(key)
        elif self.game_state == GameState.TUTORIAL:
            self.handle_tutorial_input(key)
        elif self.game_state == GameState.KEY_BINDING:
            self.handle_key_binding_input(key)

    def handle_main_menu_input(self, key):
        if key == self.key_bindings["MOVE_UP"]:
            self.handle_menu_up()
        elif key == self.key_bindings["MOVE_DOWN"]:
            self.handle_menu_down()
        elif key == self.key_bindings["SELECT"]:
            self.handle_menu_selection()

    def handle_game_mode_select_input(self, key):
        if key == self.key_bindings["MOVE_UP"]:
            self.handle_menu_up()
        elif key == self.key_bindings["MOVE_DOWN"]:
            self.handle_menu_down()
        elif key == self.key_bindings["SELECT"]:
            self.handle_menu_selection()
        elif key == self.key_bindings["BACK"]:
            self.handle_menu_back()

    def handle_options_input(self, key):
        if key == self.key_bindings["MOVE_UP"]:
            self.handle_menu_up()
        elif key == self.key_bindings["MOVE_DOWN"]:
            self.handle_menu_down()
        elif key == self.key_bindings["SELECT"]:
            self.handle_menu_selection()
        elif key == self.key_bindings["BACK"]:
            self.handle_menu_back()

    def handle_playing_input(self, key):
        if self.current_block:
            if key == self.key_bindings["MOVE_LEFT"]:
                self.move_block(-1, 0)
            elif key == self.key_bindings["MOVE_RIGHT"]:
                self.move_block(1, 0)
            elif key == self.key_bindings["SOFT_DROP"]:
                self.move_block(0, -1)
            elif key == self.key_bindings["HARD_DROP"]:
                self.hard_drop()
            elif key == self.key_bindings["ROTATE_LEFT"]:
                if self.current_block.rotate(False, self):
                    arcade.play_sound(ROTATE_SOUND)
            elif key == self.key_bindings["ROTATE_RIGHT"]:
                if self.current_block.rotate(True, self):
                    arcade.play_sound(ROTATE_SOUND)
            elif key == self.key_bindings["HOLD"]:
                self.hold_piece()
        
        if key == self.key_bindings["PAUSE"]:
            self.game_state = GameState.PAUSED

    def handle_game_over_input(self, key):
        if key == self.key_bindings["SELECT"]:
            self.game_state = GameState.MAIN_MENU

    def handle_tutorial_input(self, key):
        if key == self.key_bindings["SELECT"]:
            self.tutorial_step += 1
            if self.tutorial_step >= 8:  # Adjust based on the number of tutorial steps
                self.game_state = GameState.GAME_MODE_SELECT
        elif key == self.key_bindings["BACK"]:
            self.game_state = GameState.MAIN_MENU

    def handle_key_binding_input(self, key):
        if self.rebinding_action:
            if key != arcade.key.ESCAPE:
                self.key_bindings[self.rebinding_action] = key
                self.save_key_bindings()
            self.rebinding_action = None
        else:
            if key == self.key_bindings["MOVE_UP"]:
                self.handle_menu_up()
            elif key == self.key_bindings["MOVE_DOWN"]:
                self.handle_menu_down()
            elif key == self.key_bindings["SELECT"]:
                self.rebinding_action = list(self.key_bindings.keys())[self.menu_selection]
            elif key == self.key_bindings["BACK"]:
                self.game_state = GameState.OPTIONS

    def update(self, delta_time):
        if self.game_state == GameState.PLAYING:
            current_time = time.time()

            if self.game_mode in [GameMode.SPRINT, GameMode.ULTRA]:
                if self.time_limit and current_time - self.start_time >= self.time_limit:
                    self.game_over()
                    return

            if current_time >= self.next_drop_time and not self.is_flashing:
                self.next_drop_time = current_time + self.drop_interval
                moved = self.move_block(0, -1)
                if not moved:
                    if self.lock_timer is None:
                        self.lock_timer = current_time
                else:
                    self.lock_timer = None
            
            if self.lock_timer is not None:
                if current_time - self.lock_timer >= LOCK_DELAY:
                    self.place_block()
                    self.lock_timer = None

            if self.is_flashing:
                self.handle_line_clear_animation(delta_time)

            self.particle_list.update()
            self.update_power_ups()

            if self.game_mode == GameMode.PRESSURE:
                self.update_pressure_mode(current_time)

    def handle_line_clear_animation(self, delta_time):
        self.flash_timer += delta_time
        if self.flash_timer >= self.flash_duration:
            self.flash_timer = 0
            self.flash_visible = not self.flash_visible
            self.total_flashes += 1
            if self.total_flashes >= self.max_flashes:
                self.is_flashing = False
                self.flash_timer = 0
                self.total_flashes = 0
                self.flash_visible = True
                self.clear_lines()

    def update_pressure_mode(self, current_time):
        if current_time - self.last_pressure_time >= self.pressure_interval:
            self.add_pressure_blocks()
            self.last_pressure_time = current_time
        
        if current_time - self.start_time >= PRESSURE_INCREASE_INTERVAL * (self.pressure_level + 1):
            self.increase_pressure_difficulty()

        target_height = (GRID_HEIGHT * BLOCK_SIZE) * (self.pressure_level / 10)
        self.lava_height += (target_height - self.lava_height) * 0.1

    def add_pressure_blocks(self):
        for y in range(GRID_HEIGHT + BUFFER_ZONE_HEIGHT - 1, self.pressure_height - 1, -1):
            self.grid[y] = self.grid[y - 1].copy()

        self.grid[self.pressure_height] = [GARBAGE_BLOCK_COLOR] * GRID_WIDTH

        for _ in range(random.randint(1, 2)):
            empty_index = random.randint(0, GRID_WIDTH - 1)
            self.grid[self.pressure_height][empty_index] = None

        self.flash_lines = [self.pressure_height]
        self.is_flashing = True
        self.flash_timer = 0
        self.flash_visible = True
        self.total_flashes = 0

    def increase_pressure_difficulty(self):
        self.pressure_level = min(self.pressure_level + 1, 5)
        self.pressure_interval = max(MIN_PRESSURE_INTERVAL, self.pressure_interval - 5)

    def start_game(self):
        self.setup()
        self.game_state = GameState.PLAYING
        self.start_time = time.time()
        
        if self.game_mode == GameMode.SPRINT:
            self.time_limit = 120  # 2 minutes for Sprint mode
        elif self.game_mode == GameMode.ULTRA:
            self.time_limit = 180  # 3 minutes for Ultra mode
        else:
            self.time_limit = None
    
        if not self.spawn_new_block():
            self.game_over()
            return
    
        self.next_drop_time = time.time() + self.drop_interval
        self.start_background_music()
    
        # Initialize game mode specific variables
        if self.game_mode == GameMode.PRESSURE:
            self.last_pressure_time = time.time()
            self.pressure_level = 0
            self.lava_height = 0

    def start_background_music(self):
        if self.bg_music:
            arcade.stop_sound(self.bg_music)
        self.bg_music = arcade.play_sound(BG_MUSIC, looping=True)

    def stop_background_music(self):
        if self.bg_music:
            arcade.stop_sound(self.bg_music)
            self.bg_music = None

def main():
    game = BKGame()
    arcade.run()

if __name__ == "__main__":
    main()