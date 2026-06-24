"""
YamGuard - Splash Screen
Animated splash screen with logo and loading indicator
"""

from kivy.uix.screen import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.graphics import Color, RoundedRectangle, Ellipse, Line
from kivy.properties import NumericProperty, ColorProperty
from kivy.metrics import dp, sp
from kivy.animation import Animation
from kivy.clock import Clock

from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.boxlayout import MDBoxLayout

from themes.colors import *
from utils.constants import APP_NAME, APP_VERSION, APP_DESCRIPTION


class SplashScreen(Screen):
    """Splash screen with animations"""
    
    progress = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "splash"
        self._setup_ui()
        self._start_animation()
    
    def _setup_ui(self):
        layout = FloatLayout()
        
        # Background gradient effect
        with layout.canvas.before:
            Color(*BACKGROUND[:3])
            self.bg_rect = RoundedRectangle(pos=layout.pos, size=layout.size, radius=[0])
        layout.bind(pos=self._update_bg, size=self._update_bg)
        
        # Main content container
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(20),
            size_hint=(0.8, 0.6),
            pos_hint={'center_x': 0.5, 'center_y': 0.55},
        )
        
        # Logo circle
        logo_container = MDBoxLayout(
            size_hint=(None, None),
            size=(dp(120), dp(120)),
            pos_hint={'center_x': 0.5},
        )
        
        with logo_container.canvas:
            Color(*PRIMARY_GREEN[:3])
            self.logo_circle = Ellipse(
                pos=(logo_container.center_x - dp(60), logo_container.center_y - dp(60)),
                size=(dp(120), dp(120))
            )
        logo_container.bind(pos=self._update_logo, size=self._update_logo)
        
        # Logo icon text
        logo_container.add_widget(
            MDLabel(
                text="[b]YG[/b]",
                markup=True,
                theme_text_color="Custom",
                text_color=TEXT_ON_PRIMARY,
                font_style="H3",
                halign='center',
                valign='center',
                pos_hint={'center_x': 0.5, 'center_y': 0.5},
            )
        )
        
        content.add_widget(logo_container)
        
        # App name
        content.add_widget(
            MDLabel(
                text=APP_NAME,
                theme_text_color="Primary",
                font_style="H2",
                bold=True,
                halign='center',
                size_hint_y=None,
                height=dp(50),
            )
        )
        
        # Tagline
        content.add_widget(
            MDLabel(
                text=APP_DESCRIPTION,
                theme_text_color="Secondary",
                font_style="Caption",
                halign='center',
                size_hint_y=None,
                height=dp(40),
            )
        )
        
        # Spacer
        content.add_widget(MDBoxLayout(size_hint_y=None, height=dp(30)))
        
        # Progress bar
        self.progress_bar = MDProgressBar(
            value=0,
            color=PRIMARY_GREEN,
            back_color=BORDER,
            size_hint_y=None,
            height=dp(6),
        )
        content.add_widget(self.progress_bar)
        
        # Loading text
        self.loading_label = MDLabel(
            text="Initializing...",
            theme_text_color="Secondary",
            font_style="Caption",
            halign='center',
            size_hint_y=None,
            height=dp(20),
        )
        content.add_widget(self.loading_label)
        
        # Version
        content.add_widget(
            MDLabel(
                text=f"Version {APP_VERSION}",
                theme_text_color="Secondary",
                font_style="Caption",
                halign='center',
                size_hint_y=None,
                height=dp(20),
            )
        )
        
        layout.add_widget(content)
        self.add_widget(layout)
    
    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def _update_logo(self, instance, value):
        center_x = instance.x + instance.width / 2 - dp(60)
        center_y = instance.y + instance.height / 2 - dp(60)
        self.logo_circle.pos = (center_x, center_y)
    
    def _start_animation(self):
        """Start splash screen animation sequence"""
        # Animate progress bar
        self.anim = Animation(value=100, duration=3.0)
        self.anim.bind(on_progress=self._update_progress)
        self.anim.bind(on_complete=self._on_animation_complete)
        self.anim.start(self.progress_bar)
        
        # Pulse animation for logo
        Clock.schedule_interval(self._pulse_logo, 1.5)
    
    def _update_progress(self, animation, widget, progression):
        self.progress = progression * 100
        
        if progression < 0.3:
            self.loading_label.text = "Loading components..."
        elif progression < 0.6:
            self.loading_label.text = "Initializing database..."
        elif progression < 0.9:
            self.loading_label.text = "Loading models..."
        else:
            self.loading_label.text = "Ready!"
    
    def _on_animation_complete(self, animation, widget):
        """Called when animation completes - transition to login"""
        Clock.unschedule(self._pulse_logo)
        
        # Transition to login screen
        if self.manager:
            self.manager.current = "login"
    
    def _pulse_logo(self, dt):
        """Pulse logo animation"""
        # This would animate the logo in a real implementation
        pass
    
    def on_enter(self):
        """Called when screen is entered"""
        self._start_animation()
    
    def on_leave(self):
        """Called when screen is left"""
        Clock.unschedule(self._pulse_logo)
        if hasattr(self, 'anim'):
            self.anim.cancel(self.progress_bar)
