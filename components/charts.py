"""
YamGuard - Chart Components
Spectral visualization and data charts using matplotlib
"""

import os
import tempfile
import numpy as np
from typing import List, Dict, Any, Optional, Tuple

from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Line, Rectangle, Ellipse
from kivy.properties import ListProperty, NumericProperty, StringProperty
from kivy.metrics import dp, sp
from kivy.clock import Clock

from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
import io

from themes.colors import *


class SpectralChart(Image):
    """
    Interactive spectral signature chart
    Displays hyperspectral reflectance curve
    """
    
    wavelengths = ListProperty([])
    reflectance = ListProperty([])
    reference_reflectance = ListProperty([])
    title = StringProperty("Spectral Signature")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.allow_stretch = True
        self.keep_ratio = False
        self._trigger_redraw = Clock.create_trigger(self._draw_chart, 0.1)
        self.bind(wavelengths=self._trigger_redraw,
                 reflectance=self._trigger_redraw,
                 reference_reflectance=self._trigger_redraw)
    
    def _draw_chart(self, *args):
        """Draw the spectral chart using matplotlib"""
        if not self.wavelengths or not self.reflectance:
            return
        
        try:
            fig = Figure(figsize=(6, 3), dpi=100)
            fig.patch.set_facecolor('#FFFFFF')
            ax = fig.add_subplot(111)
            ax.set_facecolor('#FFFFFF')
            
            # Plot main spectral curve
            ax.plot(self.wavelengths, self.reflectance, 
                   color='#16A34A', linewidth=2, label='Sample', alpha=0.9)
            
            # Plot reference if available
            if self.reference_reflectance and len(self.reference_reflectance) == len(self.wavelengths):
                ax.plot(self.wavelengths, self.reference_reflectance,
                       color='#94A3B8', linewidth=1.5, linestyle='--', 
                       label='Reference', alpha=0.7)
            
            # Highlight key wavelength regions
            ax.axvspan(400, 500, alpha=0.05, color='blue', label='Blue')
            ax.axvspan(500, 600, alpha=0.05, color='green', label='Green')
            ax.axvspan(600, 700, alpha=0.05, color='red', label='Red')
            ax.axvspan(700, 1000, alpha=0.05, color='gray', label='NIR')
            
            # Labels and styling
            ax.set_xlabel('Wavelength (nm)', fontsize=10, color='#1E293B')
            ax.set_ylabel('Reflectance', fontsize=10, color='#1E293B')
            ax.set_title(self.title, fontsize=12, color='#1E293B', fontweight='bold', pad=10)
            
            ax.set_xlim(400, 1000)
            ax.set_ylim(0, 1)
            ax.grid(True, alpha=0.3, linestyle='--')
            
            # Color the spines
            for spine in ax.spines.values():
                spine.set_color('#E2E8F0')
            
            ax.tick_params(colors='#64748B', labelsize=8)
            ax.legend(loc='upper left', fontsize=8, framealpha=0.9)
            
            fig.tight_layout()
            
            # Convert to image
            canvas = FigureCanvasAgg(fig)
            buf = io.BytesIO()
            canvas.print_png(buf)
            buf.seek(0)
            
            # Load as Kivy image
            from kivy.core.image import Image as CoreImage
            self.texture = CoreImage(buf, ext='png').texture
            
            plt.close(fig)
            
        except Exception as e:
            print(f"Chart draw error: {e}")
    
    def update_data(self, wavelengths: List[float], reflectance: List[float],
                   reference: List[float] = None):
        """Update chart data"""
        self.wavelengths = wavelengths
        self.reflectance = reflectance
        if reference:
            self.reference_reflectance = reference


