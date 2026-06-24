"""
YamGuard - Login Screen
User authentication with email and password
"""

from kivy.uix.screen import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.properties import StringProperty, BooleanProperty
from kivy.metrics import dp, sp
from kivy.animation import Animation
from kivy.clock import Clock

from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDFlatButton, MDRaisedButton, MDIconButton, MDTextButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.snackbar import MDSnackbar

from themes.colors import *
from utils.constants import APP_NAME
from utils.validators import FormValidator
from database.database import user_repo
from components.dialogs import DialogManager


class LoginScreen(Screen):
    """Login screen with authentication"""
    
    email = StringProperty("")
    password = StringProperty("")
    remember_me = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "login"
        self.validator = FormValidator()
        self._setup_ui()
    
    def _setup_ui(self):
        layout = FloatLayout()
        
        # Background
        with layout.canvas.before:
            # Gradient-like background using two rectangles
            Color(*BACKGROUND[:3])
            self.bg_rect = Rectangle(pos=layout.pos, size=layout.size)
            Color(*PRIMARY_GREEN[:3])
            self.header_rect = RoundedRectangle(
                pos=layout.pos,
                size=(layout.size[0], dp(280)),
                radius=[0, 0, dp(30), dp(30)]
            )
        layout.bind(pos=self._update_bg, size=self._update_bg)
        
        # Top section with branding
        header = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            size_hint=(1, None),
            height=dp(250),
            pos_hint={'top': 1},
            padding=[0, dp(40), 0, 0],
        )
        
        # App name
        header.add_widget(
            MDLabel(
                text=APP_NAME,
                theme_text_color="Custom",
                text_color=TEXT_ON_PRIMARY,
                font_style="H2",
                bold=True,
                halign='center',
                size_hint_y=None,
                height=dp(50),
            )
        )
        
        # Tagline
        header.add_widget(
            MDLabel(
                text="Smart Agriculture AI",
                theme_text_color="Custom",
                text_color=(*TEXT_ON_PRIMARY[:3], 0.8),
                font_style="Subtitle1",
                halign='center',
                size_hint_y=None,
                height=dp(30),
            )
        )
        
        # Shield icon (using text as icon)
        header.add_widget(
            MDIconButton(
                icon="shield-check",
                theme_text_color="Custom",
                text_color=(*TEXT_ON_PRIMARY[:3], 0.9),
                user_font_size=sp(48),
                size_hint=(None, None),
                size=(dp(80), dp(80)),
                pos_hint={'center_x': 0.5},
            )
        )
        
        layout.add_widget(header)
        
        # Login card
        login_card = MDCard(
            orientation='vertical',
            spacing=dp(16),
            padding=dp(24),
            size_hint=(0.9, None),
            height=dp(380),
            pos_hint={'center_x': 0.5, 'center_y': 0.38},
            radius=[dp(20), dp(20), dp(20), dp(20)],
            elevation=4,
            shadow_softness=12,
        )
        
        # Login title
        login_card.add_widget(
            MDLabel(
                text="Welcome Back",
                theme_text_color="Primary",
                font_style="H5",
                bold=True,
                halign='left',
                size_hint_y=None,
                height=dp(40),
            )
        )
        
        login_card.add_widget(
            MDLabel(
                text="Sign in to continue",
                theme_text_color="Secondary",
                font_style="Caption",
                halign='left',
                size_hint_y=None,
                height=dp(20),
            )
        )
        
        # Email field
        self.email_field = MDTextField(
            hint_text="Email Address",
            icon_left="email",
            mode="rectangle",
            size_hint_y=None,
            height=dp(50),
            helper_text_mode="on_error",
        )
        login_card.add_widget(self.email_field)
        
        # Password field
        self.password_field = MDTextField(
            hint_text="Password",
            icon_left="lock",
            password=True,
            mode="rectangle",
            size_hint_y=None,
            height=dp(50),
            helper_text_mode="on_error",
        )
        login_card.add_widget(self.password_field)
        
        # Remember me and forgot password row
        options_row = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(36),
        )
        
        remember_box = MDBoxLayout(
            size_hint_x=0.5,
            spacing=dp(4),
        )
        self.remember_checkbox = MDCheckbox(
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            pos_hint={'center_y': 0.5},
        )
        remember_box.add_widget(self.remember_checkbox)
        remember_box.add_widget(
            MDLabel(
                text="Remember Me",
                theme_text_color="Secondary",
                font_style="Caption",
                pos_hint={'center_y': 0.5},
            )
        )
        options_row.add_widget(remember_box)
        
        forgot_btn = MDTextButton(
            text="Forgot Password?",
            theme_text_color="Custom",
            text_color=PRIMARY_GREEN,
            font_style="Caption",
            pos_hint={'center_y': 0.5, 'right': 1},
            size_hint_x=0.5,
            on_release=self._on_forgot_password,
        )
        options_row.add_widget(forgot_btn)
        
        login_card.add_widget(options_row)
        
        # Login button
        self.login_button = MDRaisedButton(
            text="SIGN IN",
            theme_text_color="Custom",
            text_color=TEXT_ON_PRIMARY,
            md_bg_color=PRIMARY_GREEN,
            size_hint=(1, None),
            height=dp(48),
            pos_hint={'center_x': 0.5},
            radius=[dp(8), dp(8), dp(8), dp(8)],
            font_style="Button",
            on_release=self._on_login,
        )
        login_card.add_widget(self.login_button)
        
        layout.add_widget(login_card)
        
        # Register link at bottom
        register_box = MDBoxLayout(
            size_hint=(None, None),
            size=(dp(250), dp(40)),
            pos_hint={'center_x': 0.5, 'y': 0.05},
        )
        register_box.add_widget(
            MDLabel(
                text="Don't have an account?",
                theme_text_color="Secondary",
                font_style="Caption",
                halign='right',
                pos_hint={'center_y': 0.5},
            )
        )
        register_box.add_widget(
            MDTextButton(
                text="Register",
                theme_text_color="Custom",
                text_color=PRIMARY_GREEN,
                font_style="Caption",
                bold=True,
                pos_hint={'center_y': 0.5},
                on_release=self._on_register,
            )
        )
        layout.add_widget(register_box)
        
        self.add_widget(layout)
    
    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
        self.header_rect.pos = instance.pos
        self.header_rect.size = (instance.size[0], dp(280))
    
    def _on_login(self, instance):
        """Handle login button press"""
        email = self.email_field.text.strip()
        password = self.password_field.text
        
        # Validate
        if not self.validator.validate_login(email, password):
            errors = self.validator.errors
            if 'email' in errors:
                self.email_field.error = True
                self.email_field.helper_text = errors['email']
            if 'password' in errors:
                self.password_field.error = True
                self.password_field.helper_text = errors['password']
            return
        
        # Clear errors
        self.email_field.error = False
        self.password_field.error = False
        
        # Attempt authentication
        user = user_repo.authenticate_user(email, password)
        
        if user:
            # Store user session
            app = self.manager.parent
            if hasattr(app, 'set_current_user'):
                app.set_current_user(user)
            
            DialogManager.show_success("Login successful!")
            Clock.schedule_once(lambda dt: self._navigate_to_dashboard(), 0.5)
        else:
            DialogManager.show_error("Invalid email or password. Please try again.")
    
    def _navigate_to_dashboard(self):
        """Navigate to dashboard screen"""
        if self.manager:
            self.manager.current = "dashboard"
            # Clear password field
            self.password_field.text = ""
    
    def _on_register(self, instance):
        """Navigate to registration screen"""
        if self.manager:
            self.manager.current = "register"
    
    def _on_forgot_password(self, instance):
        """Show forgot password dialog"""
        DialogManager.show_alert(
            "Forgot Password",
            "Please contact your system administrator to reset your password."
        )
    
    def on_enter(self):
        """Reset fields when entering screen"""
        self.email_field.text = ""
        self.password_field.text = ""
        self.email_field.error = False
        self.password_field.error = False
        self.remember_checkbox.active = False
