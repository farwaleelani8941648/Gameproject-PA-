"""
Game State (backend logic for farming game)

This file holds:
- Helpers for crop animation timing and employee animation state
- The GameState class (grid, resources, employees, goals, persistence)
- Factory helper functions for creating/loading a game state

IMPORTANT: Logic is unchanged. Only formatting and comments were added.
"""

import os
import json
import sqlite3
import time
from collections import deque

from game.resources import ResourceManager
from game.cell import Cell
from game.crops import CROP_TYPES
from game.factories import FACTORY_TYPES
from game.employees import Employee
from ui.animations import attach_employee_animation

# ================================================================
#    HELPERS FOR ANIMATION STATE AND INITIALIZATION
# ================================================================

def ensure_crop_plant_times(grid):
    """
    Ensure every crop cell has a planted timestamp.
    This lets the animation know when the crop started growing.
    If a cell is a crop but has no time, we set a default (now - 30s)
    so it already looks partly grown instead of empty.
    """
    now = time.time()
    for row in grid:
        for cell in row:
            if cell.cell_type in CROP_TYPES:
                if not hasattr(cell, "just_planted_at") or not cell.just_planted_at:
                    # Start slightly in the past so first frames are skipped
                    cell.just_planted_at = now - 30
                cell.planted_time = cell.just_planted_at


def set_employee_animation_action(emp):
    """
    Pick the correct animation for an employee based on their current state.
    Priority:
      - harvesting → beat_right
      - active or moving_home → walking (by direction)
      - otherwise → idle
    """
    if getattr(emp, "harvesting", False):
        emp.animation.set_action("beat_right")
    elif getattr(emp, "active", False) or getattr(emp, "moving_home", False):
        if getattr(emp, "direction", None) == "up":
            emp.animation.set_action("move_up")
        elif getattr(emp, "direction", None) == "down":
            emp.animation.set_action("move_down")
        elif getattr(emp, "direction", None) == "left":
            emp.animation.set_action("move_left")
        elif getattr(emp, "direction", None) == "right":
            emp.animation.set_action("move_right")
        else:
            # Default walk cycle if direction not set yet
            emp.animation.set_action("move_down")
    else:
        emp.animation.set_action("idle")


# ================================================================
#                MAIN GAME STATE CLASS
# ================================================================

