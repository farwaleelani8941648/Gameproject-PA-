# game/crops.py

# List of valid crop types used in the game
CROP_TYPES = ["corn", "wheat", "eggplant"]

class CropCell:
    """
    Represents a crop cell (optional for future use).
    Can be extended with animations, growth stages, etc.
    """
    def __init__(self, crop_type="corn", level=1):
        if crop_type not in CROP_TYPES:
            raise ValueError(f"Invalid crop type: {crop_type}")
        self.cell_type = crop_type
        self.level = level

    def __repr__(self):
        return f"<CropCell type={self.cell_type} level={self.level}>"