#!/usr/bin/env python3
"""
SHOCKWAVE PLANNER v2.0
Desktop Launch Operations Planning System
Enhanced with Space Devs Integration and Re-entry Tracking

Author: Remix Astronautics  
Date: December 2025
Version: 2.0.0
"""
import sys
import os
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap
from gui.main_window import MainWindow


def main():
    """Main application entry point"""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
 
    app = QApplication(sys.argv)
    app.setApplicationName("SHOCKWAVE PLANNER v2.0")
    app.setOrganizationName("Remix Astronautics")
    app.setStyle('Fusion')
    
    # Load splash screen if it exists
    base_dir = os.path.dirname(os.path.abspath(__file__))
    splash_path = os.path.join(base_dir, "resources", "splash_intro.png")
    
    splash = None
    if os.path.exists(splash_path):
        pixmap = QPixmap(splash_path)
        splash = QSplashScreen(pixmap)
        splash.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        splash.show()
        app.processEvents()
    
    # Create main window
    window = MainWindow()
    
    # Show window after splash delay or immediately if no splash
    def finish_loading():
        window.show()
        if splash:
            splash.finish(window)
    
    if splash:
        QTimer.singleShot(3000, finish_loading)  # 3 second splash
    else:
        finish_loading()
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
