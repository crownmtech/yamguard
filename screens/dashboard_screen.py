"""
YamGuard - Dashboard Screen
Main dashboard with statistics, recent activity, and navigation
"""

from kivy.uix.screen import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.properties import StringProperty, DictProperty

from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton, MDRaisedButton, MDFloatingActionButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.list import MDList, OneLineIconListItem, IconLeftWidget

from themes.colors import *
from utils.constants import APP_NAME
from utils.helpers import format_datetime, get_initials
from database.database import scan_repo
from components.cards import StatCard, SensorStatusCard, ActivityCard
from components.navigation import BottomNavBar


class DashboardScreen(Screen):
    """Main dashboard screen"""
    
    current_user = DictProperty({})
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "dashboard"
        self._setup_ui()
    
    def _setup_ui(self):
        layout = FloatLayout()
        
        # Background
        with layout.canvas.before:
            Color(*BACKGROUND[:3])
            self.bg_rect = Rectangle(pos=layout.pos, size=layout.size)
        layout.bind(pos=self._update_bg, size=self._update_bg)
        
        # Main content
        main_layout = MDBoxLayout(
            orientation='vertical',
            pos_hint={'x': 0, 'top': 0.95},
            size_hint=(1, 0.95),
        )
        
        # Scrollable content
        scroll = ScrollView(do_scroll_x=False)
        self.content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(16),
            padding=dp(16),
            size_hint_y=None,
            height=dp(800),
        )
        self.content.bind(minimum_height=self.content.setter('height'))
        
        # Welcome header
        self.welcome_label = MDLabel(
            text="Welcome!",
            theme_text_color="Primary",
            font_style="H5",
            bold=True,
            size_hint_y=None,
            height=dp(36),
        )
        self.content.add_widget(self.welcome_label)
        
        self.date_label = MDLabel(
            text=format_datetime(),
            theme_text_color="Secondary",
            font_style="Caption",
            size_hint_y=None,
            height=dp(20),
        )
        self.content.add_widget(self.date_label)
        
        # Sensor status
        self.sensor_card = SensorStatusCard(status="disconnected")
        self.content.add_widget(self.sensor_card)
        
        # Statistics grid
        self.content.add_widget(
            MDLabel(
                text="STATISTICS",
                theme_text_color="Secondary",
                font_style="Overline",
                bold=True,
                size_hint_y=None,
                height=dp(24),
            )
        )
        
        stats_grid = MDGridLayout(
            cols=2,
            spacing=dp(12),
            size_hint_y=None,
            height=dp(240),
        )
        
        self.stat_total = StatCard(
            title="Total Scans",
            value="0",
            icon="magnify-scan",
            card_color=PRIMARY_GREEN,
        )
        stats_grid.add_widget(self.stat_total)
        
        self.stat_healthy = StatCard(
            title="Healthy",
            value="0",
            unit="detections",
            icon="check-circle",
            card_color=HEALTHY,
        )
        stats_grid.add_widget(self.stat_healthy)
        
        self.stat_infected = StatCard(
            title="Infected",
            value="0",
            unit="detections",
            icon="alert-circle",
            card_color=WARNING,
        )
        stats_grid.add_widget(self.stat_infected)
        
        self.stat_rate = StatCard(
            title="Infection Rate",
            value="0.0",
            unit="%",
            icon="trending-up",
            card_color=INFECTED,
        )
        stats_grid.add_widget(self.stat_rate)
        
        self.content.add_widget(stats_grid)
        
        # New scan button
        scan_btn = MDRaisedButton(
            text="START NEW SCAN",
            icon="camera",
            theme_text_color="Custom",
            text_color=TEXT_ON_PRIMARY,
            md_bg_color=PRIMARY_GREEN,
            size_hint=(1, None),
            height=dp(50),
            pos_hint={'center_x': 0.5},
            radius=[dp(12), dp(12), dp(12), dp(12)],
            font_style="Button",
            on_release=self._on_new_scan,
        )
        self.content.add_widget(scan_btn)
        
        # Recent activity
        self.content.add_widget(
            MDLabel(
                text="RECENT ACTIVITY",
                theme_text_color="Secondary",
                font_style="Overline",
                bold=True,
                size_hint_y=None,
                height=dp(24),
            )
        )
        
        self.activity_container = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            size_hint_y=None,
            height=dp(300),
        )
        self.content.add_widget(self.activity_container)
        
        scroll.add_widget(self.content)
        main_layout.add_widget(scroll)
        
        layout.add_widget(main_layout)
        
        # Floating scan button
        fab = MDFloatingActionButton(
            icon="camera",
            theme_text_color="Custom",
            text_color=TEXT_ON_PRIMARY,
            md_bg_color=PRIMARY_GREEN,
            pos_hint={'right': 0.95, 'y': 0.08},
            on_release=self._on_new_scan,
            elevation=4,
        )
        layout.add_widget(fab)
        
        # Bottom navigation
        self.bottom_nav = BottomNavBar()
        self.bottom_nav.build_nav_items(self.manager)
        layout.add_widget(self.bottom_nav)
        
        self.add_widget(layout)
    
    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def _on_new_scan(self, instance):
        """Navigate to capture screen"""
        if self.manager:
            self.manager.current = "capture"
    
    def load_data(self):
        """Load dashboard data"""
        user_id = self.current_user.get('id', 1)
        
        # Update welcome
        name = self.current_user.get('fullname', 'User')
        self.welcome_label.text = f"Welcome, {name.split()[0]}!"
        
        # Get statistics
        stats = scan_repo.get_scan_statistics(user_id)
        
        self.stat_total.value = str(stats['total_scans'])
        self.stat_healthy.value = str(stats['healthy_count'])
        self.stat_infected.value = str(stats['infected_count'])
        self.stat_rate.value = f"{stats['infection_rate']}"
        
        # Load recent activity
        self._load_recent_activity(user_id)
    
    def _load_recent_activity(self, user_id: int):
        """Load recent scan activity"""
        self.activity_container.clear_widgets()
        
        recent = scan_repo.get_recent_scans(user_id, limit=5)
        
        if not recent:
            self.activity_container.add_widget(
                MDLabel(
                    text="No recent activity",
                    theme_text_color="Secondary",
                    font_style="Caption",
                    halign='center',
                    size_hint_y=None,
                    height=dp(60),
                )
            )
            self.activity_container.height = dp(80)
            return
        
        self.activity_container.height = len(recent) * dp(68) + dp(20)
        
        for scan in recent:
            classification = scan.get('classification', 'Unknown')
            if classification == 'Healthy':
                icon = "check-circle"
                color = HEALTHY
            elif 'Level 1' in classification:
                icon = "alert-circle"
                color = WARNING
            else:
                icon = "close-circle"
                color = INFECTED
            
            card = ActivityCard(
                activity=f"Scan {scan.get('tuber_id', 'Unknown')}: {classification}",
                timestamp=format_datetime(scan.get('scan_date')),
                icon=icon,
                activity_color=color,
            )
            self.activity_container.add_widget(card)
    
    def on_enter(self):
        """Load data when entering screen"""
        Clock.schedule_once(lambda dt: self.load_data(), 0.1)
