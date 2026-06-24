"""
YamGuard - Dialog Components
Custom dialogs for the application
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import StringProperty, NumericProperty, ColorProperty
from kivy.metrics import dp, sp
from kivy.clock import Clock

from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton, MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField
from kivymd.uix.selectioncontrol import MDCheckbox

from themes.colors import *


class DialogManager:
    """Central dialog manager"""
    
    _current_dialog = None
    
    @classmethod
    def dismiss_current(cls):
        if cls._current_dialog:
            cls._current_dialog.dismiss()
            cls._current_dialog = None
    
    @classmethod
    def show_alert(cls, title: str, message: str, on_dismiss=None):
        cls.dismiss_current()
        cls._current_dialog = MDDialog(
            title=title,
            text=message,
            radius=[dp(16), dp(16), dp(16), dp(16)],
            buttons=[
                MDRaisedButton(
                    text="OK",
                    theme_text_color="Custom",
                    text_color=TEXT_ON_PRIMARY,
                    md_bg_color=PRIMARY_GREEN,
                    on_release=lambda x: cls.dismiss_current(),
                )
            ],
            on_dismiss=on_dismiss,
        )
        cls._current_dialog.open()
        return cls._current_dialog
    
    @classmethod
    def show_confirm(cls, title: str, message: str, 
                     on_confirm=None, on_cancel=None):
        cls.dismiss_current()
        cls._current_dialog = MDDialog(
            title=title,
            text=message,
            radius=[dp(16), dp(16), dp(16), dp(16)],
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    theme_text_color="Custom",
                    text_color=TEXT_SECONDARY,
                    on_release=lambda x: (cls.dismiss_current(), on_cancel() if on_cancel else None),
                ),
                MDRaisedButton(
                    text="CONFIRM",
                    theme_text_color="Custom",
                    text_color=TEXT_ON_PRIMARY,
                    md_bg_color=PRIMARY_GREEN,
                    on_release=lambda x: (cls.dismiss_current(), on_confirm() if on_confirm else None),
                ),
            ],
        )
        cls._current_dialog.open()
        return cls._current_dialog
    
    @classmethod
    def show_error(cls, message: str, title: str = "Error"):
        return cls.show_alert(title, message)
    
    @classmethod
    def show_success(cls, message: str, title: str = "Success"):
        return cls.show_alert(title, message)
    
    @classmethod
    def show_loading(cls, message: str = "Processing..."):
        cls.dismiss_current()
        
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(16),
            padding=dp(16),
            size_hint_y=None,
            height=dp(100),
        )
        
        content.add_widget(
            MDLabel(
                text=message,
                theme_text_color="Primary",
                font_style="Body1",
                halign='center',
            )
        )
        
        progress = MDProgressBar(
            color=PRIMARY_GREEN,
            back_color=BORDER,
            type="indeterminate",
        )
        content.add_widget(progress)
        
        cls._current_dialog = MDDialog(
            content_cls=content,
            radius=[dp(16), dp(16), dp(16), dp(16)],
            size_hint=(0.8, None),
        )
        cls._current_dialog.open()
        return cls._current_dialog
    
    @classmethod
    def show_progress(cls, title: str = "Processing", message: str = ""):
        cls.dismiss_current()
        
        content = ProgressDialogContent(title=title, message=message)
        
        cls._current_dialog = MDDialog(
            content_cls=content,
            radius=[dp(16), dp(16), dp(16), dp(16)],
            size_hint=(0.85, None),
        )
        cls._current_dialog.open()
        return cls._current_dialog, content


class ProgressDialogContent(MDBoxLayout):
    """Custom progress dialog content"""
    
    def __init__(self, title: str = "", message: str = "", **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = dp(12)
        self.padding = dp(8)
        self.size_hint_y = None
        self.height = dp(150)
        
        self.title_label = MDLabel(
            text=title,
            theme_text_color="Primary",
            font_style="H6",
            bold=True,
            halign='center',
            size_hint_y=None,
            height=dp(30),
        )
        self.add_widget(self.title_label)
        
        self.message_label = MDLabel(
            text=message,
            theme_text_color="Secondary",
            font_style="Body2",
            halign='center',
            size_hint_y=None,
            height=dp(24),
        )
        self.add_widget(self.message_label)
        
        self.progress_bar = MDProgressBar(
            value=0,
            color=PRIMARY_GREEN,
            back_color=BORDER,
            size_hint_y=None,
            height=dp(8),
        )
        self.add_widget(self.progress_bar)
        
        self.percentage_label = MDLabel(
            text="0%",
            theme_text_color="Primary",
            font_style="H6",
            bold=True,
            halign='center',
            size_hint_y=None,
            height=dp(30),
        )
        self.add_widget(self.percentage_label)
    
    def set_progress(self, value: float, message: str = ""):
        """Update progress value (0-100)"""
        self.progress_bar.value = value
        self.percentage_label.text = f"{value:.0f}%"
        if message:
            self.message_label.text = message
    
    def set_title(self, title: str):
        self.title_label.text = title


class FilterDialogContent(MDBoxLayout):
    """Content for filter dialog"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = dp(8)
        self.padding = dp(8)
        self.size_hint_y = None
        self.height = dp(250)
        
        # Date range
        self.add_widget(MDLabel(text="Date Range", theme_text_color="Secondary", font_style="Overline", bold=True))
        
        date_box = MDBoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(48))
        self.date_from = MDTextField(
            hint_text="From (YYYY-MM-DD)",
            size_hint_x=0.5,
        )
        self.date_to = MDTextField(
            hint_text="To (YYYY-MM-DD)",
            size_hint_x=0.5,
        )
        date_box.add_widget(self.date_from)
        date_box.add_widget(self.date_to)
        self.add_widget(date_box)
        
        # Status filter
        self.add_widget(MDLabel(text="Status", theme_text_color="Secondary", font_style="Overline", bold=True, size_hint_y=None, height=dp(30)))
        
        status_box = MDBoxLayout(orientation='vertical', spacing=dp(4))
        self.status_all = self._create_checkbox("All", True)
        self.status_healthy = self._create_checkbox("Healthy", False)
        self.status_infected = self._create_checkbox("Infected", False)
        status_box.add_widget(self.status_all)
        status_box.add_widget(self.status_healthy)
        status_box.add_widget(self.status_infected)
        self.add_widget(status_box)
    
    def _create_checkbox(self, text: str, active: bool) -> MDBoxLayout:
        box = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(36))
        checkbox = MDCheckbox(size_hint=(None, None), size=(dp(32), dp(32)), active=active)
        checkbox.status_text = text
        box.add_widget(checkbox)
        box.add_widget(MDLabel(text=text, theme_text_color="Primary", font_style="Body2", pos_hint={'center_y': 0.5}))
        return box
    
    def get_filters(self) -> dict:
        """Get selected filter values"""
        status = "all"
        if self.status_healthy.children[1].active:
            status = "healthy"
        elif self.status_infected.children[1].active:
            status = "infected"
        
        return {
            'date_from': self.date_from.text,
            'date_to': self.date_to.text,
            'status': status,
        }


