from PySide2.QtGui import QPalette, QColor
from PySide2.QtCore import Qt
from config import THEME_DARK

class Theme:
    @staticmethod
    def apply_dark_theme(app_or_window):
        # Apply Palette (Fallback for some controls)
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(26, 26, 46)) # #1a1a2e
        palette.setColor(QPalette.WindowText, QColor(224, 224, 224)) # #e0e0e0
        palette.setColor(QPalette.Base, QColor(22, 33, 62)) # #16213e
        palette.setColor(QPalette.AlternateBase, QColor(15, 52, 96)) # #0f3460
        palette.setColor(QPalette.ToolTipBase, QColor(15, 52, 96))
        palette.setColor(QPalette.ToolTipText, QColor(224, 224, 224))
        palette.setColor(QPalette.Text, QColor(224, 224, 224))
        palette.setColor(QPalette.Button, QColor(15, 52, 96))
        palette.setColor(QPalette.ButtonText, QColor(224, 224, 224))
        palette.setColor(QPalette.BrightText, QColor(233, 69, 96)) # #e94560
        palette.setColor(QPalette.Link, QColor(233, 69, 96))
        palette.setColor(QPalette.Highlight, QColor(233, 69, 96))
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        app_or_window.setPalette(palette)
        
        # Comprehensive QSS Stylesheet
        app_or_window.setStyleSheet("""
            /* ========== Global ========== */
            QMainWindow {
                background-color: #1a1a2e;
            }

            QWidget {
                font-family: 'Segoe UI', 'SF Pro Display', 'Microsoft YaHei UI', sans-serif;
                font-size: 13px;
                color: #e0e0e0;
            }

            /* ========== ScrollArea (Fix for Deep Theme) ========== */
            QScrollArea {
                background-color: transparent;
                border: none;
            }

            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }

            /* ========== Bottom Bar ========== */
            QWidget#bottomBar {
                background-color: #1a1a2e;
                border-top: 1px solid #2d2d4e;
            }

            /* ========== Tab Widget ========== */
            QTabWidget::pane {
                border: 1px solid #2d2d4e;
                border-radius: 10px;
                background-color: #16213e;
                padding: 10px;
            }

            QTabBar::tab {
                background-color: #1a1a2e;
                color: #a0a0a0;
                padding: 10px 24px;
                margin-right: 4px;
                border: 1px solid #2d2d4e;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
                font-size: 13px;
            }

            QTabBar::tab:selected {
                background-color: #16213e;
                color: #e94560;
                border-bottom: 2px solid #e94560;
            }

            QTabBar::tab:hover:!selected {
                background-color: #16213e;
                color: #e0e0e0;
            }

            /* ========== Buttons ========== */
            /* Primary Action Button (Red) */
            QPushButton[objectName="primaryButton"], QPushButton#primaryButton {
                background-color: #e94560;
                color: white;
                border: none;
                padding: 10px 28px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                min-height: 36px;
            }

            QPushButton[objectName="primaryButton"]:hover, QPushButton#primaryButton:hover {
                background-color: #ff6b81;
            }

            QPushButton[objectName="primaryButton"]:pressed, QPushButton#primaryButton:pressed {
                background-color: #c0392b;
            }
            
            QPushButton[objectName="primaryButton"]:disabled, QPushButton#primaryButton:disabled {
                background-color: #555;
                color: #aaa;
            }

            /* Secondary Button (Default) */
            QPushButton {
                background-color: #0f3460;
                color: #e0e0e0;
                border: 1px solid #2d2d4e;
                padding: 8px 20px;
                border-radius: 8px;
                font-size: 13px;
                min-height: 32px;
            }

            QPushButton:hover {
                background-color: #533483;
                border-color: #e94560;
            }

            QPushButton:pressed {
                background-color: #1a1a2e;
            }
            
            QPushButton:disabled {
                background-color: #1a1a2e;
                color: #555;
                border-color: #333;
            }

            /* ========== Input Fields ========== */
            QLineEdit, QTextEdit, QPlainTextEdit {
                background-color: #12122a;
                color: #e0e0e0;
                border: 1px solid #2d2d4e;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
                font-family: 'JetBrains Mono', 'Cascadia Code', 'Consolas', monospace; /* Code font for inputs */
                selection-background-color: #e94560;
            }

            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
                border-color: #e94560;
                background-color: #1a1a2e;
            }

            /* ========== ComboBox ========== */
            QComboBox {
                background-color: #12122a;
                color: #e0e0e0;
                border: 1px solid #2d2d4e;
                border-radius: 6px;
                padding: 8px 12px;
                min-height: 32px;
                font-size: 13px;
            }

            QComboBox:hover {
                border-color: #e94560;
            }

            QComboBox::drop-down {
                border: none;
                width: 30px;
            }

            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #e94560;
                margin-right: 10px;
            }

            QComboBox QAbstractItemView {
                background-color: #12122a;
                color: #e0e0e0;
                selection-background-color: #e94560;
                selection-color: white;
                border: 1px solid #2d2d4e;
                border-radius: 4px;
                padding: 4px;
            }

            /* ========== GroupBox ========== */
            QGroupBox {
                background-color: rgba(15, 52, 96, 0.5); /* Slightly transparent */
                border: 1px solid #2d2d4e;
                border-radius: 10px;
                margin-top: 16px;
                padding: 24px 16px 16px 16px; 
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 16px;
                padding: 0 8px;
                color: #e94560;
                font-weight: bold;
                font-size: 13px;
                background-color: #16213e; /* Match container bg */
                border-radius: 4px;
            }

            /* ========== Labels ========== */
            QLabel {
                color: #e0e0e0;
                font-size: 13px;
            }

            QLabel#titleLabel {
                font-size: 18px;
                font-weight: bold;
                color: #e94560;
            }

            QLabel#subtitleLabel {
                font-size: 11px;
                color: #a0a0a0;
                margin-bottom: 10px;
            }

            QLabel#statusSuccess {
                color: #00b894;
                font-weight: bold;
                padding: 4px;
            }

            QLabel#statusError {
                color: #e94560;
                font-weight: bold;
                padding: 4px;
            }

            /* ========== ScrollBar ========== */
            QScrollBar:vertical {
                background-color: #1a1a2e;
                width: 8px;
                border-radius: 4px;
            }

            QScrollBar::handle:vertical {
                background-color: #2d2d4e;
                border-radius: 4px;
                min-height: 30px;
            }

            QScrollBar::handle:vertical:hover {
                background-color: #e94560;
            }

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }

            /* ========== CheckBox ========== */
            QCheckBox {
                color: #e0e0e0;
                spacing: 8px;
                font-size: 13px;
            }

            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid #2d2d4e;
                background-color: #12122a;
            }

            QCheckBox::indicator:checked {
                background-color: #e94560;
                border-color: #e94560;
            }

            QCheckBox::indicator:hover {
                border-color: #e94560;
            }

            /* ========== ProgressBar ========== */
            QProgressBar {
                background-color: #12122a;
                border: 1px solid #2d2d4e;
                border-radius: 6px;
                height: 8px;
                text-align: center;
                font-size: 11px;
                color: transparent;
            }

            QProgressBar::chunk {
                background-color: #e94560;
                border-radius: 5px;
            }

            /* ========== ToolTip ========== */
            QToolTip {
                background-color: #0f3460;
                color: #e0e0e0;
                border: 1px solid #e94560;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 12px;
            }

            /* ========== StatusBar ========== */
            QStatusBar {
                background-color: #1a1a2e;
                color: #a0a0a0;
                border-top: 1px solid #2d2d4e;
                font-size: 11px;
            }
            
            QStatusBar::item {
                border: none;
            }
        """)
