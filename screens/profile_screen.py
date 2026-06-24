"""
YamGuard - Profile Screen
User profile management and app settings
"""

from kivy.uix.screen import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, RoundedRectangle, Ellipse, Rectangle
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.properties import DictProperty

from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton, MDRaisedButton, MDTextButton, MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.list import MDList, OneLineIconListItem, IconLeftWidget
from kivymd.uix.selectioncontrol import MDCheckbox

from themes.colors import *
from utils.constants import APP_NAME, APP_VERSION
from utils.helpers import get_initials, format_datetime
from database.database import user_repo, activity_repo
from components.dialogs import DialogManager


class ProfileScreen(Screen):
    """User profile screen"""
    
    current_user = DictProperty({})
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "profile"
        self._setup_ui()
    
    def _setup_ui(self):
        layout = FloatLayout()
        
        # Background
        with layout.canvas.before:
            Color(*BACKGROUND[:3])
            self.bg_rect = Rectangle(pos=layout.pos, size=layout.size)
            Color(*PRIMARY_GREEN[:3])
            self.header_bg = RoundedRectangle(
                pos=layout.pos,
                size=(layout.size[0], dp(200)),
                radius=[0, 0, dp(30), dp(30)]
            )
        layout.bind(pos=self._update_bg, size=self._update_bg)
        
        # Header
        header = MDTopAppBar(
            title="Profile",
            type="small",
            elevation=0,
            md_bg_color=(0, 0, 0, 0),
            specific_text_color=TEXT_ON_PRIMARY,
            left_action_items=[["arrow-left", lambda x: self._on_back()]],
            right_action_items=[["pencil", lambda x: self._on_edit()]],
        )
        layout.add_widget(header)
        
        # Profile card
        profile_card = MDCard(
            orientation='vertical',
            spacing=dp(16),
            padding=dp(20),
            size_hint=(0.9, None),
            height=dp(280),
            pos_hint={'center_x': 0.5, 'center_y': 0.72},
            radius=[dp(20), dp(20), dp(20), dp(20)],
            elevation=4,
        )
        
        # Avatar
        avatar = MDBoxLayout(
            size_hint=(None, None),
            size=(dp(80), dp(80)),
            pos_hint={'center_x': 0.5},
        )
        with avatar.canvas:
            Color(*PRIMARY_GREEN[:3])
            self.avatar_circle = Ellipse(
                pos=(avatar.x, avatar.y),
                size=(dp(80), dp(80))
            )
        avatar.bind(pos=self._update_avatar, size=self._update_avatar)
        
        self.avatar_label = MDLabel(
            text="YG",
            theme_text_color="Custom",
            text_color=TEXT_ON_PRIMARY,
            font_style="H4",
            bold=True,
            halign='center',
            valign='center',
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
        )
        avatar.add_widget(self.avatar_label)
        profile_card.add_widget(avatar)
        
        # User info
        self.name_label = MDLabel(
            text="User Name",
            theme_text_color="Primary",
            font_style="H5",
            bold=True,
            halign='center',
            size_hint_y=None,
            height=dp(32),
        )
        profile_card.add_widget(self.name_label)
        
        self.email_label = MDLabel(
            text="user@example.com",
            theme_text_color="Secondary",
            font_style="Body2",
            halign='center',
            size_hint_y=None,
            height=dp(24),
        )
        profile_card.add_widget(self.email_label)
        
        self.role_label = MDLabel(
            text="Farmer",
            theme_text_color="Custom",
            text_color=PRIMARY_GREEN,
            font_style="Caption",
            bold=True,
            halign='center',
            size_hint_y=None,
            height=dp(20),
        )
        profile_card.add_widget(self.role_label)
        
        layout.add_widget(profile_card)
        
        # Settings section
        settings_card = MDCard(
            orientation='vertical',
            spacing=dp(4),
            padding=dp(16),
            size_hint=(0.9, None),
            height=dp(280),
            pos_hint={'center_x': 0.5, 'center_y': 0.35},
            radius=[dp(16), dp(16), dp(16), dp(16)],
            elevation=2,
        )
        
        settings_card.add_widget(
            MDLabel(
                text="SETTINGS",
                theme_text_color="Secondary",
                font_style="Overline",
                bold=True,
                size_hint_y=None,
                height=dp(24),
            )
        )
        
        # Settings list
        settings_list = MDList()
        
        # Account settings
        item1 = OneLineIconListItem(
            text="Edit Profile",
            on_release=self._on_edit,
        )
        item1.add_widget(IconLeftWidget(icon="account-edit"))
        settings_list.add_widget(item1)
        
        # Change password
        item2 = OneLineIconListItem(
            text="Change Password",
            on_release=self._on_change_password,
        )
        item2.add_widget(IconLeftWidget(icon="lock-reset"))
        settings_list.add_widget(item2)
        
        # Notifications
        item3 = OneLineIconListItem(
            text="Notifications",
            on_release=self._on_notifications,
        )
        item3.add_widget(IconLeftWidget(icon="bell-outline"))
        settings_list.add_widget(item3)
        
        # About
        item4 = OneLineIconListItem(
            text="About",
            on_release=self._on_about,
        )
        item4.add_widget(IconLeftWidget(icon="information"))
        settings_list.add_widget(item4)
        
        settings_card.add_widget(settings_list)
        layout.add_widget(settings_card)
        
        # Logout button
        layout.add_widget(
            MDTextButton(
                text="SIGN OUT",
                theme_text_color="Custom",
                text_color=INFECTED,
                font_style="Button",
                pos_hint={'center_x': 0.5, 'y': 0.08},
                on_release=self._on_logout,
            )
        )
        
        # Version info
        layout.add_widget(
            MDLabel(
                text=f"{APP_NAME} v{APP_VERSION}",
                theme_text_color="Secondary",
                font_style="Caption",
                halign='center',
                size_hint_y=None,
                height=dp(20),
                pos_hint={'center_x': 0.5, 'y': 0.02},
            )
        )
        
        # Edit profile form (initially hidden)
        self.edit_form = MDCard(
            orientation='vertical',
            spacing=dp(12),
            padding=dp(20),
            size_hint=(0.9, None),
            height=dp(350),
            pos_hint={'center_x': 0.5, 'center_y': 0.55},
            radius=[dp(20), dp(20), dp(20), dp(20)],
            elevation=6,
            opacity=0,
            disabled=True,
        )
        
        self.edit_form.add_widget(
            MDLabel(
                text="Edit Profile",
                theme_text_color="Primary",
                font_style="H6",
                bold=True,
                size_hint_y=None,
                height=dp(30),
            )
        )
        
        self.edit_name = MDTextField(
            hint_text="Full Name",
            icon_left="account",
            mode="rectangle",
            size_hint_y=None,
            height=dp(48),
        )
        self.edit_form.add_widget(self.edit_name)
        
        self.edit_phone = MDTextField(
            hint_text="Phone Number",
            icon_left="phone",
            mode="rectangle",
            size_hint_y=None,
            height=dp(48),
        )
        self.edit_form.add_widget(self.edit_phone)
        
        self.edit_org = MDTextField(
            hint_text="Organization",
            icon_left="office-building",
            mode="rectangle",
            size_hint_y=None,
            height=dp(48),
        )
        self.edit_form.add_widget(self.edit_org)
        
        edit_actions = MDBoxLayout(
            orientation='horizontal',
            spacing=dp(12),
            size_hint_y=None,
            height=dp(40),
        )
        edit_actions.add_widget(
            MDFlatButton(
                text="CANCEL",
                theme_text_color="Custom",
                text_color=TEXT_SECONDARY,
                on_release=self._on_cancel_edit,
            )
        )
        edit_actions.add_widget(
            MDRaisedButton(
                text="SAVE",
                theme_text_color="Custom",
                text_color=TEXT_ON_PRIMARY,
                md_bg_color=PRIMARY_GREEN,
                on_release=self._on_save_edit,
            )
        )
        self.edit_form.add_widget(edit_actions)
        
        layout.add_widget(self.edit_form)
        
        self.add_widget(layout)
    
    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
        self.header_bg.pos = instance.pos
        self.header_bg.size = (instance.size[0], dp(200))
    
    def _update_avatar(self, instance, value):
        self.avatar_circle.pos = instance.pos
        self.avatar_circle.size = instance.size
    
    def load_profile(self):
        """Load user profile data"""
        user = self.current_user
        
        name = user.get('fullname', 'User')
        self.name_label.text = name
        self.avatar_label.text = get_initials(name)
        
        self.email_label.text = user.get('email', '')
        self.role_label.text = user.get('role', 'Farmer').capitalize()
        
        # Pre-fill edit form
        self.edit_name.text = name
        self.edit_phone.text = user.get('phone', '')
        self.edit_org.text = user.get('organization', '')
    
    def _on_edit(self, *args):
        """Show edit form"""
        self.edit_form.opacity = 1
        self.edit_form.disabled = False
    
    def _on_cancel_edit(self, *args):
        """Hide edit form"""
        self.edit_form.opacity = 0
        self.edit_form.disabled = True
    
    def _on_save_edit(self, *args):
        """Save profile changes"""
        user_id = self.current_user.get('id')
        if not user_id:
            return
        
        updates = {
            'fullname': self.edit_name.text.strip(),
            'phone': self.edit_phone.text.strip(),
            'organization': self.edit_org.text.strip(),
        }
        
        if user_repo.update_user(user_id, **updates):
            # Update current user
            self.current_user.update(updates)
            self.load_profile()
            self._on_cancel_edit()
            DialogManager.show_success("Profile updated successfully")
        else:
            DialogManager.show_error("Failed to update profile")
    
    def _on_change_password(self, *args):
        """Show change password dialog"""
        DialogManager.show_alert(
            "Change Password",
            "Password change functionality will be implemented in a future update."
        )
    
    def _on_notifications(self, *args):
        """Show notification settings"""
        DialogManager.show_alert(
            "Notifications",
            "Notification settings will be implemented in a future update."
        )
    
    def _on_about(self, *args):
        """Show about dialog"""
        DialogManager.show_alert(
            f"About {APP_NAME}",
            f"{APP_NAME} v{APP_VERSION}\n\n"
            "Smartphone-Based Hyperspectral Imaging System\n"
            "for Early Detection of Fungal Infection\n"
            "in Yam Tubers Using Machine Learning\n\n"
            "Built with KivyMD and Python."
        )
    
    def _on_logout(self, *args):
        """Sign out user"""
        DialogManager.show_confirm(
            "Sign Out",
            "Are you sure you want to sign out?",
            on_confirm=self._do_logout,
        )
    
    def _do_logout(self):
        """Perform logout"""
        app = self.manager.parent
        if hasattr(app, 'clear_current_user'):
            app.clear_current_user()
        
        if self.manager:
            self.manager.current = "login"
    
    def _on_back(self):
        """Go back to dashboard"""
        if self.manager:
            self.manager.current = "dashboard"
    
    def on_enter(self):
        """Load profile on enter"""
        Clock.schedule_once(lambda dt: self.load_profile(), 0.1)
