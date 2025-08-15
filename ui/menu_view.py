import arcade
from ui.theme import (
    BG_COLOR, BTN_COLOR, BTN_HOVER, BTN_TEXT, BTN_QUIT, TITLE_COLOR,
    PANEL_BORDER, BUTTON_BORDER, FONT_MIN, FONT_MAX
)

class MenuView(arcade.View):
    def __init__(self):
        super().__init__()
        self.selected = -1
        self.buttons = ["Register", "Login", "Quit"]

    def on_show_view(self):
        arcade.set_background_color(BG_COLOR)
        self.selected = -1

    def on_draw(self):
        self.clear()
        w, h = self.window.width, self.window.height
        center_x = w // 2

        # ---- Title with Shadow ----
        title_font_size = max(FONT_MIN, min(FONT_MAX, int(h * 0.13)))
        arcade.draw_text("Farming Empire", center_x, int(h * 0.75), TITLE_COLOR,
                         title_font_size, anchor_x="center", bold=True)

        # ---- Main Buttons ----
        btn_width = int(w * 0.36)
        btn_height = int(h * 0.11)
        spacing = int(h * 0.05)
        top_y = int(h * 0.56)
        btn_font = max(FONT_MIN, min(FONT_MAX, int(h * 0.051)))

        for i, text in enumerate(self.buttons):
            y = top_y - i * (btn_height + spacing)
            # Theme color: quit button red, others hover/normal
            color = BTN_HOVER if self.selected == i else (BTN_COLOR if text != "Quit" else BTN_QUIT)
            shadow_color = (80, 130, 210, 45)
            # Shadow
            arcade.draw_lrbt_rectangle_filled(
                center_x - btn_width // 2 + 7, center_x + btn_width // 2 + 7,
                y - btn_height // 2 - 7, y + btn_height // 2 - 7, shadow_color)
            # Main button
            arcade.draw_lrbt_rectangle_filled(
                center_x - btn_width // 2, center_x + btn_width // 2,
                y - btn_height // 2, y + btn_height // 2, color)
            # Border
            arcade.draw_lrbt_rectangle_outline(
                center_x - btn_width // 2, center_x + btn_width // 2,
                y - btn_height // 2, y + btn_height // 2, PANEL_BORDER, BUTTON_BORDER)
            # Button Text
            arcade.draw_text(text, center_x, y - btn_height // 7, BTN_TEXT, btn_font,
                             anchor_x="center", bold=True)

    def on_mouse_motion(self, x, y, dx, dy):
        self.selected = -1
        w, h = self.window.width, self.window.height
        center_x = w // 2
        btn_width = int(w * 0.36)
        btn_height = int(h * 0.11)
        spacing = int(h * 0.05)
        top_y = int(h * 0.56)
        for i in range(len(self.buttons)):
            y = top_y - i * (btn_height + spacing)
            if (center_x - btn_width // 2 < x < center_x + btn_width // 2 and
                y - btn_height // 2 < y < y + btn_height // 2):
                self.selected = i

    def on_mouse_press(self, x, y, button, modifiers):
        w, h = self.window.width, self.window.height
        center_x = w // 2
        btn_width = int(w * 0.36)
        btn_height = int(h * 0.11)
        spacing = int(h * 0.05)
        top_y = int(h * 0.56)
        clicked = -1
        for i in range(len(self.buttons)):
            y_btn = top_y - i * (btn_height + spacing)
            if (center_x - btn_width // 2 < x < center_x + btn_width // 2 and
                y_btn - btn_height // 2 < y < y_btn + btn_height // 2):
                clicked = i

        print(f"[DEBUG] Menu pressed: {clicked}")
        try:
            if clicked == 0:
                print("[DEBUG] Trying to open RegisterView")
                from ui.register_view import RegisterView
                self.window.show_view(RegisterView())
            elif clicked == 1:
                print("[DEBUG] Trying to open LoginView")
                from ui.login_view import LoginView
                self.window.show_view(LoginView())
            elif clicked == 2:
                print("[DEBUG] Quitting from main menu.")
                arcade.close_window()
        except Exception as e:
            print("[ERROR] Menu action failed:", e)

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.ESCAPE:
            arcade.close_window()
