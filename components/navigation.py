"""
YamGuard - Navigation Components
Bottom navigation and navigation helpers
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import StringProperty, NumericProperty, ColorProperty
from kivy.metrics import dp, sp
from kivy.animation import Animation
from kivy.clock import Clock

from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton, MDFlatButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.toolbar import MDTopAppBar

from themes.colors import *


class BottomNavBar(MDBottomNavigation):
    """Custom bottom navigation bar"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.panel_color = SURFACE
        self.selected_color_background = PRIMARY_GREEN
        self.text_color_active = PRIMARY_GREEN
        self.text_color_normal = TEXT_SECONDARY
        self.use_text = True
        self.elevation = 8
    
    def build_nav_items(self, screen_manager):
        """Build navigation items"""
        self.clear_widgets()
        
        # Home
        home_item = MDBottomNavigationItem(
            name="home",
            text="Home",
            icon="home",
            on_tab_press=lambda x: self._switch_screen(screen_manager, "dashboard")
        )
        self.add_widget(home_item)
        
        # Scan
        scan_item = MDBottomNavigationItem(
            name="scan",
            text="Scan",
            icon="camera",
            on_tab_press=lambda x: self._switch_screen(screen_manager, "capture")
        )
        self.add_widget(scan_item)
        
        # History
        history_item = MDBottomNavigationItem(
            name="history",
            text="History",
            icon="history",
            on_tab_press=lambda x: self._switch_screen(screen_manager, "history")
        )
        self.add_widget(history_item)
        
        # Reports
        reports_item = MDBottomNavigationItem(
            name="reports",
            text="Reports",
            icon="file-document",
            on_tab_press=lambda x: self._switch_screen(screen_manager, "reports")
        )
        self.add_widget(reports_item)
        
        # Profile
        profile_item = MDBottomNavigationItem(
            name="profile",
            text="Profile",
            icon="account",
            on_tab_press=lambda x: self._switch_screen(screen_manager, "profile")
        )
        self.add_widget(profile_item)
    
    def _switch_screen(self, screen_manager, screen_name):
        """Switch to specified screen"""
        if screen_manager.has_screen(screen_name):
            screen_manager.current = screen_name
    
    def set_active_tab(self, tab_name):
        """Set active tab by name"""
        for item in self.children:
            if isinstance(item, MDBottomNavigationItem) and item.name == tab_name:
                self.switch_tab(item.name)
                break


class AppHeader(MDTopAppBar):
    """Custom app header with title and actions"""
    
    def __init__(self, **kwargs):
        kwargs.setdefault('type', 'small')
        kwargs.setdefault('elevation', 4)
        super().__init__(**kwargs)
        self.md_bg_color = PRIMARY_GREEN
        self.specific_text_color = TEXT_ON_PRIMARY
        self.left_action_items = []
        self.right_action_items = []
    
    def set_title(self, title: str):
        """Update header title"""
        self.title = title
    
    def add_back_button(self, callback):
        """Add back button"""
        self.left_action_items = [["arrow-left", lambda x: callback()]]
    
    def add_action(self, icon: str, callback):
        """Add right action button"""
        current = list(self.right_action_items)
        current.append([icon, lambda x: callback()])
        self.right_action_items = current


class NavDrawerItem(MDBoxLayout):
    """Navigation drawer menu item"""
    
    icon = StringProperty("circle")
    text = StringProperty("")
    badge_count = NumericProperty(0)
    is_active = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(48)
        self.padding = [dp(16), 0, dp(16), 0]
        self.spacing = dp(16)
        self._setup_ui()
    
    def _setup_ui(self):
        self.clear_widgets()
        
        bg_color = (*PRIMARY_GREEN[:3], 0.1) if self.is_active else (0, 0, 0, 0)
        icon_color = PRIMARY_GREEN if self.is_active else TEXT_SECONDARY
        text_color = TEXT_PRIMARY if self.is_active else TEXT_SECONDARY
        
        self.md_bg_color = bg_color
        
        self.add_widget(
            MDIconButton(
                icon=self.icon,
                theme_text_color="Custom",
                text_color=icon_color,
                user_font_size=sp(20),
                size_hint=(None, None),
                size=(dp(32), dp(32)),
                pos_hint={'center_y': 0.5},
            )
        )
        
        self.add_widget(
            MDLabel(
                text=self.text,
                theme_text_color="Custom",
                text_color=text_color,
                font_style="Body1",
                bold=self.is_active,
                pos_hint={'center_y': 0.5},
            )
        )
        
        if self.badge_count > 0:
            badge = MDBoxLayout(
                size_hint=(None, None),
                size=(dp(24), dp(24)),
                pos_hint={'center_y': 0.5},
            )
            with badge.canvas:
                Color(*INFECTED[:3])
                from kivy.graphics import Ellipse
                Ellipse(pos=badge.pos, size=badge.size)
            badge.add_widget(
                MDLabel(
                    text=str(self.badge_count),
                    theme_text_color="Custom",
                    text_color=TEXT_ON_PRIMARY,
                    font_style="Caption",
                    bold=True,
                    halign='center',
                    valign='center',
                    pos_hint={'center_x': 0.5, 'center_y': 0.5},
                )
            )
            self.add_widget(badge)
    
    def set_active(self, active: bool):
        self.is_active = active
        self._setup_ui()


class FloatingScanButton(MDBoxLayout):
    """Floating action button for quick scan"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(56), dp(56))
        self.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        self._setup_ui()
    
    def _setup_ui(self):
        btn = MDIconButton(
            icon="camera",
            theme_text_color="Custom",
            text_color=TEXT_ON_PRIMARY,
            md_bg_color=PRIMARY_GREEN,
            user_font_size=sp(28),
            size_hint=(None, None),
            size=(dp(56), dp(56)),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            radius=[dp(28)] * 4,
        )
        self.add_widget(btn)
    
    def animate_pulse(self):
        """Pulse animation"""
        anim = Animation(md_bg_color=(*LIGHT_GREEN[:3], 1), duration=0.3)
        anim += Animation(md_bg_color=PRIMARY_GREEN, duration=0.3)
        anim.repeat = True
        return anim
