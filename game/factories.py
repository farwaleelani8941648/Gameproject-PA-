# game/factories.py

# List of valid factory types in the game
FACTORY_TYPES = ["soil_factory", "wood_factory", "metal_factory"]

class FactoryCell:
    """
    Represents a factory cell (optional for future extension).
    Extend this class for animation, upgrades, or advanced logic.
    """
    def __init__(self, factory_type="soil_factory", level=1):
        if factory_type not in FACTORY_TYPES:
            raise ValueError(f"Invalid factory type: {factory_type}")
        self.cell_type = factory_type
        self.level = level

    def __repr__(self):
        return f"<FactoryCell type={self.cell_type} level={self.level}>"