class GameState:
    """
    Main game logic and state container.
    Handles:
      - grid (cells with crops/factories/empty)
      - resources (food, water, coins, employees)
      - employees (activation, pathfinding, harvesting)
      - goals and level progression
      - saving/loading to SQLite
    """

    # ---------------------------------------------------------------
    #                INITIALIZATION
    # ---------------------------------------------------------------
    def __init__(self, username, grid_size=16):
        self.username = username
        self.GRID_SIZE = grid_size

        # Create an empty grid of Cells (GRID_SIZE x GRID_SIZE)
        self.grid = [[Cell() for _ in range(self.GRID_SIZE)] for _ in range(self.GRID_SIZE)]

        # Player resources and level tracking
        self.resources = ResourceManager()
        self.level = 1
        self.level1_start = {
            "food": self.resources.food,
            "water": self.resources.water,
            "coins": self.resources.coins
        }
        self.level2_start = None

        # Factory stats (for achievements/progression)
        self.factories_placed = 0
        self.factories_replaced = 0

        # Employees (start with count from ResourceManager)
        self.employees = []
        for i in range(self.resources.employees):
            emp = Employee(employee_id=i, position=(0, 0), working=False)
            attach_employee_animation(emp)
            self.employees.append(emp)
        self.active_employee = None  # Index of employee the player just activated

        # Make sure crop cells have a planted_time for animation
        ensure_crop_plant_times(self.grid)

    # ---------------------------------------------------------------
    #            ANIMATION: CROP FULLY GROWN CHECK
    # ---------------------------------------------------------------
    def is_crop_fully_grown(self, cell):
        """
        Returns True if a crop cell is at the last animation frame (fully grown).
        We compute the current frame from planted_time and compare to final frame.
        """
        from ui.animations import load_crop_frames  # lazy import to avoid cycles
        if cell.cell_type not in CROP_TYPES:
            return False

        textures = load_crop_frames(cell.cell_type)
        total_frames = len(textures)
        if total_frames == 0:
            return False

        planted_time = getattr(cell, "planted_time", 0)
        grow_time = max(0, time.time() - planted_time)

        # Each frame lasts (50 / total_frames) seconds
        frame_duration = 50 / total_frames if total_frames > 0 else 1
        frame_idx = min(int(grow_time / frame_duration), total_frames - 1)
        return frame_idx == (total_frames - 1)

    # ---------------------------------------------------------------
    #     EMPLOYEE ACTIVATION & ASSIGNMENT (HARVESTING)
    # ---------------------------------------------------------------
    def activate_employee(self, employee_idx):
        """
        Make an employee 'active' so the next click on a mature crop assigns them.
        """
        if 0 <= employee_idx < len(self.employees):
            emp = self.employees[employee_idx]
            if not emp.working and not emp.active:
                self.active_employee = employee_idx
                emp.visible = True
                return True, f"Employee {employee_idx+1} activated! Click a mature crop to assign."
            else:
                return False, "That employee is already working!"
        return False, "Invalid employee selected."

    def assign_employee_to_crop(self, row, col):
        """
        Assign the currently active employee to harvest a specific crop cell.
        Checks:
          - active employee exists
          - target is in-bounds
          - cell is a mature crop (fully grown, not already being harvested)
        Sets path using BFS and adjusts animation.
        """
        if self.active_employee is None:
            return False, "No employee is currently active."

        if not (0 <= row < self.GRID_SIZE and 0 <= col < self.GRID_SIZE):
            return False, "Invalid crop position."

        cell = self.grid[row][col]
        emp = self.employees[self.active_employee]

        if cell.cell_type in CROP_TYPES and not cell.being_harvested and cell.level >= 1:
            # Require fully grown before assigning
            if not self.is_crop_fully_grown(cell):
                return False, "Crop is not fully grown yet!"

            # Lock the crop for harvesting
            cell.being_harvested = True

            # Prepare employee state and path
            emp.target = (row, col)
            emp.active = True
            emp.working = True
            emp.harvesting = False
            emp.moving_home = False
            emp.placed_time = time.time()
            emp.can_harvest = False
            emp.visible = True
            emp.state = "walking_to_crop"

            # Path to the crop (grid BFS)
            emp.path = self.bfs_path(emp.position, (row, col))

            # Set initial direction if we have a path
            if emp.path and len(emp.path) > 1:
                next_row, next_col = emp.path[1]
                cur_row, cur_col = emp.path[0]
                if next_row > cur_row:
                    emp.direction = "down"
                elif next_row < cur_row:
                    emp.direction = "up"
                elif next_col > cur_col:
                    emp.direction = "right"
                elif next_col < cur_col:
                    emp.direction = "left"

            set_employee_animation_action(emp)
            self.active_employee = None
            return True, f"Employee assigned to harvest crop at ({row+1},{col+1})"

        elif cell.being_harvested:
            return False, "This crop is already being harvested!"
        else:
            return False, "Select a mature, ready-to-harvest crop."

    # ---------------------------------------------------------------
    #          EMPLOYEE ANIMATION AND PATHFINDING
    # ---------------------------------------------------------------
    def update_employees(self, dt):
        """
        Move employees along their paths, handle harvesting animation/timing,
        and send them back home after finishing. Also hides idle employees.
        """
        EMPLOYEE_MOVE_INTERVAL = 0.30  # seconds between movement steps

        for emp in self.employees:

            # Hide employees when idle (not active/working/harvesting/moving)
            if not emp.active and not emp.working and not emp.harvesting and not emp.moving_home:
                emp.visible = False
                set_employee_animation_action(emp)
                continue

            # If walking to target or going home, tick their move timer
            if emp.active or emp.moving_home:
                emp.anim_time += dt

                # ---- Walking to crop ----
                if emp.active and emp.path and not emp.harvesting:
                    if emp.anim_time >= EMPLOYEE_MOVE_INTERVAL:
                        next_step = emp.path.pop(0)
                        emp.position = next_step
                        emp.anim_time = 0

                        # Update direction for correct walking animation
                        if emp.path:
                            next_row, next_col = emp.path[0]
                            cur_row, cur_col = emp.position
                            if next_row > cur_row:
                                emp.direction = "down"
                            elif next_row < cur_row:
                                emp.direction = "up"
                            elif next_col > cur_col:
                                emp.direction = "right"
                            elif next_col < cur_col:
                                emp.direction = "left"

                        set_employee_animation_action(emp)

                        # Reached crop: check if we can start harvesting
                        if emp.position == emp.target:
                            row, col = emp.position
                            cell = self.grid[row][col]
                            emp.last_crop_type = cell.cell_type
                            emp.can_harvest = self.is_crop_fully_grown(cell)

                            if emp.can_harvest:
                                emp.harvesting = True
                                emp.anim_time = 0
                                set_employee_animation_action(emp)
                                continue
                            else:
                                # Arrived too early (not fully grown)
                                emp.harvesting = False
                                emp.anim_time = 0

                # ---- Harvesting ----
                if emp.harvesting:
                    set_employee_animation_action(emp)
                    HARVEST_DURATION = 0.7  # seconds to finish harvesting

                    if emp.anim_time >= HARVEST_DURATION:
                        row, col = emp.position
                        cell = self.grid[row][col]

                        # Release crop and reset its growth visually/logically
                        cell.being_harvested = False
                        cell.cell_type = getattr(emp, 'last_crop_type', cell.cell_type)
                        cell.level = 0
                        cell.just_planted_at = time.time()
                        cell.planted_time = cell.just_planted_at
                        cell.harvest_invisible_until = time.time() + 2  # brief fade

                        # Employee goes home after harvest
                        emp.harvesting = False
                        emp.working = False
                        emp.active = False
                        emp.moving_home = True
                        emp.target = (0, 0)
                        emp.path = self.bfs_path(emp.position, (0, 0))
                        emp.anim_time = 0
                        set_employee_animation_action(emp)
                        continue

                # ---- Arrived at target but not harvesting (recheck) ----
                if emp.active and emp.position == emp.target and not emp.harvesting:
                    row, col = emp.position
                    cell = self.grid[row][col]
                    emp.can_harvest = self.is_crop_fully_grown(cell)
                    if emp.can_harvest:
                        emp.harvesting = True
                        emp.anim_time = 0
                        set_employee_animation_action(emp)

                # ---- Walking home ----
                if emp.moving_home and emp.path:
                    if emp.anim_time >= EMPLOYEE_MOVE_INTERVAL:
                        next_step = emp.path.pop(0)
                        emp.position = next_step
                        emp.anim_time = 0

                        # Update direction while going home
                        if emp.path:
                            next_row, next_col = emp.path[0]
                            cur_row, cur_col = emp.position
                            if next_row > cur_row:
                                emp.direction = "down"
                            elif next_row < cur_row:
                                emp.direction = "up"
                            elif next_col > cur_col:
                                emp.direction = "right"
                            elif next_col < cur_col:
                                emp.direction = "left"

                        set_employee_animation_action(emp)

                        # Hide when reached home base (0, 0)
                        if emp.position == (0, 0):
                            emp.moving_home = False
                            emp.target = None
                            emp.path = []
                            emp.active = False
                            emp.working = False
                            emp.harvesting = False
                            emp.state = "idle"
                            emp.visible = False
                            set_employee_animation_action(emp)

    # ---------------------------------------------------------------
    #        EMPLOYEE SHORTEST PATHFINDING (BFS)
    # ---------------------------------------------------------------
    def bfs_path(self, start, goal):
        """
        Breadth-First Search (BFS) for a 4-directional grid.
        Returns a list of (row, col) positions from start to goal (inclusive),
        or [] if no path exists.
        Walkable rule: empty cells are walkable; goal is always allowed.
        """
        if start == goal:
            return [start]

        rows, cols = self.GRID_SIZE, self.GRID_SIZE
        visited = [[False] * cols for _ in range(rows)]
        parent = [[None] * cols for _ in range(rows)]

        q = deque()
        q.append(start)
        visited[start[0]][start[1]] = True

        # Up, Down, Left, Right
        dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        while q:
            r, c = q.popleft()
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols:
                    # Allow stepping into 'empty' or the goal cell
                    walkable = self.grid[nr][nc].cell_type in ["empty"] or (nr, nc) == goal
                    if walkable and not visited[nr][nc]:
                        visited[nr][nc] = True
                        parent[nr][nc] = (r, c)

                        if (nr, nc) == goal:
                            # Reconstruct path from goal to start
                            path = []
                            cur = goal
                            while cur != start:
                                path.append(cur)
                                cur = parent[cur[0]][cur[1]]
                            path.append(start)
                            path.reverse()
                            return path

                        q.append((nr, nc))

        return []

    # ---------------------------------------------------------------
    #                CROP MANAGEMENT FUNCTIONS
    # ---------------------------------------------------------------
    def can_plant_crop(self, row, col, crop_type="corn"):
        """
        Quick check before planting:
        - valid crop
        - cell is empty
        - enough resources (2 of each)
        """
        cell = self.grid[row][col]
        return (
            crop_type in CROP_TYPES and
            cell.cell_type == "empty" and
            self.resources.food >= 2 and
            self.resources.water >= 2 and
            self.resources.coins >= 2
        )

    def plant_crop(self, row, col, crop_type="corn"):
        """
        Plant a crop on an empty cell, spending 2 food/water/coins.
        Sets the animation start times so it begins growing immediately.
        """
        if crop_type not in CROP_TYPES:
            return False, "Invalid crop type."

        cell = self.grid[row][col]
        if cell.cell_type == "empty":
            if self.resources.spend(food=2, water=2, coins=2):
                cell.cell_type = crop_type
                cell.level = 1
                cell.just_planted_at = time.time()
                cell.planted_time = cell.just_planted_at
                return True, f"{crop_type.title()} planted."
            else:
                return False, "Not enough resources to plant crop."
        else:
            return False, "Cell is not empty."

    def replace_crop(self, row, col, crop_type=None):
        """
        Remove an existing crop by paying a small cost (1 of each).
        Leaves the cell empty so a new crop can be planted.
        """
        REPLACE_COST = 1
        cell = self.grid[row][col]
        if cell.cell_type in CROP_TYPES:
            if self.resources.spend(food=REPLACE_COST, water=REPLACE_COST, coins=REPLACE_COST):
                cell.cell_type = "empty"
                cell.level = 0
                cell.being_harvested = False
                cell.just_planted_at = None
                cell.planted_time = None
                return True, "Crop removed. You can now plant a new crop here."
            else:
                return False, "Not enough resources to remove crop."
        else:
            return False, "Can only remove an existing crop."

    def grow_crops(self):
        """
        No forced growth here.
        The animation uses planted_time to decide the current frame.
        Keep this if you plan multi-level growth logic in the future.
        """
        # No need to forcibly regrow crops; animation will show correct stage using planted_time!
        # This function can be empty or only used if you implement multi-level crops in future.
        pass

    # ---------------------------------------------------------------
    #                FACTORY MANAGEMENT FUNCTIONS
    # ---------------------------------------------------------------
    def can_place_factory(self, row, col, factory_type):
        """
        Check if a factory can be placed:
        - Only in Level 2
        - Valid factory type
        - Empty cell
        - Enough resources (5 of each)
        """
        cell = self.grid[row][col]
        return (
            self.level == 2 and
            factory_type in FACTORY_TYPES and
            cell.cell_type == "empty" and
            self.resources.food >= 5 and
            self.resources.water >= 5 and
            self.resources.coins >= 5
        )

    def place_factory(self, row, col, factory_type):
        """
        Public method to place a factory.
        Blocks at Level 1 with a friendly message.
        """
        if self.level != 2:
            return False, "Factories can only be placed in Level 2."
        return self._place_factory(row, col, factory_type)

    def _place_factory(self, row, col, factory_type):
        """
        Internal placement logic:
        - Spend cost
        - Set cell to factory
        - Every 2 factories → add 1 employee (and attach animation)
        """
        cell = self.grid[row][col]
        if cell.cell_type == "empty":
            if self.resources.spend(food=5, water=5, coins=5):
                cell.cell_type = factory_type
                cell.level = 1
                self.factories_placed += 1

                # Reward: every 2 factories → +1 employee
                if self.factories_placed % 2 == 0:
                    self.resources.add_employee(1)
                    new_id = len(self.employees)
                    emp = Employee(employee_id=new_id, position=(0, 0), working=False)
                    attach_employee_animation(emp)
                    self.employees.append(emp)

                return True, f"{factory_type.replace('_',' ').title()} placed."
            else:
                return False, "Not enough resources to place factory."
        else:
            return False, "Cell is not empty."

    def replace_factory(self, row, col):
        """
        Remove an existing factory:
        - Refund 3 of each resource
        - Track replacements
        - Every 2 removed factories → remove 1 employee (if exists)
        """
        cell = self.grid[row][col]
        if cell.cell_type in FACTORY_TYPES:
            self.resources.earn(food=3, water=3, coins=3)
            cell.cell_type = "empty"
            cell.level = 0
            self.factories_replaced += 1

            # Penalty: every 2 removals → -1 employee
            if self.factories_replaced % 2 == 0 and self.resources.employees > 0:
                self.resources.remove_employee(1)
                if len(self.employees) > 0:
                    self.employees.pop()

            return True, "Factory removed (resources rewarded, cell empty)."
        else:
            return False, "Can only remove an existing factory."

    def upgrade(self, row, col, max_level=2):
        """
        Upgrade a factory (Level 2 requirement):
        - Costs: 10 * current level (of each resource)
        - Stops at max_level (default: 2)
        """
        if self.level != 2:
            return False, "Upgrades are only allowed in Level 2."

        cell = self.grid[row][col]
        if cell.cell_type in FACTORY_TYPES and cell.level < max_level:
            upgrade_cost = 10 * cell.level
            if self.resources.spend(food=upgrade_cost, water=upgrade_cost, coins=upgrade_cost):
                cell.level += 1
                return True, f"{cell.cell_type.replace('_',' ').title()} upgraded to level {cell.level}."
            else:
                return False, "Not enough resources to upgrade."
        elif cell.level >= max_level:
            return False, f"Already max level ({max_level})."
        else:
            return False, "No factory to upgrade here."

    # ---------------------------------------------------------------
    #              GOALS, PROGRESS, AND AUTO-HARVEST
    # ---------------------------------------------------------------
    def count_crop_types(self):
        """
        Count how many crops of each type exist and total crops.
        Returns: (dict_of_counts, total_count)
        """
        counts = {c: 0 for c in CROP_TYPES}
        total = 0
        for row in self.grid:
            for cell in row:
                if cell.cell_type in CROP_TYPES:
                    counts[cell.cell_type] += 1
                    total += 1
        return counts, total

    def count_factories(self):
        """
        Count how many factories of each type exist.
        Returns: dict_of_counts
        """
        counts = {f: 0 for f in FACTORY_TYPES}
        for row in self.grid:
            for cell in row:
                if cell.cell_type in FACTORY_TYPES:
                    counts[cell.cell_type] += 1
        return counts

    def all_factories_upgraded(self):
        """
        Check if every existing factory is upgraded to level 2.
        """
        for row in self.grid:
            for cell in row:
                if cell.cell_type in FACTORY_TYPES and cell.level < 2:
                    return False
        return True

    def _earned_since(self, resource, since):
        """
        Helper: how much of a resource has been gained since a snapshot dict.
        """
        return max(0, getattr(self.resources, resource) - since[resource])

    def check_goals_and_progress(self):
        """
        Level 1 goals:
          - Plant 10 crops
          - Earn 60 food, 60 water, 60 coins (during Level 1)

        Level 2 goals:
          - Place 2 soil, 2 wood, 2 metal factories
          - Upgrade all factories to level 2
          - Earn 120 food, 120 water, 120 coins (during Level 2)

        Returns:
          (message, progress_dict, is_game_won_bool)
        """
        # -------------------------
        # Level 1 progress
        # -------------------------
        if self.level == 1:
            crop_counts, crop_total = self.count_crop_types()
            earned = {
                "food": self._earned_since("food", self.level1_start),
                "water": self._earned_since("water", self.level1_start),
                "coins": self._earned_since("coins", self.level1_start),
            }
            progress = {
                "crops": crop_total,
                "food": earned["food"],
                "water": earned["water"],
                "coins": earned["coins"]
            }

            if crop_total >= 10 and earned["food"] >= 60 and earned["water"] >= 60 and earned["coins"] >= 60:
                self.level = 2
                self.level2_start = {
                    "food": self.resources.food,
                    "water": self.resources.water,
                    "coins": self.resources.coins
                }
                return "Level 2 unlocked! You can now place and upgrade factories.", progress, False
            else:
                details = (
                    f"Level 1: Plant 10 crops (Current: {crop_total}/10), "
                    f"Earn 60 food/water/coins in Level 1 "
                    f"(Current: {earned['food']}/{earned['water']}/{earned['coins']})"
                )
                return details, progress, False

        # -------------------------
        # Level 2 progress
        # -------------------------
        elif self.level == 2:
            factory_counts = self.count_factories()
            all_factories = all(v >= 2 for v in factory_counts.values())
            all_upgraded = self.all_factories_upgraded()

            earned = {
                "food": self._earned_since("food", self.level2_start),
                "water": self._earned_since("water", self.level2_start),
                "coins": self._earned_since("coins", self.level2_start),
            }
            progress = {
                "soil_factory": factory_counts["soil_factory"],
                "wood_factory": factory_counts["wood_factory"],
                "metal_factory": factory_counts["metal_factory"],
                "food": earned["food"],
                "water": earned["water"],
                "coins": earned["coins"]
            }

            if all_factories and all_upgraded and earned["food"] >= 120 and earned["water"] >= 120 and earned["coins"] >= 120:
                return "Congratulations! You win!", progress, True
            else:
                details = (
                    f"Level 2: Place 2 each of soil/wood/metal factories "
                    f"(Soil:{factory_counts['soil_factory']}/2, Wood:{factory_counts['wood_factory']}/2, "
                    f"Metal:{factory_counts['metal_factory']}/2), "
                    f"Upgrade all factories to at least Level 2, "
                    f"Earn 120 food/water/coins in Level 2 (Current: "
                    f"{earned['food']}/{earned['water']}/{earned['coins']})"
                )
                return details, progress, False

    def harvest_and_produce(self):
        """
        Auto-harvest:
          - For each crop/factory, add resources (3 * level for each type).
          - For crops: reset planted_time so the animation restarts from seed.
          - Leaves a short invisible period for a smoother visual reset.
        Returns a summary string of earned resources.
        """
        total_food = 0
        total_water = 0
        total_coins = 0

        for row in self.grid:
            for cell in row:
                # Reward resources for both crops and factories
                if cell.cell_type in (CROP_TYPES + FACTORY_TYPES):
                    bonus = 3 * cell.level
                    total_food += bonus
                    total_water += bonus
                    total_coins += bonus

                # Reset crop growth visually/logically
                if cell.cell_type in CROP_TYPES:
                    cell.just_planted_at = time.time()
                    cell.planted_time = cell.just_planted_at
                    cell.level = 1
                    cell.being_harvested = False
                    cell.harvest_invisible_until = time.time() + 2

        self.resources.earn(food=total_food, water=total_water, coins=total_coins)
        return f"Auto-harvest: +{total_food} food, +{total_water} water, +{total_coins} coins"

    def get_resource_summary(self):
        """
        Simple one-line string to show current resources and total employees.
        """
        r = self.resources
        return f"Food: {r.food}  Water: {r.water}  Coins: {r.coins}  Employees: {r.employees}"

    # ---------------------------------------------------------------
    #            SAVE / LOAD GAME STATE TO/FROM SQLITE
    # ---------------------------------------------------------------
    def save_game(self):
        """
        Save the current game snapshot to SQLite.
        We store:
          - level
          - resources (food/water/coins/employees)
          - grid (cell types + levels)
          - level start snapshots for goal tracking
        """
        DB_PATH = os.path.join(os.path.dirname(__file__), '../database/game_data.db')

        data = {
            "level": self.level,
            "resources": {
                "food": self.resources.food,
                "water": self.resources.water,
                "coins": self.resources.coins,
                "employees": self.resources.employees
            },
            "grid": [
                [
                    {"cell_type": cell.cell_type, "level": cell.level}
                    for cell in row
                ] for row in self.grid
            ],
            "level1_start": self.level1_start,
            "level2_start": self.level2_start
        }

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            '''
            INSERT INTO saves (username, level, resources, grid, level1_start, level2_start)
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (
                self.username,
                self.level,
                json.dumps(data["resources"]),
                json.dumps(data["grid"]),
                json.dumps(self.level1_start),
                json.dumps(self.level2_start) if self.level2_start else json.dumps({})
            )
        )
        conn.commit()
        conn.close()
        return "Game saved!"

    @staticmethod
    def list_saves_for_user(username):
        """
        Return a list of (id, save_time) for a user's saves, newest first.
        """
        DB_PATH = os.path.join(os.path.dirname(__file__), '../database/game_data.db')
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id, save_time FROM saves WHERE username=? ORDER BY save_time DESC', (username,))
        saves = c.fetchall()
        conn.close()
        return saves

    def load_game(self, save_id):
        """
        Load a saved game by its database id.
        Restores:
          - level, resources, grid
          - level start snapshots
          - employee list and animations
        """
        DB_PATH = os.path.join(os.path.dirname(__file__), '../database/game_data.db')
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT level, resources, grid, level1_start, level2_start FROM saves WHERE id=?', (save_id,))
        row = c.fetchone()
        conn.close()

        if row:
            # Basic fields
            self.level = row[0]

            # Resources
            resources = json.loads(row[1])
            self.resources.food = resources["food"]
            self.resources.water = resources["water"]
            self.resources.coins = resources["coins"]
            self.resources.employees = resources.get("employees", 2)

            # Grid
            grid_data = json.loads(row[2])
            for r in range(self.GRID_SIZE):
                for c in range(self.GRID_SIZE):
                    data = grid_data[r][c]
                    self.grid[r][c].cell_type = data["cell_type"]
                    self.grid[r][c].level = data["level"]

            # Ensure animation timers exist for crops
            ensure_crop_plant_times(self.grid)

            # Goal snapshots
            self.level1_start = json.loads(row[3]) if row[3] else {"food": 50, "water": 50, "coins": 50}
            self.level2_start = json.loads(row[4]) if row[4] else None

            # Rebuild employees (and attach animations)
            self.employees = []
            for i in range(self.resources.employees):
                emp = Employee(employee_id=i, position=(0, 0), working=False)
                attach_employee_animation(emp)
                self.employees.append(emp)

            self.active_employee = None
            return "Game loaded!"
        else:
            return "No saved game found."


# ================================================================
#           FACTORY FUNCTIONS FOR UI / GAME LAUNCH
# ================================================================

def get_new_game_state(username, grid_size=16):
    """
    Create a fresh GameState and make sure crops have animation times set.
    """
    state = GameState(username, grid_size)
    ensure_crop_plant_times(state.grid)
    return state


def load_game_state_from_save(username, save_data, grid_size=16):
    """
    Create a GameState object from a preloaded save_data dict.
    This mirrors load_game() but uses already-parsed data.
    """
    state = GameState(username, grid_size)

    # Level and resources
    state.level = save_data["level"]
    resources = save_data["resources"]
    state.resources.food = resources["food"]
    state.resources.water = resources["water"]
    state.resources.coins = resources["coins"]
    state.resources.employees = resources.get("employees", 2)

    # Grid
    grid_data = save_data["grid"]
    for r in range(state.GRID_SIZE):
        for c in range(state.GRID_SIZE):
            data = grid_data[r][c]
            state.grid[r][c].cell_type = data["cell_type"]
            state.grid[r][c].level = data["level"]

    # Animation timers for crops
    ensure_crop_plant_times(state.grid)

    # Goal snapshots
    state.level1_start = save_data.get("level1_start", {"food": 50, "water": 50, "coins": 50})
    state.level2_start = save_data.get("level2_start", None)

    # Employees (attach animations)
    state.employees = []
    for i in range(state.resources.employees):
        emp = Employee(employee_id=i, position=(0, 0), working=False)
        attach_employee_animation(emp)
        state.employees.append(emp)

    state.active_employee = None
    return state
