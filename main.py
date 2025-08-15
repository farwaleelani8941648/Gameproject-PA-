# main.py

import arcade

def main():
    # -----------------------------------------------------------------
    # 1. CONFIGURE WINDOW SIZE & SETTINGS
    # -----------------------------------------------------------------
    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 720
    MIN_WIDTH = 900
    MIN_HEIGHT = 600
    TITLE = "Farming Empire"

    # -----------------------------------------------------------------
    # 2. CREATE THE MAIN WINDOW (Resizable)
    # -----------------------------------------------------------------
    window = arcade.Window(
        width=SCREEN_WIDTH,
        height=SCREEN_HEIGHT,
        title=TITLE,
        resizable=True
    )
    window.set_minimum_size(MIN_WIDTH, MIN_HEIGHT)

    # (Optional) Try to maximize the window for best UX
    try:
        window.maximize()
    except Exception:
        pass  # Ignore if not supported (Linux, some systems)

    # -----------------------------------------------------------------
    # 3. SHOW MAIN MENU (OR LOGIN SCREEN)
    # -----------------------------------------------------------------
    try:
        from ui.menu_view import MenuView  # Lazy import to avoid cyclic issues
        menu_view = MenuView()
        window.show_view(menu_view)
    except Exception as e:
        print("[ERROR] Failed to load MenuView:", e)
        arcade.close_window()
        return

    # -----------------------------------------------------------------
    # 4. START THE GAME LOOP
    # -----------------------------------------------------------------
    arcade.run()

if __name__ == "__main__":
    main()
