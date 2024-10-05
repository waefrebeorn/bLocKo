# bLocKo.py
import arcade
import random
import time

# Constants
SCREEN_WIDTH = 800  # Adjusted for better fit
SCREEN_HEIGHT = 800  # Increased to accommodate grid
SCREEN_TITLE = "bLocKo - The Puzzle Game"

BLOCK_SIZE = 30  # Reduced block size for better fit
GRID_WIDTH = 10
GRID_HEIGHT = 20

# Calculate grid origin to center it
GRID_ORIGIN_X = (SCREEN_WIDTH - GRID_WIDTH * BLOCK_SIZE) // 2
GRID_ORIGIN_Y = (SCREEN_HEIGHT - GRID_HEIGHT * BLOCK_SIZE) // 2

# Colors
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
GHOST_COLOR = (255, 255, 255, 50)  # Semi-transparent white
FLASH_COLOR = arcade.color.WHITE

# Movement cooldowns
HARD_DROP_COOLDOWN = 0.5  # seconds between hard drops
INITIAL_DROP_INTERVAL = 1.0  # Initial drop every second
MIN_DROP_INTERVAL = 0.05  # Minimum drop interval
LOCK_DELAY = 0.75  # seconds before a block locks after landing (25% increase)

# Rotation wall kick offsets based on SRS (Super Rotation System)
# Expanded for better wall kick handling
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

# Define 5-segment block shapes (similar to pentominoes)
BLOCK_SHAPES = [
    # 'F' shape
    [(0,1), (1,1), (1,0), (1,2), (2,1)],
    # 'I' shape
    [(0,2), (1,2), (2,2), (3,2), (4,2)],
    # 'L' shape
    [(0,0), (1,0), (2,0), (3,0), (3,1)],
    # 'N' shape
    [(0,1), (1,1), (2,1), (2,0), (3,0)],
    # 'P' shape
    [(0,0), (0,1), (1,0), (1,1), (2,0)],
    # 'T' shape
    [(0,1), (1,0), (1,1), (1,2), (2,1)],
    # 'U' shape
    [(0,0), (0,2), (1,0), (1,1), (1,2)],
    # 'V' shape
    [(0,0), (1,0), (2,0), (2,1), (2,2)],
    # 'W' shape
    [(0,0), (1,0), (1,1), (2,1), (2,2)],
    # 'Y' shape
    [(0,1), (1,0), (1,1), (2,1), (3,1)],
    # 'Z' shape
    [(0,0), (0,1), (1,1), (1,2), (2,2)]
]

# Load sounds (ensure you have these files or comment out sound-related lines)
# Uncomment the following lines if you have sound files
# HARD_DROP_SOUND = arcade.load_sound("hard_drop.wav")
# LINE_CLEAR_SOUND = arcade.load_sound("line_clear.wav")
# GAME_OVER_SOUND = arcade.load_sound("game_over.wav")


