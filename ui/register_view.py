import arcade
from auth.register import register_user
from ui.theme import (
    BG_COLOR, PANEL_PADDING, PANEL_BG, PANEL_BORDER,
    HEADING_COLOR, VALUE_COLOR, LABEL_COLOR,
    BUTTON_BG, BUTTON_HOVER, BUTTON_TXT, BUTTON_RADIUS, BUTTON_BORDER,
    BTN_QUIT, BTN_COLOR, BTN_TEXT,
    FONT_MIN, FONT_MAX
)
from ui.login_view import LoginView  # <-- Needed for auto-switch

class RegisterView(arcade.View):
    def __init__(self):
        super().__init__()
        self.username = ""
        self.email = ""
        self.password = ""
        self.active_field = 0  # 0 = username, 1 = email, 2 = password
        self.error = ""
        self.success = False
        self.fields = ["Username", "Email", "Password"]

    def on_show_view(self):
        arcade.set_background_color(BG_COLOR)
        print("[DEBUG] Showing RegisterView")

    def on_draw(self):
        self.clear()
        w, h = self.window.width, self.window.height
        center_x = w // 2
        top_y = int(h * 0.80)
        field_spacing = int(h * 0.11)
        field_width = int(w * 0.40)
        field_height = int(h * 0.08)
        button_width = int(w * 0.24)
        button_height = int(h * 0.07)

        # Font sizes clamped for all screens
        title_font = max(FONT_MIN, min(FONT_MAX, int(h * 0.07)))
        label_font = max(FONT_MIN, min(FONT_MAX, int(h * 0.03)))
        val_font = max(FONT_MIN, min(FONT_MAX, int(h * 0.03)))
        btn_font = max(FONT_MIN, min(FONT_MAX, int(h * 0.037)))
        msg_font = max(FONT_MIN, min(FONT_MAX, int(h * 0.03)))

        # --- Title ---
        arcade.draw_text("Register", center_x, top_y, HEADING_COLOR, title_font, anchor_x="center", bold=True)

        # --- Fields ---
        for i, label in enumerate(self.fields):
            y = top_y - (i + 1) * field_spacing
            color = BTN_COLOR if self.active_field == i else PANEL_BG
            border = PANEL_BORDER

            # Field border
            arcade.draw_lrbt_rectangle_filled(
                center_x - field_width//2 - 4, center_x + field_width//2 + 4,
                y - field_height//2 - 4, y + field_height//2 + 4, border
            )
            # Field background
            arcade.draw_lrbt_rectangle_filled(
                center_x - field_width//2, center_x + field_width//2,
                y - field_height//2, y + field_height//2, color
            )
            # Label
            arcade.draw_text(label, center_x - field_width//2 + 18, y - field_height//4, LABEL_COLOR, label_font, anchor_x="left")
            # Value (hide password)
            val = getattr(self, label.lower()) if label != "Password" else "*" * len(self.password)
            arcade.draw_text(val, center_x - field_width//2 + 180, y - field_height//4, VALUE_COLOR, val_font, anchor_x="left")

        # --- Register Button ---
        y_btn = top_y - 4 * field_spacing
        arcade.draw_lrbt_rectangle_filled(
            center_x - button_width//2, center_x + button_width//2,
            y_btn - button_height//2, y_btn + button_height//2, BUTTON_BG
        )
        arcade.draw_lrbt_rectangle_outline(
            center_x - button_width//2, center_x + button_width//2,
            y_btn - button_height//2, y_btn + button_height//2, PANEL_BORDER, BUTTON_BORDER
        )
        arcade.draw_text("Register", center_x, y_btn - int(button_height * 0.17),
                         BUTTON_TXT, btn_font, anchor_x="center", bold=True)

        # --- Back Button ---
        y_back = y_btn - int(button_height * 1.3)
        back_w = int(button_width * 0.7)
        arcade.draw_lrbt_rectangle_filled(
            center_x - back_w//2, center_x + back_w//2,
            y_back - button_height//2, y_back + button_height//2, BTN_QUIT
        )
        arcade.draw_lrbt_rectangle_outline(
            center_x - back_w//2, center_x + back_w//2,
            y_back - button_height//2, y_back + button_height//2, PANEL_BORDER, BUTTON_BORDER
        )
        arcade.draw_text("Back", center_x, y_back - int(button_height * 0.17),
                         BTN_TEXT, label_font, anchor_x="center", bold=True)

        # --- Messages (error or success) ---
        y_msg = y_back - int(h * 0.06)
        if self.error:
            arcade.draw_text(self.error, center_x, y_msg, (255, 0, 0), msg_font, anchor_x="center")
        elif self.success:
            # Print success message two lines below
            arcade.draw_text(
                "Registration successful! Please login.",
                center_x,
                y_msg - 2 * (msg_font + 8),  # <<-- shift 2 lines below
                (34, 139, 34),
                msg_font,
                anchor_x="center"
            )

    def on_mouse_press(self, x, y, button, modifiers):
        w, h = self.window.width, self.window.height
        center_x = w // 2
        top_y = int(h * 0.80)
        field_spacing = int(h * 0.11)
        field_width = int(w * 0.40)
        field_height = int(h * 0.08)
        button_width = int(w * 0.24)
        button_height = int(h * 0.07)

        # Fields
        for i in range(3):
            field_y = top_y - (i + 1) * field_spacing
            if (center_x - field_width//2 < x < center_x + field_width//2) and \
               (field_y - field_height//2 < y < field_y + field_height//2):
                self.active_field = i
                print(f"[DEBUG] Selected field: {self.fields[i]}")
                return

        # Register Button
        y_btn = top_y - 4 * field_spacing
        if (center_x - button_width//2 < x < center_x + button_width//2) and \
           (y_btn - button_height//2 < y < y_btn + button_height//2):
            print("[DEBUG] Register button clicked.")
            self.try_register()
            return

        # Back Button
        y_back = y_btn - int(button_height * 1.3)
        back_w = int(button_width * 0.7)
        if (center_x - back_w//2 < x < center_x + back_w//2) and \
           (y_back - button_height//2 < y < y_back + button_height//2):
            print("[DEBUG] Back button clicked. Returning to menu.")
            from ui.menu_view import MenuView
            self.window.show_view(MenuView())

    def on_key_press(self, symbol, modifiers):
        if symbol in (arcade.key.TAB, arcade.key.DOWN):
            self.active_field = (self.active_field + 1) % 3
        elif symbol == arcade.key.UP:
            self.active_field = (self.active_field - 1) % 3
        elif symbol in (arcade.key.ENTER, arcade.key.RETURN):
            print("[DEBUG] Enter pressed, trying register.")
            self.try_register()
        elif symbol == arcade.key.ESCAPE:
            print("[DEBUG] Escape pressed, returning to menu.")
            from ui.menu_view import MenuView
            self.window.show_view(MenuView())

    def on_text(self, text):
        if self.success: return
        if self.active_field == 0:
            self.username += text
        elif self.active_field == 1:
            self.email += text
        elif self.active_field == 2:
            self.password += text

    def on_text_motion(self, motion):
        if motion == arcade.key.BACKSPACE:
            if self.active_field == 0 and self.username:
                self.username = self.username[:-1]
            elif self.active_field == 1 and self.email:
                self.email = self.email[:-1]
            elif self.active_field == 2 and self.password:
                self.password = self.password[:-1]

    def try_register(self):
        self.error = ""
        self.success = False
        print(f"[DEBUG] Attempting registration: {self.username}, {self.email}")
        if not (self.username and self.email and self.password):
            self.error = "All fields required."
            print("[DEBUG] Registration failed: fields missing.")
            return
        success, message = register_user(self.username, self.email, self.password)
        if success:
            self.success = True
            print("[DEBUG] Registration successful! Switching to LoginView...")

            # Delay for 1 second, then switch to LoginView
            def delayed_switch(dt):
                self.window.show_view(LoginView())
            arcade.schedule_once(delayed_switch, 1.0)
        else:
            self.error = message
            print(f"[DEBUG] Registration error: {message}")
