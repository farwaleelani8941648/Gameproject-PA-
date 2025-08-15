"""
game_window.py
--------------
Main Arcade view for the 2D farming game.

This file is responsible for:
- Rendering: grid, panels, icons, overlays, and animated sprites
- Input: mouse hover/clicks, keyboard shortcuts
- Employee activation and assignment to crops
- Game loop updates: periodic resource ticks, animations, and win checks

IMPORTANT: No logic was changed. Only comments and formatting were added.
"""

import arcade
import os
import time

from game.game_state import GameState
from ui.theme import (
    BG_COLOR, WOOD_LIGHT, WOOD_DARK, WOOD_OUTLINE,
    PANEL_BG, PANEL_BORDER,
    HEADING_COLOR, LABEL_COLOR, VALUE_COLOR,
    OP_SELECTED, OP_LOCKED, HOVER_COLOR,
    BUTTON_BG, BUTTON_HOVER, BUTTON_TXT,
    PANEL_PADDING
)
from ui.icons import crop_icons, factory_icons
from ui.icons import home_icon_texture, home_icon_fallback
from ui.animations import draw_home_icon, attach_employee_animation, draw_all_employees
from ui.game_ui_utils import (
    OPERATION_LIST, OPERATION_REQUIRE_LEVEL,
    GRID_SIZE, get_crops_and_factories, get_resources
)
from ui.drawing_helpers import (
    draw_panel, draw_goals_panel, draw_wooden_grid, draw_operation_panel,
    draw_two_column_panel, draw_resource_panel
)

# =====================================================================
#                         GAME WINDOW (MAIN VIEW)
# =====================================================================