class Block:
    def __init__(self, shape, color, grid_x, grid_y, block_type='non-I'):
        """
        Initialize a new block.
        :param shape: List of (x, y) tuples representing the block shape.
        :param color: Color of the block.
        :param grid_x: X position on the grid.
        :param grid_y: Y position on the grid.
        :param block_type: Type of the block ('I' or 'non-I') for wall kicks.
        """
        self.shape = shape
        self.color = color
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.block_type = block_type  # 'I' or 'non-I'

    def get_global_positions(self):
        """
        Get the global grid positions of the block's segments.
        :return: List of (x, y) tuples.
        """
        return [(self.grid_x + x, self.grid_y + y) for x, y in self.shape]

    def move(self, dx, dy):
        """
        Move the block by dx and dy on the grid.
        :param dx: Change in x.
        :param dy: Change in y.
        """
        self.grid_x += dx
        self.grid_y += dy

    def get_width(self):
        """
        Calculate the horizontal span of the block.
        :return: Width in number of blocks.
        """
        xs = [x for x, y in self.shape]
        return max(xs) - min(xs) + 1

    def rotate_clockwise(self, grid):
        """
        Rotate the block clockwise with dynamic wall kicks.
        :param grid: Current game grid to check for collisions.
        """
        rotated_shape = [(-y + 2, x - 2) for x, y in self.shape]
        self._apply_rotation(rotated_shape, grid, clockwise=True)

    def rotate_counterclockwise(self, grid):
        """
        Rotate the block counterclockwise with dynamic wall kicks.
        :param grid: Current game grid to check for collisions.
        """
        rotated_shape = [(y - 2, -x + 2) for x, y in self.shape]
        self._apply_rotation(rotated_shape, grid, clockwise=False)

    def _apply_rotation(self, rotated_shape, grid, clockwise=True):
        """
        Apply rotation if valid, with dynamic wall kicks based on block width and proximity to walls.
        :param rotated_shape: The rotated shape coordinates.
        :param grid: Current game grid.
        :param clockwise: Boolean indicating rotation direction.
        """
        # Normalize the rotated shape
        min_x = min(x for x, y in rotated_shape)
        min_y = min(y for x, y in rotated_shape)
        normalized_shape = [(x - min_x, y - min_y) for x, y in rotated_shape]

        # Determine wall kick type
        wall_kick_type = 'I' if self.block_type == 'I' else 'non-I'
        base_offsets = WALL_KICK_OFFSETS[wall_kick_type].copy()

        # Determine additional offsets based on block width and position
        block_width = self.get_width()
        right_edge = self.grid_x + max(x for x, y in normalized_shape)
        left_edge = self.grid_x + min(x for x, y in normalized_shape)

        # Calculate distances from both walls
        distance_from_right = GRID_WIDTH - (self.grid_x + max(x for x, y in normalized_shape)) - 1
        distance_from_left = self.grid_x + min(x for x, y in normalized_shape)

        # Initialize additional_offsets list
        additional_offsets = []

        # Handle right wall proximity
        if block_width >= 4:
            if distance_from_right < 2:
                # Shift left by 2 or 3
                additional_offsets.extend([(-2, 0), (-3, 0)])
        elif block_width == 3:
            if distance_from_right < 1:
                # Shift left by 1 or 2
                additional_offsets.extend([(-1, 0), (-2, 0)])

        # Handle left wall proximity
        if block_width >= 4:
            if distance_from_left < 2:
                # Shift right by 2 or 3
                additional_offsets.extend([(2, 0), (3, 0)])
        elif block_width == 3:
            if distance_from_left < 1:
                # Shift right by 1 or 2
                additional_offsets.extend([(1, 0), (2, 0)])

        # Add additional_offsets to base_offsets
        base_offsets.extend(additional_offsets)

        # Attempt rotation with dynamic wall kicks
        for offset in base_offsets:
            test_x = self.grid_x + offset[0]
            test_y = self.grid_y + offset[1]
            temp_block = Block(normalized_shape, self.color, test_x, test_y, self.block_type)
            if self.is_rotation_valid(temp_block, grid):
                self.shape = normalized_shape
                self.grid_x = test_x
                self.grid_y = test_y
                return  # Successful rotation

        # If all wall kicks fail, rotation is not applied

    def is_rotation_valid(self, temp_block, grid):
        """
        Check if the rotated block's position is valid.
        :param temp_block: The block after rotation.
        :param grid: Current game grid.
        :return: True if valid, False otherwise.
        """
        for x, y in temp_block.get_global_positions():
            if x < 0 or x >= GRID_WIDTH or y < 0 or y >= GRID_HEIGHT:
                return False  # Out of bounds
            if grid[y][x]:
                return False  # Collision with existing block
        return True


class BKGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(BACKGROUND_COLOR)
        self.grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_block = self.get_new_block()
        self.next_block = self.get_new_block()
        self.score = 0
        self.level = 1
        self.lines_cleared = 0

        self.last_hard_drop_time = -HARD_DROP_COOLDOWN  # Initialize to allow first hard drop

        self.next_drop_time = time.time() + INITIAL_DROP_INTERVAL  # Initial drop
        self.drop_interval = INITIAL_DROP_INTERVAL

        self.flash_lines = []  # Lines to flash before clearing
        self.is_flashing = False
        self.flash_timer = 0
        self.flash_duration = 0.1  # Seconds for each flash (faster)
        self.total_flashes = 0
        self.max_flashes = 4  # Total number of flashes
        self.flash_visible = True  # Toggle visibility for flashing

        self.lock_timer = None  # Timer for lock delay

        self.game_over_flag = False

    def get_new_block(self):
        """
        Create a new random block at the top of the grid.
        :return: Block instance.
        """
        shape = random.choice(BLOCK_SHAPES)
        color = random.choice(BLOCK_COLORS)
        # Determine block type
        block_type = 'I' if shape == [(0,2), (1,2), (2,2), (3,2), (4,2)] else 'non-I'
        # Center the block by adjusting grid_x. Since some shapes can extend up to +4, adjust accordingly.
        # Find the leftmost x in the shape to center it
        min_shape_x = min(x for x, y in shape)
        max_shape_x = max(x for x, y in shape)
        block_width = max_shape_x - min_shape_x + 1
        grid_x = (GRID_WIDTH - block_width) // 2 - min_shape_x  # Centered
        grid_y = GRID_HEIGHT - max(y for x, y in shape) - 1  # Position block at top

        new_block = Block(shape, color, grid_x, grid_y, block_type)
        if not self.is_valid_position(new_block.get_global_positions()):
            self.game_over()
        return new_block

    def on_draw(self):
        arcade.start_render()
        # Draw grid background
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                screen_x = GRID_ORIGIN_X + x * BLOCK_SIZE + BLOCK_SIZE / 2
                screen_y = GRID_ORIGIN_Y + y * BLOCK_SIZE + BLOCK_SIZE / 2
                arcade.draw_rectangle_outline(
                    screen_x,
                    screen_y,
                    BLOCK_SIZE,
                    BLOCK_SIZE,
                    GRID_COLOR
                )
                if self.grid[y][x]:
                    arcade.draw_rectangle_filled(
                        screen_x,
                        screen_y,
                        BLOCK_SIZE,
                        BLOCK_SIZE,
                        self.grid[y][x]
                    )
        # Draw ghost block
        if self.current_block and not self.is_flashing:
            ghost_positions = self.get_ghost_position()
            for pos in ghost_positions:
                x, y = pos
                screen_x = GRID_ORIGIN_X + x * BLOCK_SIZE + BLOCK_SIZE / 2
                screen_y = GRID_ORIGIN_Y + y * BLOCK_SIZE + BLOCK_SIZE / 2
                arcade.draw_rectangle_filled(
                    screen_x,
                    screen_y,
                    BLOCK_SIZE,
                    BLOCK_SIZE,
                    GHOST_COLOR
                )
        # Draw current block
        if self.current_block and not self.is_flashing:
            for pos in self.current_block.get_global_positions():
                x, y = pos
                # Ensure y is within grid to prevent IndexError
                if 0 <= y < GRID_HEIGHT and 0 <= x < GRID_WIDTH:
                    screen_x = GRID_ORIGIN_X + x * BLOCK_SIZE + BLOCK_SIZE / 2
                    screen_y = GRID_ORIGIN_Y + y * BLOCK_SIZE + BLOCK_SIZE / 2
                    arcade.draw_rectangle_filled(
                        screen_x,
                        screen_y,
                        BLOCK_SIZE,
                        BLOCK_SIZE,
                        self.current_block.color
                    )
        # Draw flashing lines
        if self.is_flashing and self.flash_visible:
            for y in self.flash_lines:
                for x in range(GRID_WIDTH):
                    if self.grid[y][x]:
                        screen_x = GRID_ORIGIN_X + x * BLOCK_SIZE + BLOCK_SIZE / 2
                        screen_y = GRID_ORIGIN_Y + y * BLOCK_SIZE + BLOCK_SIZE / 2
                        arcade.draw_rectangle_filled(
                            screen_x,
                            screen_y,
                            BLOCK_SIZE,
                            BLOCK_SIZE,
                            FLASH_COLOR
                        )
        # Draw score and level
        arcade.draw_text(f"Score: {self.score}", 10, SCREEN_HEIGHT - 30, arcade.color.WHITE, 20)
        arcade.draw_text(f"Level: {self.level}", 200, SCREEN_HEIGHT - 30, arcade.color.WHITE, 20)
        # Draw Next Block Preview
        self.draw_next_block()
        # Draw Game Over screen
        if self.game_over_flag:
            arcade.draw_lrtb_rectangle_filled(
                0,
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
                0,
                (0, 0, 0, 180)  # Semi-transparent overlay
            )
            arcade.draw_text("GAME OVER", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 20,
                             arcade.color.RED, 50, anchor_x="center")
            arcade.draw_text(f"Final Score: {self.score}", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 30,
                             arcade.color.WHITE, 30, anchor_x="center")
            arcade.draw_text("Press ENTER to Restart", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 80,
                             arcade.color.WHITE, 25, anchor_x="center")

    def draw_next_block(self):
        """
        Draw the next block preview to the right of the grid.
        """
        if self.next_block:
            
            arcade.draw_text(
                "Next:",
                GRID_ORIGIN_X + GRID_WIDTH * BLOCK_SIZE + 20,
                GRID_ORIGIN_Y + GRID_HEIGHT * BLOCK_SIZE - 40 - (2 * BLOCK_SIZE),  
                arcade.color.WHITE,
                20,
                anchor_x="left"
            )
            # Position the next block preview to the right of the grid, adjusted down by 60 pixels
            offset_x = GRID_ORIGIN_X + GRID_WIDTH * BLOCK_SIZE + 20
            offset_y = GRID_ORIGIN_Y + GRID_HEIGHT * BLOCK_SIZE - 210 - (2 * BLOCK_SIZE) 
            # Calculate the bounding box of the next block to center it
            min_x = min(x for x, y in self.next_block.shape)
            max_x = max(x for x, y in self.next_block.shape)
            min_y = min(y for x, y in self.next_block.shape)
            max_y = max(y for x, y in self.next_block.shape)
            block_width = max_x - min_x + 1
            block_height = max_y - min_y + 1
            # Center the block within a designated area
            center_x = offset_x
            center_y = offset_y + (block_height * BLOCK_SIZE) / 2
            for pos in self.next_block.shape:
                x, y = pos
                screen_x = center_x + (x - min_x) * BLOCK_SIZE
                screen_y = center_y + (y - min_y) * BLOCK_SIZE
                arcade.draw_rectangle_filled(
                    screen_x + BLOCK_SIZE / 2,
                    screen_y + BLOCK_SIZE / 2,
                    BLOCK_SIZE,
                    BLOCK_SIZE,
                    self.next_block.color
                )

    def get_ghost_position(self):
        """
        Calculate the ghost position for the current block.
        :return: List of (x, y) tuples representing the ghost block positions.
        """
        ghost_block = Block(
            self.current_block.shape.copy(),
            arcade.color.WHITE,
            self.current_block.grid_x,
            self.current_block.grid_y,
            self.current_block.block_type
        )
        while self.is_valid_position([(x, y - 1) for x, y in ghost_block.get_global_positions()]):
            ghost_block.move(0, -1)
        return ghost_block.get_global_positions()

    def update(self, delta_time):
        if self.game_over_flag:
            return  # Do not update the game if it's over

        current_time = time.time()

        # Handle block dropping
        if current_time >= self.next_drop_time and not self.is_flashing:
            self.next_drop_time = current_time + self.drop_interval
            moved = self.move_block(0, -1)
            if not moved:
                if self.lock_timer is None:
                    self.lock_timer = current_time
        else:
            # Check lock delay
            if self.lock_timer is not None:
                if current_time - self.lock_timer >= LOCK_DELAY:
                    self.place_block()
                # Optionally, you can add visual feedback for lock delay here

        # Handle flashing animation
        if self.is_flashing:
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
                    self.clear_flash_lines()

    def move_block(self, dx, dy):
        """
        Move the current block by dx and dy. If movement is not possible, set lock timer if dy is -1.
        :param dx: Change in x.
        :param dy: Change in y.
        :return: True if movement was successful, False otherwise.
        """
        if self.current_block:
            # Check collision
            new_positions = [(x + dx, y + dy) for x, y in self.current_block.get_global_positions()]
            if self.is_valid_position(new_positions):
                self.current_block.move(dx, dy)
                # Reset lock timer on any movement
                if self.lock_timer is not None:
                    self.lock_timer = None
                return True
            else:
                if dy == -1:
                    if self.lock_timer is None:
                        self.lock_timer = time.time()
                # Horizontal movements are ignored if invalid
                return False
        return False

    def is_valid_position(self, positions):
        """
        Check if the given positions are valid (within grid and not colliding).
        :param positions: List of (x, y) tuples.
        :return: True if valid, False otherwise.
        """
        for x, y in positions:
            if x < 0 or x >= GRID_WIDTH or y < 0 or y >= GRID_HEIGHT:
                return False  # Out of bounds
            if self.grid[y][x]:
                return False  # Collision with existing block
        return True

    def place_block(self):
        """
        Place the current block on the grid and check for line clears.
        """
        for x, y in self.current_block.get_global_positions():
            if y >= GRID_HEIGHT or y < 0 or x < 0 or x >= GRID_WIDTH:
                self.game_over()
                return
            self.grid[y][x] = self.current_block.color
        self.clear_lines()
        self.current_block = self.next_block
        self.next_block = self.get_new_block()
        self.lock_timer = None

    def clear_lines(self):
        """
        Check for and clear complete lines, update score and level.
        Implements flash animation before clearing.
        """
        lines_to_clear = []
        for y in range(GRID_HEIGHT):
            if all(self.grid[y][x] is not None for x in range(GRID_WIDTH)):
                lines_to_clear.append(y)

        if lines_to_clear:
            self.flash_lines = lines_to_clear.copy()
            self.is_flashing = True
            self.flash_timer = 0
            self.flash_visible = True
            self.total_flashes = 0
            # Play line clear sound
            # Uncomment if you have the sound file
            # arcade.play_sound(LINE_CLEAR_SOUND)
        else:
            # No lines to clear, continue the game
            pass

    def clear_flash_lines(self):
        """
        Remove the lines after flashing and update the grid.
        """
        for y in sorted(self.flash_lines, reverse=True):
            del self.grid[y]
            self.grid.append([None for _ in range(GRID_WIDTH)])
        self.update_score_and_level(len(self.flash_lines))
        self.flash_lines = []

    def update_score_and_level(self, lines_cleared):
        """
        Update the score and level based on the number of lines cleared.
        :param lines_cleared: Number of lines cleared.
        """
        if lines_cleared > 0:
            self.lines_cleared += lines_cleared
            self.score += (100 * lines_cleared) * self.level
            # Bonus for multiple line clears
            if lines_cleared > 1:
                self.score += (50 * (lines_cleared - 1)) * self.level
            # Level progression similar to Tetris
            self.level = self.lines_cleared // 10 + 1

    def game_over(self):
        """
        Handle game over state.
        """
        self.game_over_flag = True
        # Play game over sound
        # Uncomment if you have the sound file
        # arcade.play_sound(GAME_OVER_SOUND)

    def on_key_press(self, key, modifiers):
        if self.game_over_flag:
            if key == arcade.key.ENTER:
                self.restart_game()
            return

        if self.current_block:
            moved = False
            if key == arcade.key.LEFT:
                moved = self.move_block(-1, 0)
            elif key == arcade.key.RIGHT:
                moved = self.move_block(1, 0)
            elif key == arcade.key.UP:
                # Immediate Soft Drop
                moved = self.move_block(0, -1)
            elif key in (arcade.key.LSHIFT, arcade.key.RSHIFT):
                # Perform hard drop if cooldown has passed
                current_time = time.time()
                if current_time - self.last_hard_drop_time >= HARD_DROP_COOLDOWN:
                    self.hard_drop()
                    self.last_hard_drop_time = current_time
            elif key == arcade.key.Z:
                self.current_block.rotate_counterclockwise(self.grid)
                # Reset lock timer after rotation
                if self.lock_timer is not None:
                    self.lock_timer = None
            elif key == arcade.key.X:
                self.current_block.rotate_clockwise(self.grid)
                # Reset lock timer after rotation
                if self.lock_timer is not None:
                    self.lock_timer = None
            elif key == arcade.key.SPACE:
                self.hard_drop()

            # If any movement or rotation occurred, reset the lock timer
            if moved:
                if self.lock_timer is not None:
                    self.lock_timer = None

    def on_key_release(self, key, modifiers):
        pass  # No action needed for Option 1

    def hard_drop(self):
        """
        Instantly drop the block to the lowest possible position.
        """
        # Play hard drop sound
        # Uncomment if you have the sound file
        # arcade.play_sound(HARD_DROP_SOUND)
        while self.move_block(0, -1):
            pass
        # After hard drop, place the block
        self.place_block()

    def restart_game(self):
        """
        Restart the game after Game Over.
        """
        self.grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_block = self.get_new_block()
        self.next_block = self.get_new_block()
        self.score = 0
        self.level = 1
        self.lines_cleared = 0

        self.last_hard_drop_time = -HARD_DROP_COOLDOWN  # Reset hard drop cooldown

        self.next_drop_time = time.time() + INITIAL_DROP_INTERVAL  # Reset drop timer

        self.flash_lines = []  # Reset flash lines
        self.is_flashing = False
        self.flash_timer = 0
        self.flash_visible = True
        self.total_flashes = 0

        self.lock_timer = None  # Reset lock timer

        self.game_over_flag = False


def main():
    game = BKGame()
    arcade.run()


if __name__ == "__main__":
    main()
