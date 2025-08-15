"""
drawing_helpers.py — Centralized helper functions for drawing all game UI elements.

Handles:
    - Drawing textures and sprites
    - Resource bars and panels
    - Goals/instructions panels
    - Operation selection bar
    - Wooden game grid with crops/factories
    - Animated crop rendering

IMPORTANT: Only formatting and comments were added. All game logic remains unchanged.
"""

import arcade
import time
from ui.animations import get_crop_animation_frame


# ================================================================
#    UNIVERSAL TEXTURE DRAWING
# ================================================================
def draw_texture_with_sprite(pixel_x, pixel_y, width, height, texture, alpha=255):
    """
    Draw a texture (PNG, animated crop, factory) at pixel coordinates with a specific size and transparency.
    
    This uses a temporary SpriteList to ensure compatibility with Arcade 3.3.2.
    It avoids direct draw_texture_rectangle() calls, making it more flexible.

    Args:
        pixel_x, pixel_y (float): Center position on screen.
        width, height (float): Draw size in pixels.
        texture (arcade.Texture): The image to draw.
        alpha (int): Transparency (0 = invisible, 255 = fully opaque).
    """
    if texture is None:
        return

    sprite = arcade.Sprite()
    sprite.texture = texture
    sprite.center_x = pixel_x
    sprite.center_y = pixel_y

    # Scale sprite to desired size
    if texture.width > 0:
        sprite.scale = width / texture.width
    else:
        sprite.scale = 1.0

    sprite.alpha = alpha

    # Draw via temp list (Arcade 3.3.2-safe)
    temp_list = arcade.SpriteList()
    temp_list.append(sprite)
    temp_list.draw()


# ================================================================
#    TOP RESOURCE PANEL (Food, Water, Coins, Employees)
# ================================================================
def draw_resource_panel(
    x, y, width, height, resources,
    bg_color, border_color, heading_color, label_color, value_color
):
    """
    Draws a horizontal resource bar with Food, Water, Coins, and Employees.

    Args:
        resources (dict): Keys: "Food", "Water", "Coins", "Employees".
    """
    # Background shadow and base
    arcade.draw_lrbt_rectangle_filled(
        x + 5, x + width + 5, y - 5, y + height + 5, (210, 210, 210, 60)
    )
    arcade.draw_lrbt_rectangle_filled(x, x + width, y, y + height, bg_color)
    arcade.draw_lrbt_rectangle_outline(x, x + width, y, y + height, border_color, 4)

    # Layout
    n = 4
    col_w = width / n
    labels = ["Food", "Water", "Coins", "Employees"]
    font_label = 20
    font_value = 21
    label_y_offset = 13
    value_gap = 20

    # Vertical dividers
    for i in range(1, n):
        x_pos = x + i * col_w
        arcade.draw_line(x_pos, y, x_pos, y + height, border_color, 2)

    # Labels and values
    for i, label in enumerate(labels):
        cell_left = x + i * col_w
        cell_right = cell_left + col_w
        cx = (cell_left + cell_right) / 2

        # Heading
        label_y = y + height - label_y_offset
        arcade.draw_text(
            label, cx, label_y, heading_color, font_label,
            anchor_x="center", anchor_y="top", bold=True
        )

        # Value
        value_y = label_y - value_gap
        value = str(resources.get(label, 0))
        arcade.draw_text(
            value, cx, value_y, value_color, font_value,
            anchor_x="center", anchor_y="top", bold=True
        )


