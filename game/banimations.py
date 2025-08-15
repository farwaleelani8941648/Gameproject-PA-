# game/banimations.py

import time

# --- Crop Growth Constants (number of image stages for each crop) ---
CROP_GROWTH_STAGES = {
    "corn": 20,
    "wheat": 7,
    "eggplant": 9,
}

CROP_GROWTH_SECONDS = 60  # How many seconds for a crop to fully grow

class CropAnimationState:
    """
    Manages the animation state (timer, stage, watered, harvest-ready) for a single crop cell.
    Used by backend only (no graphics!).
    Also tracks planted_time for frontend animation compatibility.
    """
    def __init__(self, crop_type):
        self.crop_type = crop_type
        self.growth_timer = 0.0          # Seconds since watered or last reset
        self.growth_stage = 0            # Current animation frame/stage (int)
        self.watered = False             # Has this crop been watered by an employee?
        self.needs_harvest = False       # Is the crop fully grown and waiting for harvest?
        self.planted_time = time.time()  # <-- Add this! Used by frontend animation

    def reset(self):
        """
        Reset the animation state after planting or harvesting.
        """
        self.growth_timer = 0.0
        self.growth_stage = 0
        self.watered = False
        self.needs_harvest = False
        self.planted_time = time.time()  # <-- Reset to current time

    def update(self, delta_time):
        """
        Progress crop growth by delta_time seconds.
        Returns True if the crop just became harvestable in this tick.
        """
        if self.needs_harvest:
            return False  # Already fully grown, waiting for harvest

        # Don't grow unless watered!
        if not self.watered:
            self.growth_stage = 0
            return False

        self.growth_timer += delta_time

        total_stages = CROP_GROWTH_STAGES.get(self.crop_type, 1)
        stage_length = CROP_GROWTH_SECONDS / total_stages

        # Calculate which stage we're on (1-based for visuals)
        self.growth_stage = min(int(self.growth_timer // stage_length) + 1, total_stages)

        if self.growth_stage >= total_stages:
            self.needs_harvest = True
            return True  # This tick: finished growing
        return False

    def water(self):
        """
        Called when an employee waters this crop.
        """
        self.watered = True

    def harvest(self):
        """
        Called after resources are collected; prepares for next growth cycle.
        """
        self.reset()
