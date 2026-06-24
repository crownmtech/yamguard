"""
YamGuard - Result Screen
Display classification results with spectral analysis and recommendations
"""

from kivy.uix.screen import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.graphics import Color, RoundedRectangle, Ellipse, Rectangle
from kivy.graphics.texture import Texture
from kivy.properties import DictProperty, StringProperty, NumericProperty
from kivy.metrics import dp, sp
from kivy.clock import Clock

import cv2
import numpy as np

from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton, MDRaisedButton, MDTextButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.tabs import MDTabs, MDTabsBase, MDTabsLabel
from kivymd.uix.toolbar import MDTopAppBar

from themes.colors import *
from utils.helpers import format_datetime
from components.cards import RecommendationCard, ConfidenceChart
from components.charts import SpectralChart, PCAChart, ProbabilityChart
from components.dialogs import DialogManager


class ResultTab(MDBoxLayout, MDTabsBase):
    """Tab content container"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(8)


class ResultScreen(Screen):
    """Scan result display screen"""
    
    result_data = DictProperty({})
    classification = StringProperty("")
    confidence = NumericProperty(0)
    severity = StringProperty("")
    recommendation = StringProperty("")
    tuber_id = StringProperty("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "result"
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
            title="Scan Result",
            type="small",
            elevation=4,
            md_bg_color=PRIMARY_GREEN,
            specific_text_color=TEXT_ON_PRIMARY,
            left_action_items=[["arrow-left", lambda x: self._on_back()]],
            right_action_items=[["share-variant", lambda x: self._on_share()]],
        )
        layout.add_widget(header)
        
        # Scrollable content
        scroll = ScrollView(do_scroll_x=False)
        self.content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(12),
            padding=dp(16),
            size_hint_y=None,
            height=dp(1200),
        )
        
        # Status circle
        self.status_container = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            size_hint_y=None,
            height=dp(200),
            padding=[0, dp(16)],
        )
        
        # Status icon (will be colored based on result)
        self.status_icon = MDIconButton(
            icon="help-circle",
            theme_text_color="Custom",
            text_color=TEXT_TERTIARY,
            user_font_size=sp(80),
            size_hint=(None, None),
            size=(dp(100), dp(100)),
            pos_hint={'center_x': 0.5},
        )
        self.status_container.add_widget(self.status_icon)
        
        self.status_label = MDLabel(
            text="Analyzing...",
            theme_text_color="Primary",
            font_style="H4",
            bold=True,
            halign='center',
            size_hint_y=None,
            height=dp(40),
        )
        self.status_container.add_widget(self.status_label)
        
        self.tuber_id_label = MDLabel(
            text="",
            theme_text_color="Secondary",
            font_style="Caption",
            halign='center',
            size_hint_y=None,
            height=dp(20),
        )
        self.status_container.add_widget(self.tuber_id_label)
        
        self.content.add_widget(self.status_container)
        
        # Confidence score
        self.confidence_chart = ConfidenceChart(
            confidence=0,
            classification="",
            size_hint_y=None,
            height=dp(180),
        )
        self.content.add_widget(self.confidence_chart)
        
        # Recommendation card
        self.recommendation_card = RecommendationCard(
            recommendation="",
            severity="",
            size_hint_y=None,
            height=dp(140),
        )
        self.content.add_widget(self.recommendation_card)
        
        # Detail tabs
        self.content.add_widget(
            MDLabel(
                text="DETAILED ANALYSIS",
                theme_text_color="Secondary",
                font_style="Overline",
                bold=True,
                size_hint_y=None,
                height=dp(24),
            )
        )
        
        # Tab layout
        tab_container = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(350),
        )
        
        tabs = MDTabs(
            tab_indicator_height=dp(3),
            tab_indicator_color=PRIMARY_GREEN,
            text_color_active=PRIMARY_GREEN,
            text_color_normal=TEXT_SECONDARY,
        )
        
        # Spectral tab
        spectral_tab = ResultTab(title="Spectral")
        self.spectral_chart = SpectralChart(
            size_hint_y=None,
            height=dp(250),
        )
        spectral_tab.add_widget(self.spectral_chart)
        tabs.add_widget(spectral_tab)
        
        # PCA tab
        pca_tab = ResultTab(title="PCA")
        self.pca_chart = PCAChart(
            size_hint_y=None,
            height=dp(250),
        )
        pca_tab.add_widget(self.pca_chart)
        tabs.add_widget(pca_tab)
        
        # Probability tab
        prob_tab = ResultTab(title="Probabilities")
        self.prob_chart = ProbabilityChart(
            size_hint_y=None,
            height=dp(250),
        )
        prob_tab.add_widget(self.prob_chart)
        tabs.add_widget(prob_tab)
        
        tab_container.add_widget(tabs)
        self.content.add_widget(tab_container)
        
        # Action buttons
        actions = MDBoxLayout(
            orientation='horizontal',
            spacing=dp(12),
            size_hint_y=None,
            height=dp(50),
            padding=[0, dp(8)],
        )
        
        actions.add_widget(
            MDRaisedButton(
                text="NEW SCAN",
                icon="camera",
                theme_text_color="Custom",
                text_color=TEXT_ON_PRIMARY,
                md_bg_color=PRIMARY_GREEN,
                size_hint=(0.48, 1),
                on_release=self._on_new_scan,
            )
        )
        
        actions.add_widget(
            MDRaisedButton(
                text="SAVE REPORT",
                icon="file-pdf-box",
                theme_text_color="Custom",
                text_color=TEXT_ON_PRIMARY,
                md_bg_color=DARK_GREEN,
                size_hint=(0.48, 1),
                on_release=self._on_save_report,
            )
        )
        
        self.content.add_widget(actions)
        
        # Home button
        self.content.add_widget(
            MDTextButton(
                text="Back to Dashboard",
                theme_text_color="Custom",
                text_color=TEXT_SECONDARY,
                font_style="Button",
                pos_hint={'center_x': 0.5},
                size_hint_y=None,
                height=dp(40),
                on_release=self._on_home,
            )
        )
        
        scroll.add_widget(self.content)
        layout.add_widget(scroll)
        self.add_widget(layout)
    
    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def set_result_data(self, data: dict):
        """Set result data from processing"""
        self.result_data = data
        
        result = data.get('result', {})
        self.classification = result.get('classification', 'Unknown')
        self.confidence = result.get('confidence', 0)
        self.severity = result.get('severity', 'Unknown')
        self.recommendation = result.get('recommendation', '')
        self.tuber_id = data.get('tuber_id', '')
    
    def _update_display(self):
        """Update display with result data"""
        result = self.result_data.get('result', {})
        
        classification = result.get('classification', 'Unknown')
        confidence = result.get('confidence', 0)
        severity = result.get('severity', 'Unknown')
        recommendation = result.get('recommendation', '')
        
        # Update status
        if classification == 'Healthy':
            self.status_icon.icon = "check-circle"
            self.status_icon.text_color = HEALTHY
            self.status_label.text = "HEALTHY"
            status_color = HEALTHY
        elif 'Level 1' in classification:
            self.status_icon.icon = "alert-circle"
            self.status_icon.text_color = WARNING
            self.status_label.text = "EARLY INFECTION"
            status_color = WARNING
        else:
            self.status_icon.icon = "close-circle"
            self.status_icon.text_color = INFECTED
            self.status_label.text = "INFECTED"
            status_color = INFECTED
        
        self.tuber_id_label.text = f"ID: {self.tuber_id}"
        
        # Update confidence
        self.confidence_chart.confidence = confidence
        self.confidence_chart.classification = classification
        
        # Update recommendation
        self.recommendation_card.recommendation = recommendation
        self.recommendation_card.severity = severity
        
        # Update spectral chart
        wavelengths = self.result_data.get('wavelengths', [])
        reflectance = self.result_data.get('reflectance', [])
        if wavelengths and reflectance:
            self.spectral_chart.update_data(wavelengths, reflectance)
        
        # Update PCA chart
        pca_data = self.result_data.get('features', {}).get('pca', {}).get('transformed_data', [])
        if pca_data:
            # Convert to 2D points
            pc_points = [[p[0], p[1]] for p in pca_data if len(p) >= 2]
            if pc_points:
                self.pca_chart.pc_data = pc_points
        
        # Update probability chart
        probabilities = result.get('probabilities', {})
        if probabilities:
            self.prob_chart.class_names = list(probabilities.keys())
            self.prob_chart.probabilities = [v / 100.0 for v in probabilities.values()]
    
    def _on_back(self):
        """Go back"""
        if self.manager:
            self.manager.current = "capture"
    
    def _on_share(self):
        """Share result"""
        DialogManager.show_alert("Share", "Sharing functionality will be implemented in a future update.")
    
    def _on_new_scan(self, instance):
        """Start new scan"""
        if self.manager:
            self.manager.current = "capture"
    
    def _on_save_report(self, instance):
        """Save PDF report"""
        try:
            from reports.report_generator import get_report_generator
            
            user_info = {"fullname": "Test User", "organization": "YamGuard"}
            
            scan_data = {
                'tuber_id': self.tuber_id,
                'classification': self.classification,
                'severity_level': self.severity,
                'confidence_score': self.confidence,
                'recommendation': self.recommendation,
                'spectral_data': {
                    'indices': self.result_data.get('spectral_indices', {})
                },
                'scan_date': format_datetime(),
            }
            
            report_gen = get_report_generator()
            pdf_path = report_gen.generate_scan_report(scan_data, user_info)
            
            DialogManager.show_success(f"Report saved to:\n{pdf_path}")
            
        except Exception as e:
            DialogManager.show_error(f"Failed to generate report: {str(e)}")
    
    def _on_home(self, instance):
        """Go to dashboard"""
        if self.manager:
            self.manager.current = "dashboard"
    
    def on_enter(self):
        """Update display when entering"""
        Clock.schedule_once(lambda dt: self._update_display(), 0.1)
