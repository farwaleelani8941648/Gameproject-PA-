# game/cell.py

class Cell:
    """
    Represents a cell on the game grid.
    Each cell can be empty, a crop, or a factory.
    Includes a 'being_harvested' flag to prevent double-assignment to employees.
    """
    def __init__(self, cell_type="empty", level=0):
        self.cell_type = cell_type    # Example: "empty", "corn", "soil_factory"
        self.level = level            # Crop/factory upgrade level (int)
        self.being_harvested = False  # True if this crop is assigned to an employee

    def reset(self):
        """
        Reset this cell to be empty and not being harvested.
        Call this when crop/factory is removed or harvested.
        """
        self.cell_type = "empty"
        self.level = 0
        self.being_harvested = False