class PCAChart(Image):
    """PCA visualization chart"""
    
    pc_data = ListProperty([])
    labels = ListProperty([])
    title = StringProperty("PCA Visualization")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.allow_stretch = True
        self.keep_ratio = False
        self._trigger_redraw = Clock.create_trigger(self._draw_chart, 0.1)
        self.bind(pc_data=self._trigger_redraw)
    
    def _draw_chart(self, *args):
        if not self.pc_data or len(self.pc_data) < 2:
            return
        
        try:
            fig = Figure(figsize=(5, 4), dpi=100)
            fig.patch.set_facecolor('#FFFFFF')
            ax = fig.add_subplot(111)
            ax.set_facecolor('#FFFFFF')
            
            # Parse PC data
            pc1 = [point[0] for point in self.pc_data]
            pc2 = [point[1] for point in self.pc_data]
            
            # Color points based on classification (simulate with clusters)
            colors = ['#16A34A' if i < len(pc1) * 0.6 else '#F59E0B' if i < len(pc1) * 0.85 else '#DC2626' 
                     for i in range(len(pc1))]
            
            scatter = ax.scatter(pc1, pc2, c=colors, alpha=0.6, s=50, edgecolors='white', linewidth=0.5)
            
            # Add confidence ellipse (simulated)
            if len(pc1) > 2:
                from matplotlib.patches import Ellipse
                mean_x, mean_y = np.mean(pc1), np.mean(pc2)
                std_x, std_y = np.std(pc1), np.std(pc2)
                ellipse = Ellipse((mean_x, mean_y), 2*std_x, 2*std_y,
                                 fill=False, edgecolor='#16A34A', 
                                 linestyle='--', linewidth=1.5, alpha=0.5)
                ax.add_patch(ellipse)
            
            ax.set_xlabel('PC1', fontsize=10, color='#1E293B')
            ax.set_ylabel('PC2', fontsize=10, color='#1E293B')
            ax.set_title(self.title, fontsize=12, color='#1E293B', fontweight='bold', pad=10)
            ax.grid(True, alpha=0.3, linestyle='--')
            
            for spine in ax.spines.values():
                spine.set_color('#E2E8F0')
            ax.tick_params(colors='#64748B', labelsize=8)
            
            # Custom legend
            from matplotlib.lines import Line2D
            legend_elements = [
                Line2D([0], [0], marker='o', color='w', markerfacecolor='#16A34A', 
                      markersize=8, label='Healthy'),
                Line2D([0], [0], marker='o', color='w', markerfacecolor='#F59E0B', 
                      markersize=8, label='Early Infection'),
                Line2D([0], [0], marker='o', color='w', markerfacecolor='#DC2626', 
                      markersize=8, label='Moderate Infection'),
            ]
            ax.legend(handles=legend_elements, loc='best', fontsize=8, framealpha=0.9)
            
            fig.tight_layout()
            
            canvas = FigureCanvasAgg(fig)
            buf = io.BytesIO()
            canvas.print_png(buf)
            buf.seek(0)
            
            from kivy.core.image import Image as CoreImage
            self.texture = CoreImage(buf, ext='png').texture
            
            plt.close(fig)
            
        except Exception as e:
            print(f"PCA chart error: {e}")


class ProbabilityChart(Image):
    """Classification probability bar chart"""
    
    probabilities = ListProperty([])
    class_names = ListProperty([])
    title = StringProperty("Classification Probabilities")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.allow_stretch = True
        self.keep_ratio = False
        self._trigger_redraw = Clock.create_trigger(self._draw_chart, 0.1)
        self.bind(probabilities=self._trigger_redraw)
    
    def _draw_chart(self, *args):
        if not self.probabilities:
            return
        
        try:
            fig = Figure(figsize=(5, 3), dpi=100)
            fig.patch.set_facecolor('#FFFFFF')
            ax = fig.add_subplot(111)
            ax.set_facecolor('#FFFFFF')
            
            classes = self.class_names if self.class_names else [f"Class {i+1}" for i in range(len(self.probabilities))]
            probs = [p * 100 for p in self.probabilities]
            
            # Color bars based on probability
            bar_colors = []
            for p in probs:
                if p > 70:
                    bar_colors.append('#16A34A')
                elif p > 40:
                    bar_colors.append('#F59E0B')
                else:
                    bar_colors.append('#DC2626')
            
            bars = ax.barh(classes, probs, color=bar_colors, alpha=0.8, height=0.5)
            
            # Add percentage labels
            for bar, prob in zip(bars, probs):
                width = bar.get_width()
                ax.text(width + 1, bar.get_y() + bar.get_height()/2,
                       f'{prob:.1f}%', ha='left', va='center',
                       fontsize=9, color='#1E293B', fontweight='bold')
            
            ax.set_xlabel('Probability (%)', fontsize=10, color='#1E293B')
            ax.set_title(self.title, fontsize=12, color='#1E293B', fontweight='bold', pad=10)
            ax.set_xlim(0, 100)
            ax.grid(True, alpha=0.3, linestyle='--', axis='x')
            
            for spine in ax.spines.values():
                spine.set_color('#E2E8F0')
            ax.tick_params(colors='#64748B', labelsize=9)
            ax.invert_yaxis()
            
            fig.tight_layout()
            
            canvas = FigureCanvasAgg(fig)
            buf = io.BytesIO()
            canvas.print_png(buf)
            buf.seek(0)
            
            from kivy.core.image import Image as CoreImage
            self.texture = CoreImage(buf, ext='png').texture
            
            plt.close(fig)
            
        except Exception as e:
            print(f"Probability chart error: {e}")


