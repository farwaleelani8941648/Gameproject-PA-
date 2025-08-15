# ui/icons.py

import arcade
import os

# ---- HOME ICON (PNG or Emoji Fallback) ----
HOME_ICON_PATH = os.path.join("assets", "icons", "home.png")
if os.path.exists(HOME_ICON_PATH):
    home_icon_texture = arcade.load_texture(HOME_ICON_PATH)
    home_icon_fallback = None
    print(f"[ICON] Loaded home icon from: {HOME_ICON_PATH}")
else:
    home_icon_texture = None
    home_icon_fallback = "🏠"
    print("[ICON] Home icon PNG not found, will use emoji fallback.")

# ---- CROP ICONS (emoji, could be swapped for PNG later) ----
crop_icons = {
    "corn": "🌽",
    "wheat": "🌾",
    "eggplant": "🍆"
}

# ---- FACTORY ICONS (emoji, could be swapped for PNG later) ----
factory_icons = {
    "soil_factory": "🟫",
    "wood_factory": "🌲",
    "metal_factory": "🛠️"
}
