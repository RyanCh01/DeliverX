from PySide2.QtWidgets import QMainWindow, QTabWidget, QApplication
from config import APP_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT
from ui.theme import Theme

# Import Tabs
from ui.pdf_tab import PDFTab
from ui.html_tab import HTMLTab
from ui.svg_tab import SVGTab
from ui.lnk_tab import LNKTab
from ui.iso_tab import ISOTab
from ui.binder_tab import BinderTab
from ui.canary_tab import CanaryTab
from ui.file_spoofer_tab import FileSpoofTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DeliverX - Phishing & Social Engineering Toolkit | @RyanCh01")
        
        # Center Window
        self.resize(1000, 750)
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2
        )
        
        # Tabs Container
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Add Tabs
        self.create_tabs()
        
        # Status Bar
        self.statusBar().showMessage("Ready | DeliverX v1.0 | Author: @RyanCh01")
        
        # Apply Theme
        Theme.apply_dark_theme(self)

    def create_tabs(self):
        # 1. PDF Generator
        self.pdf_tab = PDFTab()
        self.tabs.addTab(self.pdf_tab, "📄 PDF Generator")
        
        # 2. HTML Smuggling
        self.html_tab = HTMLTab()
        self.tabs.addTab(self.html_tab, "🌐 HTML Smuggling")
        
        # 3. SVG Smuggling
        self.svg_tab = SVGTab()
        self.tabs.addTab(self.svg_tab, "🎨 SVG Generator")

        # 4. LNK Generator
        self.lnk_tab = LNKTab()
        self.tabs.addTab(self.lnk_tab, "🔗 LNK Generator")

        # 5. ISO Packager
        self.iso_tab = ISOTab()
        self.tabs.addTab(self.iso_tab, "💿 ISO Packager")

        # 6. File Binder
        self.binder_tab = BinderTab()
        self.tabs.addTab(self.binder_tab, "📦 File Binder")

        # 7. Canary Token
        self.canary_tab = CanaryTab()
        self.tabs.addTab(self.canary_tab, "🔔 Canary Token")

        # 8. File Spoofer
        self.file_spoof_tab = FileSpoofTab()
        self.tabs.addTab(self.file_spoof_tab, "🕐 File Spoofer")
