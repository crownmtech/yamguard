"""
YamGuard - UI Cards
Material Design card components for the application
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.properties import StringProperty, NumericProperty, ListProperty, ColorProperty
from kivy.metrics import dp, sp
from kivy.animation import Animation
from kivy.clock import Clock

from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout

from themes.colors import *


class StatCard(MDCard):
    """Statistics card for dashboard"""
    
    title = StringProperty("")
    value = StringProperty("0")
    unit = StringProperty("")
    icon = StringProperty("chart-bar")
    card_color = ColorProperty(PRIMARY_GREEN)
    text_color = ColorProperty(TEXT_ON_PRIMARY)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(110)
        self.radius = [dp(16), dp(16), dp(16), dp(16)]
        self.elevation = 2
        self.shadow_softness = 8
        self.padding = dp(16)
        self._setup_ui()
    
    def _setup_ui(self):
        self.clear_widgets()
        
        layout = MDBoxLayout(orientation='horizontal', spacing=dp(12))
        
        # Icon container
        icon_box = MDBoxLayout(
            size_hint=(None, None),
            size=(dp(48), dp(48)),
            pos_hint={'center_y': 0.5}
        )
        icon_box.add_widget(
            MDIconButton(
                icon=self.icon,
                theme_text_color="Custom",
                text_color=self.text_color,
                md_bg_color=(*self.card_color[:3], 0.3),
                pos_hint={'center_x': 0.5, 'center_y': 0.5},
            )
        )
        layout.add_widget(icon_box)
        
        # Text content
        text_box = MDBoxLayout(orientation='vertical', spacing=dp(4))
        text_box.add_widget(
            MDLabel(
                text=self.title,
                theme_text_color="Custom",
                text_color=(*self.text_color[:3], 0.8),
                font_style="Caption",
                size_hint_y=None,
                height=dp(20),
            )
        )
        value_box = MDBoxLayout(size_hint_y=None, height=dp(40), spacing=dp(4))
        value_box.add_widget(
            MDLabel(
                text=self.value,
                theme_text_color="Custom",
                text_color=self.text_color,
                font_style="H4",
                bold=True,
                size_hint_x=None,
                width=dp(80),
            )
        )
        if self.unit:
            value_box.add_widget(
                MDLabel(
                    text=self.unit,
                    theme_text_color="Custom",
                    text_color=(*self.text_color[:3], 0.6),
                    font_style="Caption",
                    pos_hint={'center_y': 0.3},
                )
            )
        text_box.add_widget(value_box)
        layout.add_widget(text_box)
        
        self.add_widget(layout)
    
    def on_value(self, *args):
        self._setup_ui()
    
    def on_title(self, *args):
        self._setup_ui()


class ScanResultCard(MDCard):
    """Card displaying scan result"""
    
    tuber_id = StringProperty("")
    classification = StringProperty("")
    confidence = NumericProperty(0)
    scan_date = StringProperty("")
    severity = StringProperty("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(100)
        self.radius = [dp(12), dp(12), dp(12), dp(12)]
        self.elevation = 1
        self.padding = dp(12)
        self.spacing = dp(8)
        self._setup_ui()
    
    def _setup_ui(self):
        self.clear_widgets()
        
        # Determine status color
        if self.classification == "Healthy":
            status_color = HEALTHY
            status_bg = HEALTHY_LIGHT
            status_icon = "check-circle"
        elif "Level 1" in self.classification:
            status_color = WARNING
            status_bg = WARNING_LIGHT
            status_icon = "alert-circle"
        else:
            status_color = INFECTED
            status_bg = INFECTED_LIGHT
            status_icon = "close-circle"
        
        layout = MDBoxLayout(orientation='horizontal', spacing=dp(12))
        
        # Status indicator
        indicator = MDBoxLayout(
            size_hint=(None, 1),
            width=dp(4),
        )
        with indicator.canvas:
            Color(*status_color[:3])
            RoundedRectangle(pos=indicator.pos, size=indicator.size, radius=[dp(4)] * 4)
        layout.add_widget(indicator)
        
        # Content
        content = MDBoxLayout(orientation='vertical', spacing=dp(4))
        content.add_widget(
            MDLabel(
                text=self.tuber_id,
                theme_text_color="Primary",
                font_style="Subtitle2",
                bold=True,
                size_hint_y=None,
                height=dp(24),
            )
        )
        content.add_widget(
            MDBoxLayout(size_hint_y=None, height=dp(24), spacing=dp(8))
        )
        status_row = content.children[0]
        status_row.add_widget(
            MDLabel(
                text=self.classification,
                theme_text_color="Custom",
                text_color=status_color,
                font_style="Caption",
                bold=True,
            )
        )
        status_row.add_widget(
            MDLabel(
                text=f"{self.confidence:.1f}%",
                theme_text_color="Secondary",
                font_style="Caption",
                halign='right',
            )
        )
        
        content.add_widget(
            MDLabel(
                text=self.scan_date,
                theme_text_color="Secondary",
                font_style="Caption",
                size_hint_y=None,
                height=dp(20),
            )
        )
        
        layout.add_widget(content)
        self.add_widget(layout)


class ActivityCard(MDCard):
    """Card displaying recent activity"""
    
    activity = StringProperty("")
    timestamp = StringProperty("")
    icon = StringProperty("circle-medium")
    activity_color = ColorProperty(INFO)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(60)
        self.radius = [dp(8), dp(8), dp(8), dp(8)]
        self.elevation = 0
        self.md_bg_color = SURFACE_VARIANT
        self.padding = dp(12)
        self._setup_ui()
    
    def _setup_ui(self):
        self.clear_widgets()
        
        layout = MDBoxLayout(orientation='horizontal', spacing=dp(12))
        layout.add_widget(
            MDIconButton(
                icon=self.icon,
                theme_text_color="Custom",
                text_color=self.activity_color,
                user_font_size=sp(20),
                size_hint=(None, None),
                size=(dp(36), dp(36)),
                pos_hint={'center_y': 0.5},
            )
        )
        
        text_box = MDBoxLayout(orientation='vertical', spacing=dp(2))
        text_box.add_widget(
            MDLabel(
                text=self.activity,
                theme_text_color="Primary",
                font_style="Body2",
                shorten=True,
                shorten_from='right',
            )
        )
        text_box.add_widget(
            MDLabel(
                text=self.timestamp,
                theme_text_color="Secondary",
                font_style="Caption",
                size_hint_y=None,
                height=dp(16),
            )
        )
        layout.add_widget(text_box)
        
        self.add_widget(layout)


class RecommendationCard(MDCard):
    """Card displaying recommendations"""
    
    recommendation = StringProperty("")
    severity = StringProperty("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(120)
        self.radius = [dp(12), dp(12), dp(12), dp(12)]
        self.elevation = 2
        self.padding = dp(16)
        self._setup_ui()
    
    def _setup_ui(self):
        self.clear_widgets()
        
        if "Healthy" in self.severity:
            card_color = HEALTHY_LIGHT
            icon_color = HEALTHY
            icon = "check-circle"
        elif "Level 1" in self.severity:
            card_color = WARNING_LIGHT
            icon_color = WARNING
            icon = "alert-circle"
        else:
            card_color = INFECTED_LIGHT
            icon_color = INFECTED
            icon = "close-circle"
        
        self.md_bg_color = card_color
        
        layout = MDBoxLayout(orientation='horizontal', spacing=dp(12))
        layout.add_widget(
            MDIconButton(
                icon=icon,
                theme_text_color="Custom",
                text_color=icon_color,
                user_font_size=sp(32),
                size_hint=(None, None),
                size=(dp(48), dp(48)),
                pos_hint={'center_y': 0.5},
            )
        )
        
        text_box = MDBoxLayout(orientation='vertical', spacing=dp(4))
        text_box.add_widget(
            MDLabel(
                text="RECOMMENDATION",
                theme_text_color="Custom",
                text_color=icon_color,
                font_style="Overline",
                bold=True,
                size_hint_y=None,
                height=dp(16),
            )
        )
        text_box.add_widget(
            MDLabel(
                text=self.recommendation,
                theme_text_color="Primary",
                font_style="Body1",
                valign='top',
            )
        )
        layout.add_widget(text_box)
        
        self.add_widget(layout)


class SensorStatusCard(MDCard):
    """Card displaying sensor connection status"""
    
    status = StringProperty("disconnected")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(50)
        self.radius = [dp(25), dp(25), dp(25), dp(25)]
        self.elevation = 1
        self.padding = dp(8)
        self._setup_ui()
    
    def _setup_ui(self):
        self.clear_widgets()
        
        if self.status == "connected":
            bg_color = GREEN_50
            dot_color = HEALTHY
            text_color = DARK_GREEN
            icon = "check-circle"
            label = "Sensor Connected"
        elif self.status == "connecting":
            bg_color = INFO_LIGHT
            dot_color = INFO
            text_color = INFO
            icon = "loading"
            label = "Connecting..."
        else:
            bg_color = WARNING_LIGHT
            dot_color = WARNING
            text_color = get_color_from_hex("#92400E")
            icon = "close-circle"
            label = "No Sensor"
        
        self.md_bg_color = bg_color
        
        layout = MDBoxLayout(
            orientation='horizontal',
            spacing=dp(8),
            padding=[dp(16), 0, dp(16), 0],
        )
        layout.add_widget(
            MDIconButton(
                icon=icon,
                theme_text_color="Custom",
                text_color=dot_color,
                user_font_size=sp(16),
                size_hint=(None, None),
                size=(dp(32), dp(32)),
                pos_hint={'center_y': 0.5},
            )
        )
        layout.add_widget(
            MDLabel(
                text=label,
                theme_text_color="Custom",
                text_color=text_color,
                font_style="Button",
                pos_hint={'center_y': 0.5},
            )
        )
        
        self.add_widget(layout)


class ProgressStepCard(MDCard):
    """Card showing a step in the processing workflow"""
    
    step_name = StringProperty("")
    step_number = NumericProperty(1)
    is_active = False
    is_completed = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(56)
        self.radius = [dp(8), dp(8), dp(8), dp(8)]
        self.elevation = 0
        self.padding = dp(12)
        self._setup_ui()
    
    def _setup_ui(self):
        self.clear_widgets()
        
        if self.is_completed:
            bg_color = GREEN_50
            number_color = HEALTHY
            icon = "check"
        elif self.is_active:
            bg_color = INFO_LIGHT
            number_color = INFO
            icon = "loading"
        else:
            bg_color = SURFACE_VARIANT
            number_color = TEXT_TERTIARY
            icon = "circle-outline"
        
        self.md_bg_color = bg_color
        
        layout = MDBoxLayout(orientation='horizontal', spacing=dp(12))
        layout.add_widget(
            MDIconButton(
                icon=icon,
                theme_text_color="Custom",
                text_color=number_color,
                user_font_size=sp(20),
                size_hint=(None, None),
                size=(dp(32), dp(32)),
                pos_hint={'center_y': 0.5},
            )
        )
        layout.add_widget(
            MDLabel(
                text=f"{self.step_number}. {self.step_name}",
                theme_text_color="Primary" if (self.is_active or self.is_completed) else "Secondary",
                font_style="Body1",
                bold=self.is_active,
                pos_hint={'center_y': 0.5},
            )
        )
        
        self.add_widget(layout)
    
    def set_active(self, active=True):
        self.is_active = active
        self._setup_ui()
    
    def set_completed(self, completed=True):
        self.is_completed = completed
        self.is_active = False
        self._setup_ui()
