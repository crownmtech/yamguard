"""
YamGuard - Registration Screen
User account creation with validation
"""

from kivy.uix.screen import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.clock import Clock

from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDTextButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.menu import MDDropdownMenu

from themes.colors import *
from utils.constants import APP_NAME, USER_ROLES
from utils.validators import FormValidator
from database.database import user_repo
from components.dialogs import DialogManager


class RegisterScreen(Screen):
    """User registration screen"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "register"
        self.validator = FormValidator()
        self.menu = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = FloatLayout()
        
        # Background
        with layout.canvas.before:
            Color(*BACKGROUND[:3])
            self.bg_rect = Rectangle(pos=layout.pos, size=layout.size)
            Color(*PRIMARY_GREEN[:3])
            self.header_rect = RoundedRectangle(
                pos=layout.pos,
                size=(layout.size[0], dp(200)),
                radius=[0, 0, dp(30), dp(30)]
            )
        layout.bind(pos=self._update_bg, size=self._update_bg)
        
        # Header
        header = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            size_hint=(1, None),
            height=dp(180),
            pos_hint={'top': 1},
            padding=[0, dp(30), 0, 0],
        )
        
        header.add_widget(
            MDIconButton(
                icon="arrow-left",
                theme_text_color="Custom",
                text_color=TEXT_ON_PRIMARY,
                pos_hint={'x': 0.05},
                on_release=self._on_back,
            )
        )
        
        header.add_widget(
            MDLabel(
                text="Create Account",
                theme_text_color="Custom",
                text_color=TEXT_ON_PRIMARY,
                font_style="H4",
                bold=True,
                halign='center',
                size_hint_y=None,
                height=dp(40),
            )
        )
        
        header.add_widget(
            MDLabel(
                text="Join YamGuard to protect your crops",
                theme_text_color="Custom",
                text_color=(*TEXT_ON_PRIMARY[:3], 0.8),
                font_style="Subtitle1",
                halign='center',
                size_hint_y=None,
                height=dp(30),
            )
        )
        
        layout.add_widget(header)
        
        # Registration card
        card = MDCard(
            orientation='vertical',
            spacing=dp(12),
            padding=dp(20),
            size_hint=(0.92, None),
            height=dp(480),
            pos_hint={'center_x': 0.5, 'center_y': 0.42},
            radius=[dp(20), dp(20), dp(20), dp(20)],
            elevation=4,
        )
        
        # Full name
        self.fullname_field = MDTextField(
            hint_text="Full Name",
            icon_left="account",
            mode="rectangle",
            size_hint_y=None,
            height=dp(48),
            helper_text_mode="on_error",
        )
        card.add_widget(self.fullname_field)
        
        # Email
        self.email_field = MDTextField(
            hint_text="Email Address",
            icon_left="email",
            mode="rectangle",
            size_hint_y=None,
            height=dp(48),
            helper_text_mode="on_error",
        )
        card.add_widget(self.email_field)
        
        # Password
        self.password_field = MDTextField(
            hint_text="Password",
            icon_left="lock",
            password=True,
            mode="rectangle",
            size_hint_y=None,
            height=dp(48),
            helper_text_mode="on_error",
        )
        card.add_widget(self.password_field)
        
        # Confirm password
        self.confirm_field = MDTextField(
            hint_text="Confirm Password",
            icon_left="lock-check",
            password=True,
            mode="rectangle",
            size_hint_y=None,
            height=dp(48),
            helper_text_mode="on_error",
        )
        card.add_widget(self.confirm_field)
        
        # Role selection
        self.role_field = MDTextField(
            hint_text="Select Role",
            icon_left="account-tie",
            mode="rectangle",
            size_hint_y=None,
            height=dp(48),
            readonly=True,
            on_focus=self._show_role_menu,
        )
        card.add_widget(self.role_field)
        
        # Role menu
        role_items = [
            {"viewclass": "OneLineListItem", "text": role_name,
             "on_release": lambda x=role_key: self._set_role(x)}
            for role_key, role_name in USER_ROLES.items()
        ]
        self.menu = MDDropdownMenu(
            caller=self.role_field,
            items=role_items,
            width_mult=4,
            max_height=dp(200),
        )
        
        # Register button
        self.register_btn = MDRaisedButton(
            text="CREATE ACCOUNT",
            theme_text_color="Custom",
            text_color=TEXT_ON_PRIMARY,
            md_bg_color=PRIMARY_GREEN,
            size_hint=(1, None),
            height=dp(48),
            pos_hint={'center_x': 0.5},
            radius=[dp(8), dp(8), dp(8), dp(8)],
            on_release=self._on_register,
        )
        card.add_widget(self.register_btn)
        
        # Login link
        login_row = MDBoxLayout(
            size_hint_y=None,
            height=dp(36),
            padding=[0, dp(8), 0, 0],
        )
        login_row.add_widget(
            MDLabel(
                text="Already have an account?",
                theme_text_color="Secondary",
                font_style="Caption",
                halign='right',
                pos_hint={'center_y': 0.5},
            )
        )
        login_row.add_widget(
            MDTextButton(
                text="Sign In",
                theme_text_color="Custom",
                text_color=PRIMARY_GREEN,
                font_style="Caption",
                bold=True,
                pos_hint={'center_y': 0.5},
                on_release=self._on_login,
            )
        )
        card.add_widget(login_row)
        
        layout.add_widget(card)
        self.add_widget(layout)
    
    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
        self.header_rect.pos = instance.pos
        self.header_rect.size = (instance.size[0], dp(200))
    
    def _show_role_menu(self, instance, focus):
        if focus:
            self.menu.open()
    
    def _set_role(self, role_key):
        self.role_field.text = USER_ROLES.get(role_key, "")
        self.selected_role = role_key
        self.menu.dismiss()
    
    def _on_register(self, instance):
        """Handle registration"""
        fullname = self.fullname_field.text.strip()
        email = self.email_field.text.strip()
        password = self.password_field.text
        confirm = self.confirm_field.text
        role = getattr(self, 'selected_role', 'farmer')
        
        # Clear previous errors
        for field in [self.fullname_field, self.email_field, self.password_field, self.confirm_field]:
            field.error = False
        
        # Validate
        if not self.validator.validate_registration(fullname, email, password, confirm, role):
            errors = self.validator.errors
            if 'fullname' in errors:
                self.fullname_field.error = True
                self.fullname_field.helper_text = errors['fullname']
            if 'email' in errors:
                self.email_field.error = True
                self.email_field.helper_text = errors['email']
            if 'password' in errors:
                self.password_field.error = True
                self.password_field.helper_text = errors['password']
            if 'confirm_password' in errors:
                self.confirm_field.error = True
                self.confirm_field.helper_text = errors['confirm_password']
            return
        
        # Create user
        user_id = user_repo.create_user(fullname, email, password, role)
        
        if user_id:
            DialogManager.show_success(
                "Account created successfully! You can now sign in.",
                title="Welcome!"
            )
            Clock.schedule_once(lambda dt: self._on_back(None), 1.5)
        else:
            DialogManager.show_error(
                "An account with this email already exists. Please use a different email."
            )
    
    def _on_back(self, instance):
        """Go back to login"""
        if self.manager:
            self.manager.current = "login"
    
    def _on_login(self, instance):
        """Navigate to login"""
        self._on_back(instance)
    
    def on_enter(self):
        """Clear fields on enter"""
        self.fullname_field.text = ""
        self.email_field.text = ""
        self.password_field.text = ""
        self.confirm_field.text = ""
        self.role_field.text = ""
        self.selected_role = "farmer"
        for field in [self.fullname_field, self.email_field, self.password_field, self.confirm_field]:
            field.error = False
