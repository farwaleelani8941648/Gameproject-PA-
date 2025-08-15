import arcade
import sqlite3
import os
import json
from ui.theme import (
    BG_COLOR, BTN_COLOR, BTN_HOVER, BTN_TEXT, BTN_QUIT, TITLE_COLOR,
    PANEL_BG, PANEL_BORDER, BUTTON_BORDER, FONT_MIN, FONT_MAX
)

DB_PATH = os.path.join(os.path.dirname(__file__), "../database/game_data.db")

class SavesView(arcade.View):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.saves = []
        self.selected_index = None
        self.error = ""

    def on_show_view(self):
        arcade.set_background_color(BG_COLOR)
        self.saves = self.load_saves()
        self.selected_index = None
        self.error = ""

    def on_draw(self):
        self.clear()
        w, h = self.window.width, self.window.height
        center_x = w // 2

        # ---- Title ----
        title_font = max(FONT_MIN, min(FONT_MAX, int(h * 0.06)))
        arcade.draw_text(f"Saved Games for {self.username}",
                         center_x, int(h * 0.83), TITLE_COLOR, title_font,
                         anchor_x="center", bold=True)

        # ---- Saves List ----
        list_top = int(h * 0.70)
        row_h = int(h * 0.10)
        box_width = int(w * 0.68)
        box_height = int(h * 0.08)
        info_font = max(FONT_MIN, int(h * 0.032))

        if not self.saves:
            arcade.draw_text("No saved games found.",
                             center_x, list_top - row_h,
                             (220, 70, 70), info_font, anchor_x="center")
        else:
            for idx, save in enumerate(self.saves):
                y = list_top - idx * (row_h + 6)
                bg_color = BTN_HOVER if self.selected_index == idx else PANEL_BG
                # Row background
                arcade.draw_lrbt_rectangle_filled(
                    center_x - box_width//2, center_x + box_width//2,
                    y - box_height//2, y + box_height//2, bg_color
                )
                arcade.draw_lrbt_rectangle_outline(
                    center_x - box_width//2, center_x + box_width//2,
                    y - box_height//2, y + box_height//2, PANEL_BORDER, 2
                )
                # Info string: Save Slot + Level + Date
                date_str = save.get("date", "Unknown Date")
                info = f"Slot {idx+1} | Level: {save['level']} | Date: {date_str}"
                arcade.draw_text(info, center_x, y - int(box_height * 0.13),
                                 (35, 45, 60), info_font, anchor_x="center")

        # ---- Load Game button ----
        y_load = int(h * 0.18)
        btn_width = int(w * 0.25)
        btn_height = int(h * 0.08)
        btn_font = max(FONT_MIN, int(h * 0.035))
        if self.selected_index is not None and self.saves:
            arcade.draw_lrbt_rectangle_filled(
                center_x - btn_width//2, center_x + btn_width//2,
                y_load - btn_height//2, y_load + btn_height//2, BTN_COLOR
            )
            arcade.draw_lrbt_rectangle_outline(
                center_x - btn_width//2, center_x + btn_width//2,
                y_load - btn_height//2, y_load + btn_height//2, PANEL_BORDER, BUTTON_BORDER
            )
            arcade.draw_text("Load Game", center_x, y_load - btn_height // 6,
                             BTN_TEXT, btn_font, anchor_x="center", bold=True)

        # ---- Back button ----
        y_back = int(h * 0.08)
        btn2_width = int(w * 0.14)
        btn2_height = int(h * 0.065)
        arcade.draw_lrbt_rectangle_filled(
            center_x - btn2_width//2, center_x + btn2_width//2,
            y_back - btn2_height//2, y_back + btn2_height//2, BTN_QUIT)
        arcade.draw_lrbt_rectangle_outline(
            center_x - btn2_width//2, center_x + btn2_width//2,
            y_back - btn2_height//2, y_back + btn2_height//2, PANEL_BORDER, BUTTON_BORDER)
        arcade.draw_text("Back", center_x, y_back - btn2_height // 7,
                         BTN_TEXT, btn_font, anchor_x="center", bold=True)

        # ---- Error message ----
        if self.error:
            arcade.draw_text(self.error, center_x, y_back - int(h * 0.06), (255, 0, 0), btn_font, anchor_x="center")

    def on_mouse_press(self, x, y, button, modifiers):
        w, h = self.window.width, self.window.height
        center_x = w // 2

        # ---- Back button ----
        btn2_width = int(w * 0.14)
        btn2_height = int(h * 0.065)
        y_back = int(h * 0.08)
        if (center_x - btn2_width//2 < x < center_x + btn2_width//2 and
            y_back - btn2_height//2 < y < y_back + btn2_height//2):
            from ui.game_menu_view import GameMenuView
            self.window.show_view(GameMenuView(self.username))
            return

        # ---- Load Game button ----
        btn_width = int(w * 0.25)
        btn_height = int(h * 0.08)
        y_load = int(h * 0.18)
        if (self.selected_index is not None and self.saves and
            center_x - btn_width//2 < x < center_x + btn_width//2 and
            y_load - btn_height//2 < y < y_load + btn_height//2):
            selected_save_id = self.saves[self.selected_index]['id']
            try:
                from ui.game_window import GameWindow
                self.window.show_view(GameWindow(self.username, save_id=selected_save_id))
            except Exception as e:
                self.error = f"Error loading game: {e}"
            return

        # ---- Click a save row ----
        list_top = int(h * 0.70)
        row_h = int(h * 0.10)
        box_width = int(w * 0.68)
        box_height = int(h * 0.08)
        for idx, save in enumerate(self.saves):
            y_row = list_top - idx * (row_h + 6)
            if (center_x - box_width//2 < x < center_x + box_width//2 and
                y_row - box_height//2 < y < y_row + box_height//2):
                self.selected_index = idx
                break

    def load_saves(self):
        """
        Loads all saved games for the user, most recent first.
        Returns a list of dicts (id, level, date).
        """
        saves = []
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            # Make sure your saves table has: id (PK), level, save_time (or saved_at), username, etc.
            c.execute('SELECT id, level, save_time FROM saves WHERE username=? ORDER BY save_time DESC', (self.username,))
            rows = c.fetchall()
            for row in rows:
                saves.append({
                    "id": row[0],
                    "level": row[1],
                    "date": row[2]
                })
            conn.close()
        except Exception as e:
            self.error = f"DB Error: {e}"
        return saves