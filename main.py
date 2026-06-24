"""
YamGuard - Main Application Entry Point
Agricultural AI System for Early Detection of Fungal Infection in Yam Tubers
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('YamGuard')

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.absolute()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from kivy.config import Config
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import DictProperty, StringProperty
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, FadeTransition, SlideTransition

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton, MDRaisedButton
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.snackbar import MDSnackbar

# Import theme
from themes.colors import PRIMARY_GREEN, BACKGROUND, TEXT_PRIMARY, TEXT_ON_PRIMARY

# Import screens
from screens.splash_screen import SplashScreen
from screens.login_screen import LoginScreen
from screens.register_screen import RegisterScreen
from screens.dashboard_screen import DashboardScreen
from screens.capture_screen import CaptureScreen
from screens.processing_screen import ProcessingScreen
from screens.result_screen import ResultScreen
from screens.history_screen import HistoryScreen
from screens.report_screen import ReportScreen
from screens.profile_screen import ProfileScreen

# Import utilities
from utils.constants import APP_NAME, APP_VERSION, APP_DESCRIPTION, BASE_DIR
from utils.helpers import ensure_directories
from database.database import DatabaseManager


class YamGuardScreenManager(ScreenManager):
    """Custom screen manager with transitions"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.transition = FadeTransition(duration=0.3)
    
    def switch_screen(self, screen_name: str, direction: str = "left"):
        """Switch to screen with slide transition"""
        self.transition = SlideTransition(direction=direction)
        self.current = screen_name


class YamGuardApp(MDApp):
    """
    YamGuard Main Application Class
    
    Manages application lifecycle, navigation, and global state.
    """
    
    # Properties
    current_user = DictProperty({})
    theme_color = StringProperty("Green")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = APP_NAME
        self.theme_cls.primary_palette = "Green"
        self.theme_cls.primary_hue = "600"
        self.theme_cls.theme_style = "Light"
        self._screen_manager = None
    
    def build(self):
        """Build the application"""
        logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
        
        # Ensure directories exist
        ensure_directories()
        
        # Initialize database
        try:
            db = DatabaseManager()
            logger.info("Database initialized")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
        
        # Configure window
        Window.clearcolor = BACKGROUND
        Window.softinput_mode = "below_target"
        
        # Create root layout
        root = MDFloatLayout()
        
        # Create screen manager
        self._screen_manager = YamGuardScreenManager()
        
        # Add all screens
        self._add_screens()
        
        root.add_widget(self._screen_manager)
        
        # Return root
        return root
    
    def _add_screens(self):
        """Add all application screens"""
        screens = [
            SplashScreen(),
            LoginScreen(),
            RegisterScreen(),
            DashboardScreen(),
            CaptureScreen(),
            ProcessingScreen(),
            ResultScreen(),
            HistoryScreen(),
            ReportScreen(),
            ProfileScreen(),
        ]
        
        for screen in screens:
            self._screen_manager.add_widget(screen)
    
    def set_current_user(self, user_data: dict):
        """Set current authenticated user"""
        self.current_user = user_data
        
        # Update screens that need user data
        for screen_name in ['dashboard', 'history', 'report', 'profile']:
            screen = self._screen_manager.get_screen(screen_name)
            if screen and hasattr(screen, 'current_user'):
                screen.current_user = user_data
        
        logger.info(f"User logged in: {user_data.get('email', 'Unknown')}")
    
    def clear_current_user(self):
        """Clear current user (logout)"""
        self.current_user = {}
        logger.info("User logged out")
    
    def show_message(self, message: str, duration: float = 2.0):
        """Show snackbar message"""
        snackbar = MDSnackbar(
            text=message,
            duration=duration,
            bg_color=PRIMARY_GREEN,
            snackbar_x=dp(10),
            snackbar_y=dp(10),
        )
        snackbar.size_hint_x = 0.95
        snackbar.open()
    
    def on_start(self):
        """Called when application starts"""
        logger.info("Application started")
    
    def on_stop(self):
        """Called when application stops"""
        logger.info("Application stopping")
    
    def on_pause(self):
        """Called when application is paused (Android)"""
        logger.info("Application paused")
        return True
    
    def on_resume(self):
        """Called when application resumes (Android)"""
        logger.info("Application resumed")


def main():
    """Main entry point"""
    try:
        # Kivy configuration for mobile
        Config.set('graphics', 'width', '360')
        Config.set('graphics', 'height', '640')
        Config.set('graphics', 'resizable', '0')
        Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
        Config.set('kivy', 'exit_on_escape', '0')
        
        # Run application
        YamGuardApp().run()
        
    except Exception as e:
        logger.critical(f"Application crash: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()
