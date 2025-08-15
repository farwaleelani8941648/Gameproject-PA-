"""
animations.py — Handles all sprite loading, animation states, and drawing
for employees, crops, factories, and home icons.

Modules used:
    - arcade: rendering library
    - PIL (Pillow): image cropping for sprite sheets
    - glob: file search for crop frames
    - os/time: file paths and timing

IMPORTANT: Logic unchanged — only formatting, grouping, and comments were added.
"""

import arcade
import os
import time
from PIL import Image
import glob

# ================================================================
#    EMPLOYEE SPRITE SHEET SETTINGS
# ================================================================
EMPLOYEE_SPRITE_PATH = os.path.join("assets", "employees", "cat.png")
EMPLOYEE_SHEET_COLUMNS = 2
EMPLOYEE_SHEET_ROWS = 12
EMPLOYEE_FRAMES_USED = 16  # Use only the first 16 frames (2 cols × first 8 rows)
EMPLOYEE_ANIM_FPS = 8      # Animation speed

# Drawing sizes
EMPLOYEE_DRAW_SIZE = 60
HOME_ICON_SIZE = 62

# Map animation names to frame indices in sprite sheet
EMPLOYEE_ANIMATION_MAP = {
    "idle":          [0],
    "move_up":       [0, 1, 8, 9],
    "move_down":     [0, 1, 8, 9],
    "move_backward": [2, 3, 10, 11],
    "move_right":    [6],
    "move_left":     [4],
    "beat_right":    [14, 15],
    "beat_left":     [13, 12],
}

# Global cache of loaded frames
_EMPLOYEE_FRAMES = None


# ================================================================
#    EMPLOYEE SPRITE LOADING FUNCTIONS
# ================================================================
def load_employee_frames():
    """
    Loads employee sprite sheet into individual frames (arcade.Texture list).
    Uses only the first EMPLOYEE_FRAMES_USED frames.
    Caches them in _EMPLOYEE_FRAMES to avoid reloading.
    """
    global _EMPLOYEE_FRAMES
    if _EMPLOYEE_FRAMES is not None:
        return _EMPLOYEE_FRAMES

    if not os.path.exists(EMPLOYEE_SPRITE_PATH):
        raise FileNotFoundError(f"Employee sprite sheet not found: {EMPLOYEE_SPRITE_PATH}")

    # Open sprite sheet and calculate frame size
    img = Image.open(EMPLOYEE_SPRITE_PATH)
    sheet_width, sheet_height = img.width, img.height
    sprite_w = sheet_width // EMPLOYEE_SHEET_COLUMNS
    sprite_h = sheet_height // EMPLOYEE_SHEET_ROWS

    # Temporary dir to save frames before loading as arcade textures
    temp_dir = "_tmp_employee_frames"
    os.makedirs(temp_dir, exist_ok=True)

    textures = []
    for frame_idx in range(EMPLOYEE_FRAMES_USED):
        row = frame_idx // EMPLOYEE_SHEET_COLUMNS
        col = frame_idx % EMPLOYEE_SHEET_COLUMNS
        left = col * sprite_w
        upper = row * sprite_h
        right = left + sprite_w
        lower = upper + sprite_h

        # Crop frame from sheet and save temporarily
        frame = img.crop((left, upper, right, lower))
        tmp_path = os.path.join(temp_dir, f"employee_frame_{frame_idx}.png")
        frame.save(tmp_path)

        # Load into arcade texture
        tex = arcade.load_texture(tmp_path)
        textures.append(tex)

    img.close()
    _EMPLOYEE_FRAMES = textures
    return _EMPLOYEE_FRAMES


def get_employee_frame(anim_idx):
    """Return a single employee frame by animation index (wraps if overflow)."""
    frames = load_employee_frames()
    return frames[anim_idx % EMPLOYEE_FRAMES_USED]


# ================================================================
#    ANIMATION STATE CLASSES
# ================================================================
class CropAnimationState:
    """Tracks growth stage of a crop over time."""
    GROWTH_STAGES = ["seedling", "growing", "mature", "harvest"]

    def __init__(self, total_growth_time=40):
        self.growth_stage = 0
        self.stage_time = 0
        self.total_growth_time = total_growth_time
        self.last_update = time.time()

    def update(self, delta_time):
        """Advance growth stage based on elapsed time."""
        now = time.time()
        self.stage_time += now - self.last_update
        self.last_update = now
        stage_lengths = [
            self.total_growth_time * 0.25,
            self.total_growth_time * 0.30,
            self.total_growth_time * 0.35,
            float('inf')
        ]
        while self.growth_stage < len(stage_lengths) - 1 and self.stage_time > stage_lengths[self.growth_stage]:
            self.stage_time -= stage_lengths[self.growth_stage]
            self.growth_stage += 1

    def get_stage(self):
        return CropAnimationState.GROWTH_STAGES[self.growth_stage]

    def reset(self):
        """Restart growth cycle from seedling."""
        self.growth_stage = 0
        self.stage_time = 0
        self.last_update = time.time()


