# game/employees.py

import time

class Employee:
    """
    Represents an employee (worker/cat) in the game.
    Handles movement, animation state, assigned crop, and job progress.
    Designed for cell-by-cell walking and sprite animations.
    """

    def __init__(self, employee_id=None, position=None, working=False):
        self.employee_id = employee_id  # Unique integer for each employee
        self.position = position if position is not None else (7, 0)  # Start at hub (row, col)
        self.working = working          # True if busy; False if idle in hub
        self.target_crop = None         # (row, col) position of assigned crop

        # --- Animation & movement state ---
        self.active = False             # True = moving or working, False = idle at hub
        self.harvesting = False         # True = currently harvesting
        self.moving_home = False        # True = returning to hub (after harvesting)
        self.direction = "down"         # For sprite sheet: "up", "down", "left", "right"
        self.path = []                  # List of (row, col) to follow next (for BFS path)
        self.anim_frame = 0             # Sprite animation frame
        self.anim_time = 0              # Animation frame timer (seconds)
        self.target = None              # Next destination (row, col): crop or hub
        self.state = "idle"             # "idle", "walking_to_crop", "harvesting", "returning_home"

        # --- New attributes for your requirements ---
        self.visible = False            # Employees start invisible at hub (idle state)
        self.placed_time = None         # Timestamp when activated/assigned
        self.can_harvest = False        # Will become True after 30s
        self.move_delay = 0.15          # Slow down speed (seconds between steps) – you can tune this
        self.last_move_time = 0         # For movement timing

    def activate(self, crop_pos):
        """
        Called when player selects and assigns this employee to a crop.
        """
        self.active = True
        self.working = True
        self.target_crop = crop_pos
        self.state = "walking_to_crop"
        self.visible = True
        self.placed_time = time.time()
        self.can_harvest = False

    def update_harvest_permission(self):
        """
        Called each frame/update loop: updates permission to harvest after 30 seconds.
        """
        if self.placed_time and not self.can_harvest:
            if time.time() - self.placed_time >= 30:
                self.can_harvest = True

    def reset(self):
        """
        Return employee to hub and idle state, invisible until next activation.
        """
        self.position = (7, 0)    # or your fixed hub position
        self.active = False
        self.working = False
        self.target_crop = None
        self.harvesting = False
        self.moving_home = False
        self.direction = "down"
        self.path = []
        self.anim_frame = 0
        self.anim_time = 0
        self.target = None
        self.state = "idle"
        self.visible = False
        self.placed_time = None
        self.can_harvest = False
        self.last_move_time = 0

    def can_start_harvest(self):
        """
        Returns True if 30s has passed since activation, else False.
        """
        return self.can_harvest

    def should_draw(self):
        """
        Returns True if employee is visible (activated), else False.
        Used by drawing code to control transparency.
        """
        return self.visible

    def __repr__(self):
        loc = f"at {self.position}" if self.position else "in hub"
        if self.state == "walking_to_crop":
            state = "walking"
        elif self.state == "harvesting":
            state = "harvesting"
        elif self.state == "returning_home":
            state = "returning"
        else:
            state = "idle"
        return f"<Employee {self.employee_id if self.employee_id is not None else ''} {state} {loc}>"