class TrendChart(Image):
    """Trend analysis line chart"""
    
    dates = ListProperty([])
    values = ListProperty([])
    healthy_values = ListProperty([])
    infected_values = ListProperty([])
    title = StringProperty("Trend Analysis")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.allow_stretch = True
        self.keep_ratio = False
        self._trigger_redraw = Clock.create_trigger(self._draw_chart, 0.1)
        self.bind(dates=self._trigger_redraw, values=self._trigger_redraw)
    
    def _draw_chart(self, *args):
        if not self.dates or not self.values:
            return
        
        try:
            fig = Figure(figsize=(6, 3), dpi=100)
            fig.patch.set_facecolor('#FFFFFF')
            ax = fig.add_subplot(111)
            ax.set_facecolor('#FFFFFF')
            
            x = range(len(self.dates))
            
            # Plot total scans
            ax.plot(x, self.values, color='#3B82F6', linewidth=2, 
                   marker='o', markersize=6, label='Total Scans', alpha=0.9)
            
            # Plot healthy and infected if available
            if self.healthy_values and len(self.healthy_values) == len(self.values):
                ax.plot(x, self.healthy_values, color='#22C55E', linewidth=2,
                       marker='s', markersize=5, label='Healthy', alpha=0.8)
            
            if self.infected_values and len(self.infected_values) == len(self.values):
                ax.plot(x, self.infected_values, color='#DC2626', linewidth=2,
                       marker='^', markersize=5, label='Infected', alpha=0.8)
            
            ax.set_xticks(x)
            ax.set_xticklabels(self.dates, rotation=45, ha='right', fontsize=7)
            ax.set_ylabel('Count', fontsize=10, color='#1E293B')
            ax.set_title(self.title, fontsize=12, color='#1E293B', fontweight='bold', pad=10)
            ax.grid(True, alpha=0.3, linestyle='--')
            ax.legend(loc='best', fontsize=8, framealpha=0.9)
            
            for spine in ax.spines.values():
                spine.set_color('#E2E8F0')
            ax.tick_params(colors='#64748B', labelsize=8)
            
            fig.tight_layout()
            
            canvas = FigureCanvasAgg(fig)
            buf = io.BytesIO()
            canvas.print_png(buf)
            buf.seek(0)
            
            from kivy.core.image import Image as CoreImage
            self.texture = CoreImage(buf, ext='png').texture
            
            plt.close(fig)
            
        except Exception as e:
            print(f"Trend chart error: {e}")


