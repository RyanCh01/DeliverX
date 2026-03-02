#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeliverX - Phishing & Social Engineering Toolkit
Author: @RyanCh01
GitHub: https://github.com/RyanCh01
"""

import sys
from PySide2.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # Set Fusion Style
    app.setStyle("Fusion")
    
    # Create and Show Main Window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