class ReportConfigDialogContent(MDBoxLayout):
    """Content for report configuration dialog"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = dp(12)
        self.padding = dp(8)
        self.size_hint_y = None
        self.height = dp(300)
        
        # Report title
        self.title_field = MDTextField(
            hint_text="Report Title",
            text="YamGuard Diagnostic Report",
        )
        self.add_widget(self.title_field)
        
        # Date range
        date_box = MDBoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(48))
        self.date_from = MDTextField(
            hint_text="From (YYYY-MM-DD)",
            size_hint_x=0.5,
        )
        self.date_to = MDTextField(
            hint_text="To (YYYY-MM-DD)",
            size_hint_x=0.5,
        )
        date_box.add_widget(self.date_from)
        date_box.add_widget(self.date_to)
        self.add_widget(date_box)
        
        # Classification filter
        self.add_widget(MDLabel(
            text="Include Classifications",
            theme_text_color="Secondary",
            font_style="Overline",
            bold=True,
            size_hint_y=None,
            height=dp(24),
        ))
        
        filter_box = MDBoxLayout(orientation='vertical', spacing=dp(4))
        self.include_healthy = self._create_checkbox("Healthy", True)
        self.include_infected = self._create_checkbox("Infected", True)
        filter_box.add_widget(self.include_healthy)
        filter_box.add_widget(self.include_infected)
        self.add_widget(filter_box)
        
        # Comments
        self.comments_field = MDTextField(
            hint_text="Additional Comments (optional)",
            multiline=True,
            size_hint_y=None,
            height=dp(60),
        )
        self.add_widget(self.comments_field)
    
    def _create_checkbox(self, text: str, active: bool) -> MDBoxLayout:
        box = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(36))
        checkbox = MDCheckbox(size_hint=(None, None), size=(dp(32), dp(32)), active=active)
        box.add_widget(checkbox)
        box.add_widget(MDLabel(text=text, theme_text_color="Primary", font_style="Body2", pos_hint={'center_y': 0.5}))
        box.checkbox = checkbox
        return box
    
    def get_config(self) -> dict:
        """Get report configuration"""
        return {
            'title': self.title_field.text,
            'date_from': self.date_from.text,
            'date_to': self.date_to.text,
            'include_healthy': self.include_healthy.checkbox.active,
            'include_infected': self.include_infected.checkbox.active,
            'comments': self.comments_field.text,
        }
