"""
YamGuard - Processing Screen
Animated processing workflow with spectral visualization
"""

import os
import cv2
import numpy as np
from kivy.uix.screen import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.progressbar import ProgressBar
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.properties import NumericProperty, StringProperty
from kivy.metrics import dp, sp
from kivy.animation import Animation
from kivy.clock import Clock

from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton, MDRaisedButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.progressbar import MDProgressBar

from themes.colors import *
from utils.constants import PROCESSING_STAGES
from utils.helpers import generate_tuber_id, get_timestamp
from models.image_processor import ImageProcessor
from models.hyperspectral_simulator import HyperspectralSimulator
from models.feature_extractor import FeatureExtractor
from models.classifier import get_classifier
from components.cards import ProgressStepCard
from components.charts import SpectralChart
from components.dialogs import DialogManager
from database.database import scan_repo, activity_repo


class ProcessingScreen(Screen):
    """Image processing and analysis screen"""
    
    progress = NumericProperty(0)
    current_stage = StringProperty("")
    image_path = StringProperty("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "processing"
        self.image_processor = ImageProcessor()
        self.hyper_sim = HyperspectralSimulator()
        self.feature_extractor = FeatureExtractor()
        self.classifier = get_classifier()
        self._setup_ui()
        self.processing_data = {}
    
    def _setup_ui(self):
        layout = FloatLayout()
        
        # Background
        with layout.canvas.before:
            Color(*BACKGROUND[:3])
            self.bg_rect = Rectangle(pos=layout.pos, size=layout.size)
        layout.bind(pos=self._update_bg, size=self._update_bg)
        
        # Header
        header = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(56),
            pos_hint={'top': 1},
            padding=[dp(8), 0],
            md_bg_color=SURFACE,
        )
        
        header.add_widget(
            MDIconButton(
                icon="close",
                theme_text_color="Custom",
                text_color=TEXT_PRIMARY,
                on_release=self._on_cancel,
            )
        )
        
        header.add_widget(
            MDLabel(
                text="Processing",
                theme_text_color="Primary",
                font_style="H6",
                halign='center',
            )
        )
        
        header.add_widget(MDBoxLayout(size_hint_x=None, width=dp(48)))
        
        layout.add_widget(header)
        
        # Main content
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(16),
            padding=dp(16),
            pos_hint={'x': 0, 'top': 0.92},
            size_hint=(1, 0.85),
        )
        
        # Progress info
        self.progress_label = MDLabel(
            text="Initializing...",
            theme_text_color="Primary",
            font_style="H5",
            bold=True,
            halign='center',
            size_hint_y=None,
            height=dp(40),
        )
        content.add_widget(self.progress_label)
        
        # Progress bar
        self.progress_bar = MDProgressBar(
            value=0,
            color=PRIMARY_GREEN,
            back_color=BORDER,
            size_hint_y=None,
            height=dp(8),
        )
        content.add_widget(self.progress_bar)
        
        self.percentage_label = MDLabel(
            text="0%",
            theme_text_color="Secondary",
            font_style="H6",
            halign='center',
            size_hint_y=None,
            height=dp(30),
        )
        content.add_widget(self.percentage_label)
        
        # Stage cards
        content.add_widget(
            MDLabel(
                text="PROCESSING STAGES",
                theme_text_color="Secondary",
                font_style="Overline",
                bold=True,
                size_hint_y=None,
                height=dp(24),
            )
        )
        
        self.stages_container = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            size_hint_y=None,
            height=dp(280),
        )
        
        self.stage_cards = {}
        for i, stage in enumerate(PROCESSING_STAGES):
            card = ProgressStepCard(
                step_name=stage,
                step_number=i + 1,
            )
            self.stage_cards[stage] = card
            self.stages_container.add_widget(card)
        
        content.add_widget(self.stages_container)
        
        # Spectral chart (shown during processing)
        content.add_widget(
            MDLabel(
                text="LIVE SPECTRAL ANALYSIS",
                theme_text_color="Secondary",
                font_style="Overline",
                bold=True,
                size_hint_y=None,
                height=dp(24),
            )
        )
        
        self.spectral_chart = SpectralChart(
            size_hint_y=None,
            height=dp(180),
        )
        content.add_widget(self.spectral_chart)
        
        # Elapsed time
        self.time_label = MDLabel(
            text="Elapsed: 0.0s",
            theme_text_color="Secondary",
            font_style="Caption",
            halign='center',
            size_hint_y=None,
            height=dp(20),
        )
        content.add_widget(self.time_label)
        
        layout.add_widget(content)
        self.add_widget(layout)
    
    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def set_image_path(self, path: str):
        """Set the image to process"""
        self.image_path = path
    
    def start_processing(self):
        """Start the processing pipeline"""
        if not self.image_path or not os.path.exists(self.image_path):
            DialogManager.show_error("No image to process")
            return
        
        # Reset UI
        self.progress = 0
        self.progress_bar.value = 0
        for card in self.stage_cards.values():
            card.set_active(False)
            card.set_completed(False)
        
        # Start processing sequence
        self.processing_data = {
            'start_time': Clock.get_time(),
            'tuber_id': generate_tuber_id(),
        }
        
        self._processing_step = 0
        Clock.schedule_once(self._process_next_step, 0.5)
    
    def _process_next_step(self, dt):
        """Process next pipeline step"""
        steps = [
            ("Calibration", self._step_calibration, 10),
            ("Noise Reduction", self._step_denoise, 25),
            ("Segmentation", self._step_segment, 45),
            ("Feature Extraction", self._step_features, 70),
            ("Classification", self._step_classify, 95),
        ]
        
        if self._processing_step < len(steps):
            stage_name, stage_func, target_progress = steps[self._processing_step]
            
            # Update UI
            self.progress_label.text = f"{stage_name}..."
            self.current_stage = stage_name
            
            # Mark previous as completed
            for i, (name, _, _) in enumerate(steps):
                if i < self._processing_step:
                    self.stage_cards[name].set_completed(True)
            
            # Mark current as active
            self.stage_cards[stage_name].set_active(True)
            
            # Animate progress
            anim = Animation(value=target_progress, duration=0.8)
            anim.bind(on_complete=lambda *args: stage_func())
            anim.start(self.progress_bar)
            
            self._processing_step += 1
        else:
            # All steps complete
            self._on_processing_complete()
    
    def _step_calibration(self):
        """Calibration step"""
        try:
            image = self.image_processor.load_image(self.image_path)
            if image is not None:
                # White balance
                processed = self.image_processor.white_balance(image)
                self.processing_data['calibrated'] = processed
                
                # Update spectral chart with initial data
                wavelengths, reflectance = self._generate_preview_spectral()
                self.spectral_chart.update_data(wavelengths, reflectance)
        except Exception as e:
            print(f"Calibration error: {e}")
        
        self._update_time()
        Clock.schedule_once(self._process_next_step, 0.3)
    
    def _step_denoise(self):
        """Noise reduction step"""
        try:
            if 'calibrated' in self.processing_data:
                denoised = self.image_processor.denoise(self.processing_data['calibrated'])
                self.processing_data['denoised'] = denoised
        except Exception as e:
            print(f"Denoise error: {e}")
        
        self._update_time()
        Clock.schedule_once(self._process_next_step, 0.3)
    
    def _step_segment(self):
        """Segmentation step"""
        try:
            if 'denoised' in self.processing_data:
                normalized = self.image_processor.normalize(self.processing_data['denoised'])
                segmented, mask = self.image_processor.segment_tuber(normalized)
                self.processing_data['segmented'] = segmented
                self.processing_data['mask'] = mask
        except Exception as e:
            print(f"Segmentation error: {e}")
        
        self._update_time()
        Clock.schedule_once(self._process_next_step, 0.3)
    
    def _step_features(self):
        """Feature extraction step"""
        try:
            # Generate hyperspectral cube
            if 'denoised' in self.processing_data:
                normalized = self.image_processor.normalize(self.processing_data['denoised'])
                hyper_cube = self.hyper_sim.simulate_bands(normalized)
                self.processing_data['hyper_cube'] = hyper_cube
                
                # Extract spectral signature
                mask = self.processing_data.get('mask')
                wavelengths, reflectance = self.hyper_sim.generate_signature(hyper_cube, mask)
                self.processing_data['wavelengths'] = wavelengths
                self.processing_data['reflectance'] = reflectance
                
                # Extract features
                features = self.feature_extractor.extract_all_features(hyper_cube, mask)
                self.processing_data['features'] = features
                self.processing_data['spectral_indices'] = self.hyper_sim.get_spectral_indices(hyper_cube)
                
                # Update spectral chart
                self.spectral_chart.update_data(wavelengths, reflectance)
        except Exception as e:
            print(f"Feature extraction error: {e}")
        
        self._update_time()
        Clock.schedule_once(self._process_next_step, 0.3)
    
    def _step_classify(self):
        """Classification step"""
        try:
            features = self.processing_data.get('features', {})
            spectral_indices = self.processing_data.get('spectral_indices', {})
            
            result = self.classifier.analyze_tuber(features, spectral_indices)
            self.processing_data['result'] = result.to_dict()
            
            # Update progress
            self.progress_label.text = "Analysis Complete!"
            Animation(value=100, duration=0.3).start(self.progress_bar)
            
        except Exception as e:
            print(f"Classification error: {e}")
        
        self._update_time()
        Clock.schedule_once(self._process_next_step, 0.5)
    
    def _on_processing_complete(self):
        """Handle processing completion"""
        # Mark all stages complete
        for card in self.stage_cards.values():
            card.set_completed(True)
        
        self.percentage_label.text = "100%"
        self.progress_label.text = "Complete!"
        
        # Save scan to database
        self._save_scan()
        
        # Navigate to results
        Clock.schedule_once(self._go_to_results, 1.0)
    
    def _save_scan(self):
        """Save scan results to database"""
        try:
            result = self.processing_data.get('result', {})
            user_id = 1  # Default user
            
            scan_repo.create_scan(
                user_id=user_id,
                tuber_id=self.processing_data.get('tuber_id', generate_tuber_id()),
                image_path=self.image_path,
                classification=result.get('classification', 'Unknown'),
                severity_level=result.get('severity', 'Unknown'),
                confidence_score=result.get('confidence', 0),
                recommendation=result.get('recommendation', ''),
                spectral_data={
                    'wavelengths': self.processing_data.get('wavelengths', []),
                    'reflectance': self.processing_data.get('reflectance', []),
                    'indices': self.processing_data.get('spectral_indices', {}),
                },
                pca_data=self.processing_data.get('features', {}).get('pca', {}),
            )
            
            # Log activity
            activity_repo.log_activity(
                user_id,
                "scan_complete",
                f"Completed scan of {self.processing_data.get('tuber_id', 'unknown')}"
            )
            
        except Exception as e:
            print(f"Save scan error: {e}")
    
    def _go_to_results(self, dt):
        """Navigate to results screen"""
        result_screen = self.manager.get_screen("result")
        if result_screen:
            result_screen.set_result_data(self.processing_data)
        
        self.manager.current = "result"
    
    def _generate_preview_spectral(self):
        """Generate preview spectral data"""
        wavelengths = list(np.linspace(400, 1000, 128))
        reflectance = [0.3 + 0.2 * np.sin((w - 400) / 600 * np.pi) + np.random.normal(0, 0.02) for w in wavelengths]
        return wavelengths, reflectance
    
    def _update_time(self):
        """Update elapsed time display"""
        if 'start_time' in self.processing_data:
            elapsed = Clock.get_time() - self.processing_data['start_time']
            self.time_label.text = f"Elapsed: {elapsed:.1f}s"
    
    def _on_cancel(self, instance):
        """Cancel processing and go back"""
        if self.manager:
            self.manager.current = "capture"
    
    def on_enter(self):
        """Start processing when entering"""
        Clock.schedule_once(lambda dt: self.start_processing(), 0.3)
