## WebScraper Pro - Main Entry Point
## Commercial-grade Web Scraping Application

import sys
import os

# Ensure the application directory is in the path
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    application_path = sys._MEIPASS
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, application_path)


def main():
    import customtkinter as ctk
    from ui.main_window import MainWindow
    from ui.styles import theme, apply_custom_styles

    # Apply theme
    theme.set_dark()
    apply_custom_styles()

    # Create and run the application
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
