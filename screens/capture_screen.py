"""
YamGuard - Camera Capture Screen
Handles image capture with camera controls
"""

import os
import cv2
import numpy as np
from kivy.uix.screen import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, RoundedRectangle, Rectangle, Line
from kivy.graphics.texture import Texture
from kivy.properties import StringProperty, BooleanProperty
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.core.window import Window

from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton, MDRaisedButton, MDFloatingActionButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.toolbar import MDTopAppBar

from themes.colors import *
from utils.constants import UPLOADS_DIR
from utils.helpers import generate_filename, generate_tuber_id
from models.image_processor import ImageProcessor
from components.dialogs import DialogManager


class CaptureScreen(Screen):
    """Camera capture screen with live preview"""
    
    is_capturing = BooleanProperty(False)
    has_image = BooleanProperty(False)
    current_image_path = StringProperty("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "capture"
        self.image_processor = ImageProcessor()
        self.capture = None
        self.preview_texture = None
        self.captured_image = None
        self._setup_ui()
        self._clock_event = None
    
    def _setup_ui(self):
        layout = FloatLayout()
        
        # Background
        with layout.canvas.before:
            Color(0, 0, 0, 1)
            self.bg_rect = Rectangle(pos=layout.pos, size=layout.size)
        layout.bind(pos=self._update_bg, size=self._update_bg)
        
        # Camera preview area
        self.preview = Image(
            allow_stretch=True,
            keep_ratio=True,
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            size_hint=(1, 1),
        )
        layout.add_widget(self.preview)
        
        # Overlay guides
        self.overlay = FloatLayout()
        
        # Corner brackets for positioning guide
        guide_color = (1, 1, 1, 0.5)
        guide_size = dp(30)
        center_x, center_y = 0.5, 0.45
        box_width, box_height = 0.7, 0.4
        
        with self.overlay.canvas:
            # Top-left corner
            Color(*guide_color)
            self.tl_h = Line(points=[0, 0, 0, 0], width=2)
            self.tl_v = Line(points=[0, 0, 0, 0], width=2)
            # Top-right corner
            self.tr_h = Line(points=[0, 0, 0, 0], width=2)
            self.tr_v = Line(points=[0, 0, 0, 0], width=2)
            # Bottom-left corner
            self.bl_h = Line(points=[0, 0, 0, 0], width=2)
            self.bl_v = Line(points=[0, 0, 0, 0], width=2)
            # Bottom-right corner
            self.br_h = Line(points=[0, 0, 0, 0], width=2)
            self.br_v = Line(points=[0, 0, 0, 0], width=2)
        
        self.overlay.bind(pos=self._update_guides, size=self._update_guides)
        layout.add_widget(self.overlay)
        
        # Top bar
        top_bar = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(56),
            pos_hint={'top': 1},
            padding=[dp(8), 0],
            md_bg_color=(0, 0, 0, 0.5),
        )
        
        top_bar.add_widget(
            MDIconButton(
                icon="arrow-left",
                theme_text_color="Custom",
                text_color=TEXT_ON_PRIMARY,
                on_release=self._on_back,
            )
        )
        
        top_bar.add_widget(
            MDLabel(
                text="New Scan",
                theme_text_color="Custom",
                text_color=TEXT_ON_PRIMARY,
                font_style="H6",
                halign='center',
            )
        )
        
        top_bar.add_widget(
            MDIconButton(
                icon="flash",
                theme_text_color="Custom",
                text_color=TEXT_ON_PRIMARY,
                on_release=self._toggle_flash,
            )
        )
        
        layout.add_widget(top_bar)
        
        # Step indicator
        step_bar = MDBoxLayout(
            orientation='horizontal',
            size_hint=(0.8, None),
            height=dp(36),
            pos_hint={'center_x': 0.5, 'top': 0.92},
            spacing=dp(8),
        )
        
        steps = ["Reference", "Position", "Spectral", "Process"]
        self.step_labels = []
        for i, step in enumerate(steps):
            step_label = MDLabel(
                text=f"{i+1}. {step}",
                theme_text_color="Custom",
                text_color=(*TEXT_ON_PRIMARY[:3], 0.6) if i > 0 else TEXT_ON_PRIMARY,
                font_style="Caption",
                halign='center',
                bold=(i == 0),
            )
            self.step_labels.append(step_label)
            step_bar.add_widget(step_label)
        
        layout.add_widget(step_bar)
        
        # Bottom control bar
        control_bar = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(120),
            pos_hint={'y': 0},
            padding=[dp(20), dp(16)],
            md_bg_color=(0, 0, 0, 0.7),
        )
        
        # Gallery button
        control_bar.add_widget(
            MDIconButton(
                icon="image",
                theme_text_color="Custom",
                text_color=TEXT_ON_PRIMARY,
                user_font_size=sp(24),
                size_hint=(None, None),
                size=(dp(48), dp(48)),
                pos_hint={'center_y': 0.5},
                on_release=self._on_gallery,
            )
        )
        
        # Capture button (center, larger)
        capture_container = MDBoxLayout(
            size_hint_x=0.6,
            pos_hint={'center_y': 0.5},
        )
        self.capture_btn = MDFloatingActionButton(
            icon="camera",
            theme_text_color="Custom",
            text_color=TEXT_ON_PRIMARY,
            md_bg_color=PRIMARY_GREEN,
            size=(dp(64), dp(64)),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            elevation=4,
            on_release=self._on_capture,
        )
        capture_container.add_widget(self.capture_btn)
        control_bar.add_widget(capture_container)
        
        # Switch camera button
        control_bar.add_widget(
            MDIconButton(
                icon="camera-flip",
                theme_text_color="Custom",
                text_color=TEXT_ON_PRIMARY,
                user_font_size=sp(24),
                size_hint=(None, None),
                size=(dp(48), dp(48)),
                pos_hint={'center_y': 0.5},
                on_release=self._switch_camera,
            )
        )
        
        layout.add_widget(control_bar)
        
        # Preview action bar (shown after capture)
        self.preview_bar = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(80),
            pos_hint={'y': 0.15},
            padding=[dp(40), dp(8)],
            spacing=dp(20),
            opacity=0,
        )
        
        self.retake_btn = MDRaisedButton(
            text="RETAKE",
            theme_text_color="Custom",
            text_color=TEXT_PRIMARY,
            md_bg_color=(*SURFACE[:3], 1),
            size_hint=(0.45, 1),
            on_release=self._on_retake,
        )
        self.preview_bar.add_widget(self.retake_btn)
        
        self.proceed_btn = MDRaisedButton(
            text="PROCEED",
            theme_text_color="Custom",
            text_color=TEXT_ON_PRIMARY,
            md_bg_color=PRIMARY_GREEN,
            size_hint=(0.45, 1),
            on_release=self._on_proceed,
        )
        self.preview_bar.add_widget(self.proceed_btn)
        
        layout.add_widget(self.preview_bar)
        
        self.add_widget(layout)
    
    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def _update_guides(self, instance, value):
        """Update positioning guide lines"""
        cx = instance.center_x
        cy = instance.center_y * 0.9
        w = instance.width * 0.7
        h = instance.height * 0.35
        gs = dp(30)
        
        # Top-left
        self.tl_h.points = [cx - w/2, cy + h/2, cx - w/2 + gs, cy + h/2]
        self.tl_v.points = [cx - w/2, cy + h/2, cx - w/2, cy + h/2 - gs]
        # Top-right
        self.tr_h.points = [cx + w/2, cy + h/2, cx + w/2 - gs, cy + h/2]
        self.tr_v.points = [cx + w/2, cy + h/2, cx + w/2, cy + h/2 - gs]
        # Bottom-left
        self.bl_h.points = [cx - w/2, cy - h/2, cx - w/2 + gs, cy - h/2]
        self.bl_v.points = [cx - w/2, cy - h/2, cx - w/2, cy - h/2 + gs]
        # Bottom-right
        self.br_h.points = [cx + w/2, cy - h/2, cx + w/2 - gs, cy - h/2]
        self.br_v.points = [cx + w/2, cy - h/2, cx + w/2, cy - h/2 + gs]
    
    def _start_camera(self):
        """Start camera preview"""
        try:
            self.capture = cv2.VideoCapture(0)
            if self.capture.isOpened():
                self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self._clock_event = Clock.schedule_interval(self._update_preview, 1.0 / 30.0)
        except Exception as e:
            print(f"Camera error: {e}")
            # Show placeholder
            self._show_camera_placeholder()
    
    def _stop_camera(self):
        """Stop camera preview"""
        if self._clock_event:
            self._clock_event.cancel()
            self._clock_event = None
        if self.capture:
            self.capture.release()
            self.capture = None
    
    def _update_preview(self, dt):
        """Update camera preview frame"""
        if self.capture and self.capture.isOpened():
            ret, frame = self.capture.read()
            if ret:
                # Flip horizontally for mirror effect
                frame = cv2.flip(frame, 1)
                # Convert to texture
                buf = cv2.flip(frame, 0).tobytes()
                texture = Texture.create(
                    size=(frame.shape[1], frame.shape[0]),
                    colorfmt='bgr'
                )
                texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
                self.preview.texture = texture
    
    def _show_camera_placeholder(self):
        """Show placeholder when camera unavailable"""
        placeholder = MDBoxLayout(
            orientation='vertical',
            spacing=dp(16),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
        )
        placeholder.add_widget(
            MDIconButton(
                icon="camera-off",
                theme_text_color="Custom",
                text_color=(*TEXT_ON_PRIMARY[:3], 0.5),
                user_font_size=sp(64),
                pos_hint={'center_x': 0.5},
            )
        )
        placeholder.add_widget(
            MDLabel(
                text="Camera not available\nTap to select from gallery",
                theme_text_color="Custom",
                text_color=(*TEXT_ON_PRIMARY[:3], 0.6),
                font_style="Body1",
                halign='center',
            )
        )
        # This would need to be added differently in a real implementation
    
    def _on_capture(self, instance):
        """Handle capture button"""
        if not self.has_image:
            self._capture_image()
        else:
            self._on_proceed(None)
    
    def _capture_image(self):
        """Capture image from camera or generate placeholder"""
        if self.capture and self.capture.isOpened():
            ret, frame = self.capture.read()
            if ret:
                self.captured_image = frame
                self._save_and_show_captured(frame)
        else:
            # Create a placeholder image for demo
            placeholder = np.random.randint(100, 200, (480, 640, 3), dtype=np.uint8)
            placeholder = cv2.GaussianBlur(placeholder, (15, 15), 0)
            # Add some realistic patterns
            cv2.circle(placeholder, (320, 240), 100, (120, 140, 100), -1)
            self.captured_image = placeholder
            self._save_and_show_captured(placeholder)
    
    def _save_and_show_captured(self, frame):
        """Save captured image and show preview"""
        # Save image
        filename = generate_filename("scan", "jpg")
        self.current_image_path = self.image_processor.save_image(frame, filename)
        
        # Show captured image
        buf = cv2.flip(frame, 0).tobytes()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
        texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        self.preview.texture = texture
        
        self.has_image = True
        self.preview_bar.opacity = 1
        self.capture_btn.icon = "check"
        self.capture_btn.md_bg_color = HEALTHY
    
    def _on_retake(self, instance):
        """Retake photo"""
        self.has_image = False
        self.captured_image = None
        self.preview_bar.opacity = 0
        self.capture_btn.icon = "camera"
        self.capture_btn.md_bg_color = PRIMARY_GREEN
        
        # Delete saved file
        if self.current_image_path and os.path.exists(self.current_image_path):
            os.remove(self.current_image_path)
        self.current_image_path = ""
    
    def _on_proceed(self, instance):
        """Proceed to processing"""
        if not self.current_image_path:
            DialogManager.show_error("No image captured")
            return
        
        # Pass data to processing screen
        processing_screen = self.manager.get_screen("processing")
        if processing_screen:
            processing_screen.set_image_path(self.current_image_path)
        
        self._stop_camera()
        self.manager.current = "processing"
    
    def _on_back(self, instance):
        """Go back to dashboard"""
        self._stop_camera()
        if self.manager:
            self.manager.current = "dashboard"
    
    def _toggle_flash(self, instance):
        """Toggle flash (placeholder)"""
        pass
    
    def _switch_camera(self, instance):
        """Switch between front/rear camera"""
        pass
    
    def _on_gallery(self, instance):
        """Open gallery to select image"""
        try:
            from plyer import filechooser
            filechooser.open_file(
                on_selection=self._on_gallery_selection,
                filters=[["Image files", "*.jpg", "*.jpeg", "*.png"]]
            )
        except ImportError:
            DialogManager.show_error("Gallery access not available")
    
    def _on_gallery_selection(self, selection):
        """Handle gallery image selection"""
        if selection:
            image_path = selection[0]
            frame = cv2.imread(image_path)
            if frame is not None:
                self.captured_image = frame
                self._save_and_show_captured(frame)
    
    def on_enter(self):
        """Start camera when entering"""
        self.has_image = False
        self.preview_bar.opacity = 0
        self.capture_btn.icon = "camera"
        self.capture_btn.md_bg_color = PRIMARY_GREEN
        self.current_image_path = ""
        Clock.schedule_once(lambda dt: self._start_camera(), 0.5)
    
    def on_leave(self):
        """Stop camera when leaving"""
        self._stop_camera()
