
import os

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Output directory
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

# Ensure output directory exists
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Application Settings
APP_TITLE = "HTML Smuggling & Phishing Tool"
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 700

# Theme Settings
THEME_DARK = {
    "Window": (30, 30, 30),
    "WindowText": (255, 255, 255),
    "Base": (25, 25, 25),
    "AlternateBase": (53, 53, 53),
    "ToolTipBase": (255, 255, 255),
    "ToolTipText": (255, 255, 255),
    "Text": (255, 255, 255),
    "Button": (45, 45, 45),
    "ButtonText": (255, 255, 255),
    "BrightText": (255, 0, 0),
    "Link": (42, 130, 218),
    "Highlight": (42, 130, 218),
    "HighlightedText": (0, 0, 0),
}