class DistributionChart(Image):
    """Distribution pie/donut chart"""
    
    values = ListProperty([])
    labels = ListProperty([])
    colors_list = ListProperty([])
    title = StringProperty("Distribution")
    chart_type = StringProperty("donut")  # "pie" or "donut"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.allow_stretch = True
        self.keep_ratio = False
        self._trigger_redraw = Clock.create_trigger(self._draw_chart, 0.1)
        self.bind(values=self._trigger_redraw)
    
    def _draw_chart(self, *args):
        if not self.values:
            return
        
        try:
            fig = Figure(figsize=(4, 4), dpi=100)
            fig.patch.set_facecolor('#FFFFFF')
            ax = fig.add_subplot(111)
            ax.set_facecolor('#FFFFFF')
            
            colors = self.colors_list if self.colors_list else ['#16A34A', '#F59E0B', '#DC2626', '#3B82F6', '#8B5CF6']
            labels = self.labels if self.labels else [f"Item {i+1}" for i in range(len(self.values))]
            
            if self.chart_type == "donut":
                wedges, texts, autotexts = ax.pie(
                    self.values, labels=labels, colors=colors,
                    autopct='%1.1f%%', startangle=90,
                    wedgeprops=dict(width=0.4, edgecolor='white', linewidth=2),
                    textprops={'fontsize': 9, 'color': '#1E293B'}
                )
                ax.set_title(self.title, fontsize=12, color='#1E293B', fontweight='bold', pad=10)
            else:
                wedges, texts, autotexts = ax.pie(
                    self.values, labels=labels, colors=colors,
                    autopct='%1.1f%%', startangle=90,
                    textprops={'fontsize': 9, 'color': '#1E293B'}
                )
                ax.set_title(self.title, fontsize=12, color='#1E293B', fontweight='bold', pad=10)
            
            # Style autotexts
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(8)
            
            fig.tight_layout()
            
            canvas = FigureCanvasAgg(fig)
            buf = io.BytesIO()
            canvas.print_png(buf)
            buf.seek(0)
            
            from kivy.core.image import Image as CoreImage
            self.texture = CoreImage(buf, ext='png').texture
            
            plt.close(fig)
            
        except Exception as e:
            print(f"Distribution chart error: {e}")


class ConfidenceChart(MDCard):
    """Card with confidence gauge visualization"""
    
    confidence = NumericProperty(0)
    classification = StringProperty("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(200)
        self.radius = [dp(16), dp(16), dp(16), dp(16)]
        self.elevation = 2
        self.padding = dp(16)
        self._setup_ui()
    
    def _setup_ui(self):
        self.clear_widgets()
        
        layout = MDBoxLayout(orientation='vertical', spacing=dp(8))
        
        # Title
        layout.add_widget(
            MDLabel(
                text="CONFIDENCE SCORE",
                theme_text_color="Secondary",
                font_style="Overline",
                bold=True,
                size_hint_y=None,
                height=dp(16),
                halign='center',
            )
        )
        
        # Gauge area (simplified as progress bar)
        gauge_layout = MDBoxLayout(size_hint_y=None, height=dp(40), padding=[dp(20), 0])
        
        # Background bar
        with gauge_layout.canvas:
            Color(0.9, 0.9, 0.9, 1)
            self.gauge_bg = Rectangle(pos=gauge_layout.pos, size=gauge_layout.size)
            
            # Progress bar
            if self.confidence > 85:
                gauge_color = HEALTHY
            elif self.confidence > 60:
                gauge_color = WARNING
            else:
                gauge_color = INFECTED
            
            Color(*gauge_color[:3])
            progress_width = (self.confidence / 100) * gauge_layout.size[0] if gauge_layout.size[0] > 0 else 0
            self.gauge_fill = Rectangle(
                pos=gauge_layout.pos,
                size=(progress_width, gauge_layout.size[1])
            )
        
        gauge_layout.bind(pos=self._update_gauge, size=self._update_gauge)
        layout.add_widget(gauge_layout)
        
        # Confidence percentage
        layout.add_widget(
            MDLabel(
                text=f"{self.confidence:.1f}%",
                theme_text_color="Primary",
                font_style="H3",
                bold=True,
                halign='center',
                size_hint_y=None,
                height=dp(50),
            )
        )
        
        # Classification label
        if self.classification == "Healthy":
            color = HEALTHY
        elif "Level 1" in self.classification:
            color = WARNING
        else:
            color = INFECTED
        
        layout.add_widget(
            MDLabel(
                text=self.classification,
                theme_text_color="Custom",
                text_color=color,
                font_style="H6",
                bold=True,
                halign='center',
                size_hint_y=None,
                height=dp(30),
            )
        )
        
        self.add_widget(layout)
    
    def _update_gauge(self, instance, value):
        self.gauge_bg.pos = instance.pos
        self.gauge_bg.size = instance.size
        self.gauge_fill.pos = instance.pos
        progress_width = (self.confidence / 100) * instance.size[0]
        self.gauge_fill.size = (progress_width, instance.size[1])
    
    def on_confidence(self, *args):
        self._setup_ui()
