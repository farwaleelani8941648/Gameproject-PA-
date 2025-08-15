# ui/theme.py

# --------- COLORS ---------
BG_COLOR      = (232, 232, 240, 255)
WOOD_LIGHT    = (220, 184, 135, 255)
WOOD_DARK     = (191, 142, 77, 255)
WOOD_OUTLINE  = (110, 76, 33, 255)
PANEL_BG      = (255, 248, 235, 255)
PANEL_BORDER  = (180, 150, 110)
HEADING_COLOR = (80, 55, 18)
LABEL_COLOR   = (120, 92, 55)
VALUE_COLOR   = (70, 49, 18)
OP_SELECTED   = (133, 207, 80)
OP_LOCKED     = (210, 210, 210)
HOVER_COLOR   = (255, 233, 157, 200)
BUTTON_BG     = (200, 150, 90, 255)
BUTTON_HOVER  = (170, 110, 60, 255)
BUTTON_TXT    = (70, 49, 18)
TITLE_COLOR   = (34, 87, 44)
BUTTON_BORDER = 3

# --------- BUTTONS (Menus etc) ---------
BTN_QUIT   = (255, 89, 89)
BTN_COLOR  = (91, 227, 128)
BTN_HOVER  = (67, 187, 98)
BTN_TEXT   = (255, 255, 255)

# --------- LAYOUT ---------
PANEL_PADDING         = 24           # Panel padding (px)
GRID_MIN_SIDE         = 680          # Minimum grid side, for large grid
LEFT_PANEL_WIDTH_PX   = 180          # Left panel width (px)
RIGHT_PANEL_WIDTH_PX  = 220          # Right panel width (px)
BOTTOM_PANEL_HEIGHT   = 62           # Bottom panel height (px)
BORDER_WIDTH          = 3
BUTTON_RADIUS         = 12

# --------- FONT SIZES ---------
FONT_MIN        = 14
FONT_MAX        = 44
FONT_HEADING    = 32
FONT_PANEL_HEAD = 22
FONT_PANEL_LABEL= 18
FONT_PANEL_VALUE= 20
FONT_OP_PANEL   = 22
FONT_RESOURCE   = 22

def clamp_font_size(window_height, ratio=0.03):
    """
    Responsive font size utility.
    """
    size = int(window_height * ratio)
    return max(FONT_MIN, min(FONT_MAX, size))