# ================================================================
#    LEFT TWO-COLUMN PANEL (Crops & Factories)
# ================================================================
def draw_two_column_panel(
    x, y, width, height,
    left_title, left_items, right_title, right_items,
    bg_color, border_color, heading_color, value_color
):
    """
    Draw a panel split into two columns (e.g., Crops and Factories).

    Args:
        left_items, right_items: Lists of (name, value) pairs.
    """
    # Background and outline
    arcade.draw_lrbt_rectangle_filled(x + 6, x + width + 6, y - 6, y + height + 6, (210, 210, 210, 44))
    arcade.draw_lrbt_rectangle_filled(x, x + width, y, y + height, bg_color)
    arcade.draw_lrbt_rectangle_outline(x, x + width, y, y + height, border_color, 3)

    col_w = width / 2
    row_h = height / 4
    heading_font = min(max(15, int(row_h * 0.43)), 23)

    # Column titles
    arcade.draw_text(left_title, x + col_w / 2, y + height - row_h / 2, heading_color, heading_font,
                     anchor_x="center", anchor_y="center", bold=True)
    arcade.draw_text(right_title, x + col_w + col_w / 2, y + height - row_h / 2, heading_color, heading_font,
                     anchor_x="center", anchor_y="center", bold=True)

    # Vertical separator
    arcade.draw_line(x + col_w, y, x + col_w, y + height, border_color, 2)

    # Horizontal row lines
    for i in range(1, 4):
        y_sep = y + height - i * row_h
        arcade.draw_line(x, y_sep, x + width, y_sep, border_color, 1)

    # Pad item lists to 4 rows
    left_items = left_items + [("", "")] * (4 - len(left_items))
    right_items = right_items + [("", "")] * (4 - len(right_items))
    value_font = min(max(14, int(row_h * 0.36)), 19)

    # Draw each row
    for i in range(4):
        row_y = y + height - row_h * (i + 1.5)
        # Left column
        arcade.draw_text(left_items[i][0], x + 16, row_y, heading_color, value_font,
                         anchor_x="left", anchor_y="center", bold=True)
        arcade.draw_text(str(left_items[i][1]), x + col_w - 16, row_y, value_color, value_font,
                         anchor_x="right", anchor_y="center", bold=True)
        # Right column
        arcade.draw_text(right_items[i][0], x + col_w + 16, row_y, heading_color, value_font,
                         anchor_x="left", anchor_y="center", bold=True)
        arcade.draw_text(str(right_items[i][1]), x + width - 16, row_y, value_color, value_font,
                         anchor_x="right", anchor_y="center", bold=True)


# ================================================================
#    GENERIC INFO PANEL
# ================================================================
def draw_panel(
    x, y, width, height, n_sections, headings,
    values=None, title=None, vertical=False,
    bg_color=None, border_color=None, heading_color=None, value_color=None
):
    """
    Draw a generic info panel, split into n_sections horizontally or vertically.
    Can optionally display a title.

    Args:
        vertical (bool): True for vertical sections, False for horizontal.
    """
    # Background
    arcade.draw_lrbt_rectangle_filled(
        x + 5, x + width + 5, y - 5, y + height + 5, (210, 210, 210, 80)
    )
    arcade.draw_lrbt_rectangle_filled(x, x + width, y, y + height, bg_color)
    arcade.draw_lrbt_rectangle_outline(x, x + width, y, y + height, border_color, 4)

    coords = []
    if vertical:
        # Vertical division
        section_h = height / n_sections
        for i in range(n_sections):
            top = y + height - i * section_h
            bottom = top - section_h
            arcade.draw_lrbt_rectangle_outline(x, x + width, bottom, top, border_color, 2)
            coords.append((x + width / 2, (top + bottom) / 2))
        heading_font = max(14, int(section_h * 0.35))
        value_font = max(12, int(section_h * 0.28))
    else:
        # Horizontal division
        section_w = width / n_sections
        for i in range(n_sections):
            left = x + i * section_w
            right = left + section_w
            arcade.draw_lrbt_rectangle_outline(left, right, y, y + height, border_color, 2)
            coords.append(((left + right) / 2, y + height / 2))
        heading_font = max(14, min(int(height * 0.62), int(section_w * 0.5), 30))
        value_font = max(12, min(int(height * 0.44), int(section_w * 0.43), 23))

    # Headings
    for i, head in enumerate(headings):
        if i >= len(coords):
            break
        cx, cy = coords[i]
        if head:
            arcade.draw_text(
                str(head), cx, cy + (28 if vertical else 22),
                heading_color, heading_font, anchor_x="center", anchor_y="center", bold=True
            )

    # Values
    if values:
        for i, val in enumerate(values):
            if i >= len(coords):
                break
            if val is not None and val != "":
                cx, cy = coords[i]
                arcade.draw_text(
                    str(val), cx, cy - (16 if vertical else 15),
                    value_color, value_font, anchor_x="center", anchor_y="center", bold=True
                )

    # Title (only for horizontal mode)
    if title and not vertical:
        arcade.draw_text(
            title, x + width // 2, y + height - 10,
            heading_color, heading_font + 6, anchor_x="center", anchor_y="top", bold=True
        )


