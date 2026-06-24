"""
YamGuard - History Screen
Scan history with search, filter, and export functionality
"""

import os
from datetime import datetime

from kivy.uix.screen import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.properties import DictProperty

from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton, MDRaisedButton, MDTextButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.chip import MDChip

from themes.colors import *
from utils.helpers import format_datetime
from database.database import scan_repo
from components.cards import ScanResultCard
from components.dialogs import DialogManager


class HistoryScreen(Screen):
    """Scan history screen"""
    
    current_user = DictProperty({})
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "history"
        self._setup_ui()
    
    def _setup_ui(self):
        layout = FloatLayout()
        
        # Background
        with layout.canvas.before:
            Color(*BACKGROUND[:3])
            self.bg_rect = Rectangle(pos=layout.pos, size=layout.size)
        layout.bind(pos=self._update_bg, size=self._update_bg)
        
        # Header
        header = MDTopAppBar(
            title="Scan History",
            type="small",
            elevation=4,
            md_bg_color=PRIMARY_GREEN,
            specific_text_color=TEXT_ON_PRIMARY,
            left_action_items=[["arrow-left", lambda x: self._on_back()]],
            right_action_items=[
                ["filter-variant", lambda x: self._on_filter()],
                ["export", lambda x: self._on_export()],
            ],
        )
        layout.add_widget(header)
        
        # Content
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(12),
            padding=dp(16),
            pos_hint={'x': 0, 'top': 0.92},
            size_hint=(1, 0.88),
        )
        
        # Search bar
        search_box = MDBoxLayout(
            orientation='horizontal',
            spacing=dp(8),
            size_hint_y=None,
            height=dp(48),
        )
        
        self.search_field = MDTextField(
            hint_text="Search by ID or classification...",
            icon_left="magnify",
            mode="rectangle",
            size_hint_x=0.85,
        )
        search_box.add_widget(self.search_field)
        
        search_btn = MDIconButton(
            icon="magnify",
            theme_text_color="Custom",
            text_color=PRIMARY_GREEN,
            size_hint_x=None,
            width=dp(48),
            on_release=self._on_search,
        )
        search_box.add_widget(search_btn)
        
        content.add_widget(search_box)
        
        # Quick filter chips
        chips_box = MDBoxLayout(
            orientation='horizontal',
            spacing=dp(8),
            size_hint_y=None,
            height=dp(36),
        )
        
        self.all_chip = MDChip(
            text="All",
            check=True,
            active=True,
            on_release=lambda x: self._on_chip_filter("all"),
        )
        chips_box.add_widget(self.all_chip)
        
        self.healthy_chip = MDChip(
            text="Healthy",
            check=True,
            on_release=lambda x: self._on_chip_filter("healthy"),
        )
        chips_box.add_widget(self.healthy_chip)
        
        self.infected_chip = MDChip(
            text="Infected",
            check=True,
            on_release=lambda x: self._on_chip_filter("infected"),
        )
        chips_box.add_widget(self.infected_chip)
        
        content.add_widget(chips_box)
        
        # Statistics summary
        self.stats_box = MDBoxLayout(
            orientation='horizontal',
            spacing=dp(8),
            size_hint_y=None,
            height=dp(60),
        )
        
        self.total_label = MDLabel(
            text="Total: 0",
            theme_text_color="Secondary",
            font_style="Caption",
            halign='center',
        )
        self.stats_box.add_widget(self.total_label)
        
        self.healthy_stat = MDLabel(
            text="Healthy: 0%",
            theme_text_color="Custom",
            text_color=HEALTHY,
            font_style="Caption",
            halign='center',
        )
        self.stats_box.add_widget(self.healthy_stat)
        
        self.infected_stat = MDLabel(
            text="Infected: 0%",
            theme_text_color="Custom",
            text_color=INFECTED,
            font_style="Caption",
            halign='center',
        )
        self.stats_box.add_widget(self.infected_stat)
        
        content.add_widget(self.stats_box)
        
        # Results list
        self.results_scroll = ScrollView(do_scroll_x=False)
        self.results_container = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            size_hint_y=None,
            padding=[0, dp(8)],
        )
        self.results_container.bind(
            minimum_height=self.results_container.setter('height')
        )
        
        self.results_scroll.add_widget(self.results_container)
        content.add_widget(self.results_scroll)
        
        layout.add_widget(content)
        self.add_widget(layout)
    
    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def load_history(self, search: str = "", status_filter: str = "all"):
        """Load scan history"""
        user_id = self.current_user.get('id', 1)
        
        if search or status_filter != "all":
            scans = scan_repo.search_scans(user_id, search=search, status_filter=status_filter)
        else:
            scans = scan_repo.get_user_scans(user_id, limit=100)
        
        self._display_scans(scans)
    
    def _display_scans(self, scans: list):
        """Display scan results"""
        self.results_container.clear_widgets()
        
        if not scans:
            self.results_container.add_widget(
                MDLabel(
                    text="No scans found",
                    theme_text_color="Secondary",
                    font_style="Body1",
                    halign='center',
                    valign='center',
                    size_hint_y=None,
                    height=dp(100),
                )
            )
            self.results_container.height = dp(120)
            self._update_stats(0, 0, 0)
            return
        
        healthy_count = sum(1 for s in scans if s.get('classification') == 'Healthy')
        infected_count = len(scans) - healthy_count
        
        self._update_stats(len(scans), healthy_count, infected_count)
        
        self.results_container.height = len(scans) * dp(108) + dp(20)
        
        for scan in scans:
            card = ScanResultCard(
                tuber_id=scan.get('tuber_id', 'Unknown'),
                classification=scan.get('classification', 'Unknown'),
                confidence=scan.get('confidence_score', 0),
                scan_date=format_datetime(scan.get('scan_date', '')),
                severity=scan.get('severity_level', 'Unknown'),
                size_hint_y=None,
                height=dp(100),
            )
            self.results_container.add_widget(card)
    
    def _update_stats(self, total: int, healthy: int, infected: int):
        """Update statistics display"""
        self.total_label.text = f"Total: {total}"
        healthy_pct = (healthy / total * 100) if total > 0 else 0
        infected_pct = (infected / total * 100) if total > 0 else 0
        self.healthy_stat.text = f"Healthy: {healthy_pct:.1f}%"
        self.infected_stat.text = f"Infected: {infected_pct:.1f}%"
    
    def _on_search(self, instance):
        """Search scans"""
        search = self.search_field.text.strip()
        self.load_history(search=search)
    
    def _on_chip_filter(self, filter_type: str):
        """Filter by chip selection"""
        self.all_chip.active = (filter_type == "all")
        self.healthy_chip.active = (filter_type == "healthy")
        self.infected_chip.active = (filter_type == "infected")
        
        self.load_history(status_filter=filter_type)
    
    def _on_filter(self):
        """Show advanced filter dialog"""
        DialogManager.show_alert("Filter", "Use the search bar and filter chips to filter results.")
    
    def _on_export(self):
        """Export history"""
        DialogManager.show_confirm(
            "Export History",
            "Export scan history to CSV?",
            on_confirm=self._export_csv,
        )
    
    def _export_csv(self):
        """Export to CSV"""
        try:
            import csv
            from utils.constants import EXPORTS_DIR
            
            user_id = self.current_user.get('id', 1)
            scans = scan_repo.get_user_scans(user_id, limit=1000)
            
            output_path = os.path.join(EXPORTS_DIR, f"scan_history_{datetime.now().strftime('%Y%m%d')}.csv")
            os.makedirs(EXPORTS_DIR, exist_ok=True)
            
            with open(output_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Tuber ID', 'Classification', 'Severity', 'Confidence', 'Date'])
                for scan in scans:
                    writer.writerow([
                        scan.get('tuber_id', ''),
                        scan.get('classification', ''),
                        scan.get('severity_level', ''),
                        scan.get('confidence_score', ''),
                        scan.get('scan_date', ''),
                    ])
            
            DialogManager.show_success(f"Exported to:\n{output_path}")
        except Exception as e:
            DialogManager.show_error(f"Export failed: {str(e)}")
    
    def _on_back(self):
        """Go back to dashboard"""
        if self.manager:
            self.manager.current = "dashboard"
    
    def on_enter(self):
        """Load history on enter"""
        self.search_field.text = ""
        self.all_chip.active = True
        self.healthy_chip.active = False
        self.infected_chip.active = False
        Clock.schedule_once(lambda dt: self.load_history(), 0.1)