class FactoryAnimationState:
    """Tracks factory production state (idle, producing, done)."""
    STATES = ["idle", "producing", "done"]

    def __init__(self, production_time=20):
        self.state = 0
        self.time_in_state = 0
        self.production_time = production_time
        self.last_update = time.time()

    def update(self, delta_time):
        """Advance state to 'done' when production time passes."""
        now = time.time()
        self.time_in_state += now - self.last_update
        self.last_update = now
        if self.state == 1 and self.time_in_state > self.production_time:
            self.state = 2
            self.time_in_state = 0

    def start_production(self):
        """Switch state to producing."""
        self.state = 1
        self.time_in_state = 0
        self.last_update = time.time()

    def get_state(self):
        return FactoryAnimationState.STATES[self.state]

    def reset(self):
        """Reset to idle state."""
        self.state = 0
        self.time_in_state = 0
        self.last_update = time.time()


class EmployeeAnimationState:
    """Tracks an employee's action animation (idle, walking, harvesting)."""
    STATES = ["idle", "walking", "harvesting"]

    def __init__(self):
        self.state = 0
        self.action = "idle"
        self.frame_list = EMPLOYEE_ANIMATION_MAP["idle"]
        self.frame_idx = 0
        self.last_update = time.time()
        self.t = 0
        self.active = False

    def update(self, delta_time):
        """
        Step through animation frames when active and moving/harvesting.
        """
        now = time.time()
        elapsed = now - self.last_update
        self.t += elapsed
        self.last_update = now

        if self.active and self.state in (1, 2):
            frames = self.frame_list if self.frame_list else [0]
            if self.t > 1.0 / EMPLOYEE_ANIM_FPS:
                self.frame_idx = (self.frame_idx + 1) % len(frames)
                self.t = 0

    def set_action(self, action):
        """Change current animation action (affects frame list)."""
        self.action = action
        self.frame_list = EMPLOYEE_ANIMATION_MAP.get(action, [0])
        self.frame_idx = 0

    def set_state(self, state_str):
        """Change state by name (idle, walking, harvesting)."""
        if state_str in EmployeeAnimationState.STATES:
            self.state = EmployeeAnimationState.STATES.index(state_str)
            self.active = (self.state != 0)

    def get_state(self):
        return EmployeeAnimationState.STATES[self.state]

    def reset(self):
        """Reset to idle animation."""
        self.state = 0
        self.t = 0
        self.last_update = time.time()
        self.frame_idx = 0
        self.active = False
        self.action = "idle"
        self.frame_list = EMPLOYEE_ANIMATION_MAP["idle"]


# ================================================================
#    ATTACH ANIMATION TO GAME OBJECTS
# ================================================================
def attach_crop_animation(cell, total_growth_time=40):
    """Attach crop animation state to a cell if not already set."""
    if not hasattr(cell, "animation"):
        cell.animation = CropAnimationState(total_growth_time=total_growth_time)


def attach_factory_animation(cell, production_time=20):
    """Attach factory animation state to a cell if not already set."""
    if not hasattr(cell, "animation"):
        cell.animation = FactoryAnimationState(production_time=production_time)


def attach_employee_animation(employee):
    """Attach employee animation state to an employee if not already set."""
    if not hasattr(employee, "animation"):
        employee.animation = EmployeeAnimationState()


# ================================================================
#    HOME ICON DRAWING
# ================================================================
_HOME_ICON_SPRITE = None
_HOME_ICON_LIST = None

