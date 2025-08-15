# ui/game_ui_utils.py

from ui.theme import PANEL_PADDING

OPERATION_LIST = [
    "Plant Crop",
    "Replace Crop",
    "Place Factory",
    "Replace Factory",
    "Upgrade Factory"
]

# The minimum level required to unlock each operation (index matches OPERATION_LIST)
OPERATION_REQUIRE_LEVEL = [1, 1, 2, 2, 2]

# Main game grid size (change if you want a bigger/smaller board)
GRID_SIZE = 8

def get_rect_grid_metrics(window_width, window_height, grid_width=800, grid_height=500):
    """
    Returns (grid_x, grid_y, grid_width, grid_height) for a fixed-size grid,
    centered in the window with space for side panels and top resource bar.
    """
    pad = PANEL_PADDING
    left_w = int(window_width * 0.18)
    right_w = int(window_width * 0.12)
    total_grid_width = grid_width
    total_grid_height = grid_height

    # Center grid horizontally between left panel and right goals panel
    grid_x = left_w + (window_width - left_w - right_w - total_grid_width) // 2
    # Center grid vertically (after making space for top resource panel)
    grid_y = (window_height - total_grid_height) // 2

    return grid_x, grid_y, total_grid_width, total_grid_height

def get_resources(resource_mgr):
    """
    Returns a dict for the resource panel display.
    Expects a ResourceManager or similar object with .food, .water, .coins, .employees attributes.
    """
    return {
        "Food": resource_mgr.food,
        "Water": resource_mgr.water,
        "Coins": resource_mgr.coins,
        "Employees": resource_mgr.employees
    }

def get_crops_and_factories(game_state):
    """
    Returns two lists of tuples: (name, count) for crops and factories,
    ready to display in the two-column crops/factories panel.
    """
    crops, _ = game_state.count_crop_types()
    factories = game_state.count_factories()
    crops_list = [
        ("Corn", crops.get("corn", 0)),
        ("Wheat", crops.get("wheat", 0)),
        ("Eggplant", crops.get("eggplant", 0))
    ]
    factories_list = [
        ("Soil", factories.get("soil_factory", 0)),
        ("Wood", factories.get("wood_factory", 0)),
        ("Metal", factories.get("metal_factory", 0))
    ]
    return crops_list, factories_list