class GameWindow(arcade.View):
    """Main game window for 2D farm sim (grid, panels, UI, all input)."""

    # Fixed pixel size for the central grid area
    GRID_PIXEL_WIDTH = 800
    GRID_PIXEL_HEIGHT = 500

    # --------------------- 1. INITIALIZATION & STATE --------------------
    def __init__(self, username, save_id=None):
        """
        Create the game window and load or initialize the GameState.

        Args:
            username (str): Player name shown in the HUD.
            save_id (int|None): If provided, loads that save; otherwise starts a new state.
        """
        super().__init__()

        # Basic identifiers and UI flags
        self.username = username
        self.GRID_SIZE = GRID_SIZE
        self.grid_hover = (-1, -1)          # (row, col) under mouse or (-1,-1) if none
        self.status_msg = ""                # bottom status/hint line
        self.win_mode = False               # overlay when game is won
        self.selected_operation = -1        # index in OPERATION_LIST; -1 means none selected
        self.selected_crop = "corn"         # default crop for "Plant Crop"
        self.selected_factory = "soil_factory"  # default factory for "Place Factory"

        # Periodic auto-harvest timer (seconds)
        self.last_tick_time = time.time()
        self.tick_interval = 60

        # Hover states for buttons/operations
        self._save_hover = False
        self._quit_hover = False
        self._op_hover = -1

        # If an employee was just activated (index), show a message and wait for crop click
        self.active_employee_idx = None

        # Load home icon texture (fallback to emoji if missing)
        home_icon_path = os.path.join("assets", "icons", "home.png")
        self.home_icon_texture = None
        if os.path.exists(home_icon_path):
            self.home_icon_texture = arcade.load_texture(home_icon_path)

        # State load (existing save) or new state
        if save_id is not None:
            self.game_state = GameState(self.username, grid_size=self.GRID_SIZE)
            load_msg = self.game_state.load_game(save_id)
            self.status_msg = load_msg
        else:
            self.game_state = GameState(self.username, grid_size=self.GRID_SIZE)

        # Attach animation state to each employee (needed for drawing/updating)
        if hasattr(self.game_state, "employees"):
            for emp in self.game_state.employees:
                attach_employee_animation(emp)

    # --------------------- 2. MAIN DRAWING LOGIC -----------------------
    def on_show_view(self):
        """Called once when the view is shown: set background color."""
        arcade.set_background_color(BG_COLOR)

    def grid_to_pixel(self, row, col):
        """
        Convert a grid cell (row, col) to screen pixel coordinates (center of the cell).
        """
        w, h = self.window.width, self.window.height
        grid_w, grid_h = self.GRID_PIXEL_WIDTH, self.GRID_PIXEL_HEIGHT
        grid_x = (w - grid_w) // 2
        grid_y = (h - grid_h) // 2
        cell_w = grid_w / self.GRID_SIZE
        cell_h = grid_h / self.GRID_SIZE
        pixel_x = grid_x + col * cell_w + cell_w / 2
        pixel_y = grid_y + row * cell_h + cell_h / 2
        return pixel_x, pixel_y

    def on_draw(self):
        """
        Render the full UI:
          - resource panel (top)
          - crops/factories panel + save/quit (left)
          - goals/instructions (right)
          - operation bar (bottom)
          - grid with animated crops/factories and employees
          - overlays (player info, hints, win message)
        """
        self.clear()

        # Common layout and panel sizes
        w, h = self.window.width, self.window.height
        grid_w, grid_h = self.GRID_PIXEL_WIDTH, self.GRID_PIXEL_HEIGHT
        pad = PANEL_PADDING
        panel_gap = 18
        left_panel_w = int(w * 0.20)
        right_panel_w = int(w * 0.20)
        grid_x = (w - grid_w) // 2
        grid_y = (h - grid_h) // 2

        # ---------- Resource Panel (top center) ----------
        resource_panel_h = 76
        resource_panel_y = grid_y + grid_h + panel_gap
        draw_resource_panel(
            grid_x, resource_panel_y, grid_w, resource_panel_h,
            get_resources(self.game_state.resources),
            PANEL_BG, PANEL_BORDER, HEADING_COLOR, LABEL_COLOR, VALUE_COLOR
        )

        # ---------- Crops/Factories (left) ----------
        crops_list, factories_list = get_crops_and_factories(self.game_state)
        crops_panel_h = grid_h
        crops_panel_y = grid_y
        crops_panel_x = grid_x - left_panel_w - pad
        draw_two_column_panel(
            crops_panel_x, crops_panel_y, left_panel_w, crops_panel_h,
            "Crops", crops_list, "Factories", factories_list,
            PANEL_BG, PANEL_BORDER, HEADING_COLOR, VALUE_COLOR
        )

        # ---------- Save/Quit Buttons ----------
        btn_w, btn_h = 152, 48
        btn_x = crops_panel_x + (left_panel_w - btn_w) // 2
        save_y = crops_panel_y - btn_h - 20
        quit_y = save_y - btn_h - 16
        for label, y, hover in [("💾 Save Game", save_y, self._save_hover), ("⏻ Quit Game", quit_y, self._quit_hover)]:
            left = btn_x
            right = btn_x + btn_w
            bottom = y
            top = y + btn_h
            # Drop shadow
            arcade.draw_lrbt_rectangle_filled(left + 3, right + 3, bottom - 3, top + 3, (120, 120, 120, 36))
            # Button face (hover-aware)
            arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, BUTTON_HOVER if hover else BUTTON_BG)
            arcade.draw_lrbt_rectangle_outline(left, right, bottom, top, PANEL_BORDER, 2)
            # Button label
            arcade.draw_text(label, (left + right) / 2, (bottom + top) / 2, BUTTON_TXT, 18,
                             anchor_x="center", anchor_y="center", bold=True)

        # ---------- Goals/Instructions (right) ----------
        goals_panel_x = grid_x + grid_w + pad
        right_panel_h = min(630, h - 2 * pad)
        goals_panel_y = (h - right_panel_h) // 2
        draw_goals_panel(
            goals_panel_x, goals_panel_y, right_panel_w, right_panel_h,
            self.get_level_instructions, self.get_level_goals,
            bg_color=PANEL_BG, border_color=PANEL_BORDER,
            heading_color=HEADING_COLOR, label_color=LABEL_COLOR, value_color=VALUE_COLOR
        )

        # ---------- Operation panel (bottom) ----------
        operation_panel_h = 40
        operation_panel_y = grid_y - operation_panel_h - panel_gap
        level = getattr(self.game_state, "level", 1)
        locked_idx = [i for i, req in enumerate(OPERATION_REQUIRE_LEVEL) if req > level]
        draw_operation_panel(
            grid_x, operation_panel_y, grid_w, operation_panel_h,
            OPERATION_LIST,
            self.selected_operation if self.selected_operation >= 0 else self._op_hover,
            locked_idx,
            PANEL_BG, PANEL_BORDER, HEADING_COLOR, VALUE_COLOR, OP_SELECTED, OP_LOCKED
        )

        # ---------- Wooden Grid (with per-cell crop invisibility and animation) ----------
        draw_wooden_grid(
            grid_x, grid_y, grid_w, grid_h, self.GRID_SIZE,
            self.game_state.grid, self.grid_hover, self.selected_operation, OPERATION_LIST,
            crop_icons, factory_icons, WOOD_DARK, WOOD_LIGHT, HOVER_COLOR, WOOD_OUTLINE, VALUE_COLOR
        )

        # ---------- HOME ICON ON (0,0) ----------
        pixel_x, pixel_y = self.grid_to_pixel(0, 0)
        draw_home_icon(pixel_x, pixel_y, self.home_icon_texture or home_icon_fallback)

        # ---------- EMPLOYEE ANIMATION ----------
        if hasattr(self.game_state, "employees"):
            draw_all_employees(self.game_state.employees, self.grid_to_pixel, scale=1.5)

        # ---------- TEXT OVERLAYS: All below operation panel ----------
        overlay_x = w // 2
        base_y = operation_panel_y - pad - 10  # start drawing overlay text below operations

        # Player name (top-right, always visible)
        arcade.draw_text(
            f"Player: {self.username}", w - pad, h - pad // 2,
            (110, 76, 33), 26, anchor_x="right", anchor_y="top", bold=True
        )

        # Use consistent font + spacing for the 3 lines below
        BOTTOM_FONT = 16
        BOTTOM_SPACING = 22
        line_y = base_y

        # 1) Employee activation helper
        if self.active_employee_idx is not None:
            arcade.draw_text(
                f"Employee {self.active_employee_idx+1} activated! Click a mature crop to assign.",
                overlay_x, line_y, (60, 120, 30), BOTTOM_FONT, anchor_x="center", bold=True
            )
            line_y -= BOTTOM_SPACING

        # 2) Selected crop/factory message
        select_msg = ""
        if self.selected_operation >= 0:
            op = OPERATION_LIST[self.selected_operation]
            if op == "Plant Crop":
                select_msg = f"Selected Crop: {self.selected_crop.title()}"
            elif op == "Place Factory":
                select_msg = f"Selected Factory: {self.selected_factory.replace('_', ' ').title()}"
        if select_msg:
            arcade.draw_text(select_msg, overlay_x, line_y, (135, 85, 40), BOTTOM_FONT, anchor_x="center", bold=True)
            line_y -= BOTTOM_SPACING

        # 3) Status message or contextual hint
        if self.status_msg:
            arcade.draw_text(self.status_msg, overlay_x, line_y, (180, 50, 50), BOTTOM_FONT,
                             anchor_x="center", bold=True)
            line_y -= BOTTOM_SPACING
        else:
            msg = ""
            if self.selected_operation == -1:
                msg = "Select an operation below to begin."
            else:
                op = OPERATION_LIST[self.selected_operation]
                if op in ["Plant Crop", "Replace Crop"]:
                    msg = "Press 1=🌽, 2=🌾, 3=🍆 to choose crop"
                elif op in ["Place Factory", "Replace Factory"]:
                    msg = "Press S=🟫, W=🌲, M=🛠️ to choose factory"
            if msg:
                arcade.draw_text(msg, overlay_x, line_y, (85, 125, 155), BOTTOM_FONT, anchor_x="center")
                line_y -= BOTTOM_SPACING

        # ---------- WIN OVERLAY & MAXIMIZE WARNING (unchanged) ----------
        if self.win_mode:
            overlay_w, overlay_h = int(w * 0.53), int(h * 0.22)
            left = w // 2 - overlay_w // 2
            right = w // 2 + overlay_w // 2
            bottom = h // 2 - overlay_h // 2
            top = h // 2 + overlay_h // 2
            arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, (0, 0, 0, 110))
            arcade.draw_lrbt_rectangle_filled(left + 8, right - 8, bottom + 8, top - 8, (180, 250, 200, 255))
            arcade.draw_text("🎉 YOU WIN! 🎉", w // 2, h // 2 + int(overlay_h * 0.18),
                             (34, 87, 44), 36, anchor_x="center", bold=True)
            arcade.draw_text("Press ESC to quit", w // 2, h // 2 - int(overlay_h * 0.13),
                             (60, 70, 110), 18, anchor_x="center", bold=True)

        # Prompt user to maximize if the window is small
        if w < 1200 or h < 700:
            arcade.draw_text(
                "🔴 Please maximize window for the best experience.",
                w // 2, h // 2, (190, 22, 34), 24, anchor_x="center", bold=True
            )

    # ---------------- 3. MOUSE EVENTS (HOVER) ------------------
    def on_mouse_motion(self, x, y, dx, dy):
        """
        Track hovering over:
          - Save/Quit buttons
          - Operation bar sections
          - Grid cells (row, col)
        """
        w, h = self.window.width, self.window.height
        grid_w, grid_h = self.GRID_PIXEL_WIDTH, self.GRID_PIXEL_HEIGHT
        grid_x = (w - grid_w) // 2
        grid_y = (h - grid_h) // 2
        pad = PANEL_PADDING
        panel_gap = 18
        left_panel_w = int(w * 0.20)

        # Save/Quit button rects
        btn_w, btn_h = 152, 48
        crops_panel_y = grid_y
        btn_x = grid_x - left_panel_w - pad + (left_panel_w - btn_w) // 2
        save_y = crops_panel_y - btn_h - 20
        quit_y = save_y - btn_h - 16

        # Hover flags for buttons
        self._save_hover = (btn_x <= x <= btn_x + btn_w and save_y <= y <= save_y + btn_h)
        self._quit_hover = (btn_x <= x <= btn_x + btn_w and quit_y <= y <= quit_y + btn_h)

        # Operation bar hover
        op_panel_h = 68
        op_panel_y = grid_y - op_panel_h - panel_gap
        op_bar_left = grid_x
        op_bar_right = grid_x + grid_w
        op_bar_bottom = op_panel_y
        op_bar_top = op_panel_y + op_panel_h
        self._op_hover = -1
        if op_bar_left <= x <= op_bar_right and op_bar_bottom <= y <= op_bar_top:
            section_w = grid_w / len(OPERATION_LIST)
            idx = int((x - op_bar_left) // section_w)
            if 0 <= idx < len(OPERATION_LIST):
                self._op_hover = idx

        # Grid cell hover (row, col)
        cell_size_x = grid_w / self.GRID_SIZE
        cell_size_y = grid_h / self.GRID_SIZE
        col = int((x - grid_x) // cell_size_x)
        row = int((y - grid_y) // cell_size_y)
        if 0 <= row < self.GRID_SIZE and 0 <= col < self.GRID_SIZE:
            self.grid_hover = (row, col)
        else:
            self.grid_hover = (-1, -1)

    # ---------------- 4. MOUSE CLICK & EMPLOYEE ASSIGNMENT ------------------
    def on_mouse_press(self, x, y, button, modifiers):
        """
        Handle left-click actions:
          - Save/Quit buttons
          - Selecting an operation in the bottom bar
          - Clicking grid: employee activation at (0,0), assignment to crops, or running the selected operation
        """
        w, h = self.window.width, self.window.height
        grid_w, grid_h = self.GRID_PIXEL_WIDTH, self.GRID_PIXEL_HEIGHT
        grid_x = (w - grid_w) // 2
        grid_y = (h - grid_h) // 2
        pad = PANEL_PADDING
        panel_gap = 18
        left_panel_w = int(w * 0.20)
        btn_w, btn_h = 152, 48
        crops_panel_y = grid_y
        btn_x = grid_x - left_panel_w - pad + (left_panel_w - btn_w) // 2
        save_y = crops_panel_y - btn_h - 20
        quit_y = save_y - btn_h - 16

        # Save/Quit Buttons
        if btn_x <= x <= btn_x + btn_w and save_y <= y <= save_y + btn_h:
            msg = self.game_state.save_game()
            self.status_msg = f"SAVED: {msg}"
            return
        if btn_x <= x <= btn_x + btn_w and quit_y <= y <= quit_y + btn_h:
            arcade.close_window()
            return

        # Operation bar click → select operation (if level allows)
        op_panel_h = 68
        op_panel_y = grid_y - op_panel_h - panel_gap
        op_bar_left = grid_x
        op_bar_right = grid_x + grid_w
        op_bar_bottom = op_panel_y
        op_bar_top = op_panel_y + op_panel_h
        section_w = grid_w / len(OPERATION_LIST)
        if op_bar_left <= x <= op_bar_right and op_bar_bottom <= y <= op_bar_top:
            idx = int((x - op_bar_left) // section_w)
            level = getattr(self.game_state, "level", 1)
            if 0 <= idx < len(OPERATION_LIST) and OPERATION_REQUIRE_LEVEL[idx] <= level:
                self.selected_operation = idx
                self.status_msg = ""  # clear any previous error/hint
            return

        # ---------- GRID CLICK HANDLING ----------
        cell_size_x = grid_w / self.GRID_SIZE
        cell_size_y = grid_h / self.GRID_SIZE
        col = int((x - grid_x) // cell_size_x)
        row = int((y - grid_y) // cell_size_y)
        if not (0 <= row < self.GRID_SIZE and 0 <= col < self.GRID_SIZE):
            return

        cell = self.game_state.grid[row][col]

        # If grid is empty and not trying to plant, show message and block
        if self.selected_operation != -1 and OPERATION_LIST[self.selected_operation] != "Plant Crop":
            if all(cell.cell_type is None for row_cells in self.game_state.grid for cell in row_cells):
                self.status_msg = "Please plant crops first!"
                return

        # EMPLOYEE ACTIVATION: Click home/hub (0,0) to activate an idle employee
        if (row, col) == (0, 0):
            for idx, emp in enumerate(self.game_state.employees):
                if not emp.active and not emp.working:
                    result, msg = self.game_state.activate_employee(idx)
                    self.active_employee_idx = idx if result else None
                    self.status_msg = msg
                    return
            self.status_msg = "No idle employees available!"
            return

        # EMPLOYEE ASSIGNMENT: Assign the selected employee to a mature crop
        if self.active_employee_idx is not None:
            cell = self.game_state.grid[row][col]
            if cell.cell_type in crop_icons and cell.level >= 1:
                if getattr(cell, 'being_harvested', False):
                    self.status_msg = "This crop is already being harvested!"
                    return
                result, msg = self.game_state.assign_employee_to_crop(row, col)
                self.status_msg = msg
                if result:
                    self.active_employee_idx = None
                return
            else:
                self.status_msg = "Click a mature crop to assign employee!"
            return

        # DEFAULT: All other grid operations (plant, factory, replace, upgrade)
        if self.selected_operation == -1 or self.win_mode:
            return

        op = OPERATION_LIST[self.selected_operation]
        if op == "Plant Crop":
            success, msg = self.game_state.plant_crop(row, col, self.selected_crop)
        elif op == "Replace Crop":
            success, msg = self.game_state.replace_crop(row, col)
        elif op == "Place Factory":
            success, msg = self.game_state.place_factory(row, col, self.selected_factory)
        elif op == "Replace Factory":
            success, msg = self.game_state.replace_factory(row, col)
        elif op == "Upgrade Factory":
            success, msg = self.game_state.upgrade(row, col, max_level=2)
        else:
            success, msg = False, "Unknown operation."
        self.status_msg = msg

    # ------------------ 5. UPDATE / ANIMATION / WIN STATE -------------------
    def on_update(self, delta_time):
        """
        Game loop:
          - Periodic auto-harvest tick
          - Employee updates (movement/harvest state machine)
          - Crop "regrow" handler (kept as a placeholder by design)
          - Employee animation frame updates
          - Check goals/win conditions and set overlays/messages
        """
        if self.win_mode:
            return

        now = time.time()

        # Periodic auto-harvest/produce tick
        if now - self.last_tick_time > self.tick_interval:
            msg = self.game_state.harvest_and_produce()
            self.status_msg = msg
            self.last_tick_time = now

        # Employee movement, harvesting logic, etc.
        self.game_state.update_employees(delta_time)

        # Instantly regrow all harvested crops to mature (level 1)
        # (Your logic keeps this as a no-op placeholder; left intact.)
        self.game_state.grow_crops()

        # Employee animation frame updates based on current state
        for emp in self.game_state.employees:
            if hasattr(emp, "animation"):
                if emp.harvesting:
                    emp.animation.set_state("harvesting")
                elif emp.active and emp.working:
                    emp.animation.set_state("walking")
                else:
                    emp.animation.set_state("idle")
                emp.animation.update(delta_time)

        # Win and progression check
        details, advanced, win = self.game_state.check_goals_and_progress()
        if win:
            # If still in Level 1 when win triggers here, switch to Level 2 (one-time)
            if getattr(self.game_state, "level", 1) == 1 and not self.win_mode:
                self.game_state.level = 2
                self.status_msg = "Level 1 complete! Level 2 unlocked."
                self.win_mode = False
            else:
                self.win_mode = True
                self.status_msg = details
        else:
            self.win_mode = False

    # ------------------------ 6. KEY PRESS LOGIC ---------------------------
    def on_key_press(self, symbol, modifiers):
        """
        Keyboard shortcuts:
          - ESC: quit
          - F5: save game
          - While an operation is selected:
              • Plant/Replace Crop: 1=🌽, 2=🌾, 3=🍆
              • Place/Replace Factory: S=Soil, W=Wood, M=Metal
        """
        if symbol == arcade.key.ESCAPE:
            arcade.close_window()

        if self.win_mode:
            return

        if symbol == arcade.key.F5:
            msg = self.game_state.save_game()
            self.status_msg = f"SAVED: {msg}"
        elif self.selected_operation >= 0:
            op = OPERATION_LIST[self.selected_operation]
            if op in ["Plant Crop", "Replace Crop"]:
                if symbol == arcade.key.KEY_1:
                    self.selected_crop = "corn"
                    self.status_msg = "Crop: Corn"
                elif symbol == arcade.key.KEY_2:
                    self.selected_crop = "wheat"
                    self.status_msg = "Crop: Wheat"
                elif symbol == arcade.key.KEY_3:
                    self.selected_crop = "eggplant"
                    self.status_msg = "Crop: Eggplant"
            elif op in ["Place Factory", "Replace Factory"]:
                if symbol == arcade.key.S:
                    self.selected_factory = "soil_factory"
                    self.status_msg = "Factory: Soil"
                elif symbol == arcade.key.W:
                    self.selected_factory = "wood_factory"
                    self.status_msg = "Factory: Wood"
                elif symbol == arcade.key.M:
                    self.selected_factory = "metal_factory"
                    self.status_msg = "Factory: Metal"

    # --------------------- 7. LEVEL INSTRUCTIONS & GOALS ---------------------
    def get_level_instructions(self):
        """
        Return instructional text for the right panel, based on current level.
        """
        level = getattr(self.game_state, "level", 1)
        if level == 1:
            return (
                "LEVEL 1\n"
                "- Select an operation, then click on a grid cell.\n"
                "- Plant crops in any empty cell on the grid.\n"
                "- Each crop gives food, water, and coins every 60s.\n"
                "- Meet the level goals below to unlock Level 2."
            )
        elif level == 2:
            return (
                "LEVEL 2\n"
                "- You can plant/replace crops and place/replace factories.\n"
                "- Upgrade all factories to Level 2 to boost production.\n"
                "- Achieve all goals below to win the game!"
            )
        return ""

    def get_level_goals(self):
        """
        Build the (goal, current-progress) tuples displayed in the right panel.
        Uses the 'advanced' dict returned by check_goals_and_progress().
        """
        details, advanced, win = self.game_state.check_goals_and_progress()
        level = getattr(self.game_state, "level", 1)
        if not isinstance(advanced, dict):
            advanced = {}

        if level == 1:
            return [
                ("Plant Crops", f"{advanced.get('crops', 0)} / 10"),
                ("Food required", f"{advanced.get('food', 0)} / 60"),
                ("Water required", f"{advanced.get('water', 0)} / 60"),
                ("Coins required", f"{advanced.get('coins', 0)} / 60"),
            ]
        elif level == 2:
            return [
                ("Soil Factories", f"{advanced.get('soil_factory', 0)} / 2"),
                ("Wood Factories", f"{advanced.get('wood_factory', 0)} / 2"),
                ("Metal Factories", f"{advanced.get('metal_factory', 0)} / 2"),
                ("Upgrade All Factories", "Level 2"),
                ("Food required", f"{advanced.get('food', 0)} / 120"),
                ("Water required", f"{advanced.get('water', 0)} / 120"),
                ("Coins required", f"{advanced.get('coins', 0)} / 120"),
            ]
        return []

# --------------------- 8. LAUNCH GAME WINDOW FUNCTION ---------------------
def launch_game_window(username, save_id=None):
    """
    Helper to show the GameWindow for a given user (and optional save id).
    """
    window = arcade.get_window()
    window.show_view(GameWindow(username, save_id=save_id))