def draw_home_icon(pixel_x, pixel_y, home_texture):
    """
    Draw home icon at given pixel position.
    Uses sprite scaling if texture is available, otherwise draws an emoji.
    """
    global _HOME_ICON_SPRITE, _HOME_ICON_LIST
    if home_texture:
        if _HOME_ICON_SPRITE is None or _HOME_ICON_LIST is None or _HOME_ICON_SPRITE.texture != home_texture:
            _HOME_ICON_SPRITE = arcade.Sprite()
            _HOME_ICON_SPRITE.texture = home_texture
            if home_texture and home_texture.width > 0:
                _HOME_ICON_SPRITE.scale = HOME_ICON_SIZE / home_texture.width
            else:
                _HOME_ICON_SPRITE.scale = 1.0
            _HOME_ICON_SPRITE.alpha = 255
            _HOME_ICON_LIST = arcade.SpriteList()
            _HOME_ICON_LIST.append(_HOME_ICON_SPRITE)
        _HOME_ICON_SPRITE.center_x = pixel_x
        _HOME_ICON_SPRITE.center_y = pixel_y
        _HOME_ICON_LIST.draw()
    else:
        arcade.draw_text("🏠", pixel_x, pixel_y, (100, 60, 10), 48, anchor_x="center", anchor_y="center")


def draw_all_employees(employees, grid_to_pixel_fn, scale=1.0):
    """
    Draw all employees at their grid positions using their current animation frames.
    Employees appear semi-transparent if idle.
    """
    sprite_list = arcade.SpriteList()
    for emp in employees:
        if not hasattr(emp, "animation"):
            continue
        if not getattr(emp, "visible", True):
            continue

        # Convert grid position to pixel coordinates
        pos = emp.position if getattr(emp, "position", None) else (0, 0)
        pixel_x, pixel_y = grid_to_pixel_fn(*pos)

        # Get current animation frame
        anim = emp.animation
        frame_indices = anim.frame_list if hasattr(anim, "frame_list") else [0]
        frame_idx = frame_indices[anim.frame_idx % len(frame_indices)]
        frame = get_employee_frame(frame_idx)

        # Create sprite for drawing
        sprite = arcade.Sprite()
        sprite.texture = frame
        sprite.center_x = pixel_x
        sprite.center_y = pixel_y
        if sprite.texture and sprite.texture.width > 0:
            sprite.scale = scale * (EMPLOYEE_DRAW_SIZE / sprite.texture.width)
        else:
            sprite.scale = scale
        sprite.alpha = 255 if getattr(anim, "active", False) or getattr(emp, "working", False) else 96

        sprite_list.append(sprite)

    sprite_list.draw()


# ================================================================
#    CROP ANIMATION HELPERS
# ================================================================
_CROP_ANIMATION_FRAMES = {}

def load_crop_frames(crop_type):
    """
    Load all numbered PNGs for a crop type from assets/crops/<crop_type>/.
    Returns list of arcade.Texture objects, sorted by number.
    """
    if crop_type in _CROP_ANIMATION_FRAMES:
        return _CROP_ANIMATION_FRAMES[crop_type]

    folder = os.path.join("assets", "crops", crop_type)
    files = sorted(
        glob.glob(os.path.join(folder, "*.png")),
        key=lambda f: int(os.path.splitext(os.path.basename(f))[0])
    )

    if not files:
        print(f"[CROP ANIMATION] No frames found for crop: {crop_type} in {folder}")

    textures = [arcade.load_texture(f) for f in files]
    _CROP_ANIMATION_FRAMES[crop_type] = textures
    return textures


def get_crop_animation_frame(cell, crop_type, cell_grow_duration=50):
    """
    Get correct crop frame based on growth progress.
    Frames are numbered sequentially in the crop's folder.
    """
    textures = load_crop_frames(crop_type)
    total_frames = len(textures)
    if total_frames == 0:
        print(f"[CROP ANIMATION] No textures loaded for {crop_type}")
        return None

    # Determine growth time from planted_time
    planted_time = getattr(cell, "planted_time", getattr(cell, "just_planted_at", None))
    if not planted_time or planted_time == 0:
        print(f"[CROP ANIMATION] WARNING: cell for {crop_type} missing planted_time/just_planted_at")
        planted_time = 0

    grow_time = max(0, time.time() - planted_time)
    frame_duration = cell_grow_duration / total_frames if total_frames > 0 else 1
    frame_idx = min(int(grow_time / frame_duration), total_frames - 1)

    return textures[frame_idx]


def draw_crop_animation(cell, crop_type, pixel_x, pixel_y, cell_size, cell_grow_duration=50):
    """
    Draw correct animated crop frame at given pixel coordinates.
    Call this when drawing the grid for any cell containing a crop.
    """
    tex = get_crop_animation_frame(cell, crop_type, cell_grow_duration=cell_grow_duration)
    if tex:
        arcade.draw_texture_rectangle(pixel_x, pixel_y, cell_size, cell_size, tex)