# ================================================================
#    GOALS / INSTRUCTIONS PANEL
# ================================================================
def draw_goals_panel(
    x, y, width, height, get_level_instructions, get_level_goals,
    bg_color=None, border_color=None, heading_color=None, label_color=None, value_color=None
):
    """
    Draws the right-side panel showing level instructions and goals.

    Args:
        get_level_instructions (func): Returns instruction string.
        get_level_goals (func): Returns list of (goal, value) tuples.
    """
    height = min(height, 1000)
    arcade.draw_lrbt_rectangle_filled(x + 8, x + width + 8, y - 8, y + height + 8, (210, 210, 210, 55))

    # Space allocation
    max_instr_h = 330
    max_goals_h = 300
    total_needed = max_instr_h + max_goals_h
    if height < total_needed:
        scale = height / total_needed
        instr_h = int(max_instr_h * scale)
        goals_h = int(max_goals_h * scale)
    else:
        instr_h = max_instr_h
        goals_h = max_goals_h

    pad_x = 22
    pad_y = 35
    instr_top = y + height
    instr_bot = instr_top - instr_h
    goals_top = instr_bot
    goals_bot = goals_top - goals_h

    # Instructions box
    arcade.draw_lrbt_rectangle_filled(x, x + width, instr_bot, instr_top, bg_color)
    arcade.draw_lrbt_rectangle_outline(x, x + width, instr_bot, instr_top, border_color, 4)
    arcade.draw_text("Instructions", x + width // 2, instr_top - pad_y, heading_color, 25,
                     anchor_x="center", bold=True)
    arcade.draw_text(get_level_instructions(), x + pad_x, instr_top - pad_y - 32,
                     label_color, 17, anchor_x="left", anchor_y="top",
                     width=width - 2 * pad_x, multiline=True)

    # Goals box
    arcade.draw_lrbt_rectangle_filled(x, x + width, goals_bot, goals_top, bg_color)
    arcade.draw_lrbt_rectangle_outline(x, x + width, goals_bot, goals_top, border_color, 4)
    arcade.draw_text("Level Goals", x + width // 2, goals_top - pad_y, heading_color, 22,
                     anchor_x="center", bold=True)
    goals = get_level_goals()
    row_h = 38
    row_gap = 12
    start_y = goals_top - pad_y - 32

    for i, (goal, val) in enumerate(goals):
        box_top = start_y - i * (row_h + row_gap)
        box_bot = box_top - row_h
        box_left = x + 18
        box_right = x + width - 18
        if box_bot < goals_bot + 10:
            break
        arcade.draw_lrbt_rectangle_outline(box_left, box_right, box_bot, box_top, border_color, 2)
        arcade.draw_text(goal, box_left + 12, box_top - 9, label_color, 17,
                         anchor_x="left", anchor_y="top", bold=True)
        arcade.draw_text(val, box_right - 12, box_top - 9, value_color, 17,
                         anchor_x="right", anchor_y="top", bold=True)


