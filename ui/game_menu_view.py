import arcade
from ui.theme import (
    BG_COLOR, BTN_COLOR, BTN_HOVER, BTN_TEXT, BTN_QUIT, TITLE_COLOR,
    PANEL_BORDER, FONT_MIN, FONT_MAX
)

class GameMenuView(arcade.View):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.buttons = ["New Game", "Saved Game", "Quit Game"]
        self.selected = -1

    def on_show_view(self):
        arcade.set_background_color(BG_COLOR)
        self.selected = -1

    def on_draw(self):
        self.clear()
        w, h = self.window.width, self.window.height
        center_x = w // 2

        # Responsive font sizes
        title_font = max(FONT_MIN, min(FONT_MAX, int(h * 0.062)))
        menu_font = max(FONT_MIN, min(FONT_MAX, int(h * 0.047)))
        btn_font = max(FONT_MIN, min(FONT_MAX, int(h * 0.051)))
        select_font = max(FONT_MIN, min(FONT_MAX, int(h * 0.032)))

        # --- Titles ---
        arcade.draw_text(f"Welcome, {self.username}!", center_x, int(h * 0.81), TITLE_COLOR, title_font, anchor_x="center", bold=True)
        arcade.draw_text("Main Menu", center_x, int(h * 0.72), TITLE_COLOR, menu_font, anchor_x="center", bold=True)

        # --- Button layout ---
        btn_width = int(w * 0.36)
        btn_height = int(h * 0.12)
        spacing = int(h * 0.05)
        top_y = int(h * 0.53)

        for i, text in enumerate(self.buttons):
            y = top_y - i * (btn_height + spacing)
            # Quit button is red, others are themed
            color = BTN_QUIT if text == "Quit Game" else (BTN_HOVER if self.selected == i else BTN_COLOR)
            shadow_color = (100, 149, 237, 60)

            # Shadow (behind main button)
            arcade.draw_lrbt_rectangle_filled(
                center_x - btn_width // 2 + 7, center_x + btn_width // 2 + 7,
                y - btn_height // 2 - 7, y + btn_height // 2 - 7,
                shadow_color)
            # Main button
            arcade.draw_lrbt_rectangle_filled(
                center_x - btn_width // 2, center_x + btn_width // 2,
                y - btn_height // 2, y + btn_height // 2, color)
            # Outline
            arcade.draw_lrbt_rectangle_outline(
                center_x - btn_width // 2, center_x + btn_width // 2,
                y - btn_height // 2, y + btn_height // 2, PANEL_BORDER, 3)
            # Text
            arcade.draw_text(text, center_x, y - btn_height // 7,
                             BTN_TEXT, btn_font, anchor_x="center", bold=True)


    def on_mouse_motion(self, x, y, dx, dy):
        self.selected = -1
        w, h = self.window.width, self.window.height
        center_x = w // 2
        btn_width = int(w * 0.36)
        btn_height = int(h * 0.12)
        spacing = int(h * 0.05)
        top_y = int(h * 0.53)
        for i in range(len(self.buttons)):
            y = top_y - i * (btn_height + spacing)
            if (center_x - btn_width // 2 < x < center_x + btn_width // 2 and
                y - btn_height // 2 < y < y + btn_height // 2):
                self.selected = i

    def on_mouse_press(self, x, y, button, modifiers):
        w, h = self.window.width, self.window.height
        center_x = w // 2
        btn_width = int(w * 0.36)
        btn_height = int(h * 0.12)
        spacing = int(h * 0.05)
        top_y = int(h * 0.53)
        clicked = -1
        for i in range(len(self.buttons)):
            y_btn = top_y - i * (btn_height + spacing)
            if (center_x - btn_width // 2 < x < center_x + btn_width // 2 and
                y_btn - btn_height // 2 < y < y_btn + btn_height // 2):
                clicked = i

        self.selected = clicked

        if self.selected == 0:  # New Game
            from ui.game_window import GameWindow
            self.window.show_view(GameWindow(self.username))
        elif self.selected == 1:  # Saved Game
            from ui.saves_view import SavesView
            self.window.show_view(SavesView(self.username))
        elif self.selected == 2:  # Quit Game
            arcade.close_window()

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.ESCAPE:
            arcade.close_window()