# ================================================================
#    OPERATION PANEL (Below Grid)
# ================================================================
def draw_operation_panel(
    x, y, width, height, headings, selected_idx, locked_idx,
    bg_color, border_color, heading_color, value_color, op_selected, op_locked
):
    """
    Draws the bottom operation bar where players choose actions.

    Args:
        selected_idx (int): Index of currently selected operation.
        locked_idx (list[int]): Indices of locked operations.
    """
    n_sections = len(headings)
    section_w = width / n_sections

    for i, heading in enumerate(headings):
        left = x + i * section_w
        right = left + section_w
        top = y + height
        bottom = y

        # Shadow
        arcade.draw_lrbt_rectangle_filled(left + 3, right + 3, bottom - 3, top + 3, (210, 210, 210, 42))

        # Fill color based on state
        if i == selected_idx:
            color = op_selected
        elif i in locked_idx:
            color = op_locked
        else:
            color = bg_color

        # Panel background
        arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, color)
        arcade.draw_lrbt_rectangle_outline(left, right, bottom, top, border_color, 2)

        # Label text
        txt_color = (140, 140, 140) if i in locked_idx else heading_color
        txt = heading + (" 🔒" if i in locked_idx else "")
        font_size = min(max(14, int(height * 0.32)), 22)
        arcade.draw_text(txt, (left + right) / 2, y + height / 2, txt_color, font_size,
                         anchor_x="center", anchor_y="center", bold=True)


# ================================================================
#    MAIN WOODEN GAME GRID
# ================================================================
def draw_wooden_grid(
    grid_x, grid_y, grid_width, grid_height, grid_size, grid, grid_hover, selected_operation,
    OPERATION_LIST, crop_icons, factory_icons,
    wood_dark, wood_light, hover_color, border_color, value_color
):
    """
    Draws the central game grid with wooden tiles, crops, and factories.
    Supports:
        - Hover highlights
        - Animated crops (drawn smaller and right-aligned in cell)
        - Hiding icons during replacement or after harvest
    """
    cell_w = grid_width / grid_size
    cell_h = grid_height / grid_size
    icon_font = int(min(cell_w, cell_h) * 0.56)

    for row in range(grid_size):
        for col in range(grid_size):
            x = grid_x + col * cell_w
            y = grid_y + row * cell_h
            is_dark = (row + col) % 2 == 0
            color = wood_dark if is_dark else wood_light

            cell = grid[row][col]
            hide_icon = False

            # Hide icon for Replace operation on hovered cell
            if selected_operation >= 0:
                op = OPERATION_LIST[selected_operation]
                if (row, col) == grid_hover:
                    if op == "Replace Crop" and cell.cell_type in crop_icons:
                        hide_icon = True
                    if op == "Replace Factory" and cell.cell_type in factory_icons:
                        hide_icon = True

            # Hide just-harvested crops for 2 seconds
            if cell.cell_type in crop_icons:
                if hasattr(cell, "harvest_invisible_until") and cell.harvest_invisible_until > time.time():
                    hide_icon = True

            # Highlight hovered cell
            if (row, col) == grid_hover:
                color = hover_color

            # Draw cell background
            arcade.draw_lrbt_rectangle_filled(x, x + cell_w, y, y + cell_h, color)
            arcade.draw_lrbt_rectangle_outline(x, x + cell_w, y, y + cell_h, border_color, 3)

            # Draw animated crop (right-center, smaller)
            if not hide_icon and cell.cell_type in ("corn", "wheat", "eggplant"):
                tex = get_crop_animation_frame(cell, cell.cell_type, cell_grow_duration=50)
                if tex:
                    crop_draw_width = cell_w * 0.44
                    crop_draw_height = cell_h * 0.44
                    crop_center_x = x + cell_w * 0.72
                    crop_center_y = y + cell_h / 2
                    draw_texture_with_sprite(crop_center_x, crop_center_y, crop_draw_width, crop_draw_height, tex)
                else:
                    # Fallback: emoji icon
                    icon = crop_icons.get(cell.cell_type, "")
                    if icon:
                        arcade.draw_text(icon, x + cell_w // 2, y + cell_h // 2, value_color, icon_font,
                                         anchor_x="center", anchor_y="center")
            elif not hide_icon:
                icon = ""
                if cell.cell_type in factory_icons:
                    icon = factory_icons[cell.cell_type]
                if icon:
                    arcade.draw_text(icon, x + cell_w // 2, y + cell_h // 2, value_color, icon_font,
                                     anchor_x="center", anchor_y="center")

            # Level number for crops/factories
            if cell.cell_type != "empty" and not hide_icon:
                arcade.draw_text(str(cell.level), x + cell_w - 22, y + 14, (100, 78, 35), 16, bold=True)
