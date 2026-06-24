"""
YamGuard - Report Screen
Generate and manage diagnostic reports
"""

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
from kivymd.uix.gridlayout import MDGridLayout

from themes.colors import *
from utils.helpers import format_datetime, get_date_range
from database.database import scan_repo, report_repo
from components.charts import TrendChart, DistributionChart
from components.dialogs import DialogManager, ReportConfigDialogContent
from reports.report_generator import get_report_generator


class ReportScreen(Screen):
    """Report generation and management screen"""
    
    current_user = DictProperty({})
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "report"
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
            title="Reports",
            type="small",
            elevation=4,
            md_bg_color=PRIMARY_GREEN,
            specific_text_color=TEXT_ON_PRIMARY,
            left_action_items=[["arrow-left", lambda x: self._on_back()]],
            right_action_items=[["plus", lambda x: self._on_new_report()]],
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
        
        # Statistics section
        content.add_widget(
            MDLabel(
                text="SUMMARY STATISTICS",
                theme_text_color="Secondary",
                font_style="Overline",
                bold=True,
                size_hint_y=None,
                height=dp(24),
            )
        )
        
        # Stats cards
        stats_grid = MDGridLayout(
            cols=2,
            spacing=dp(12),
            size_hint_y=None,
            height=dp(120),
        )
        
        self.total_scans_card = MDCard(
            orientation='vertical',
            padding=dp(12),
            radius=[dp(12)] * 4,
            elevation=1,
        )
        self.total_scans_card.add_widget(MDLabel(text="Total Scans", theme_text_color="Secondary", font_style="Caption", halign='center'))
        self.total_scans_value = MDLabel(text="0", theme_text_color="Primary", font_style="H4", bold=True, halign='center')
        self.total_scans_card.add_widget(self.total_scans_value)
        stats_grid.add_widget(self.total_scans_card)
        
        self.infection_rate_card = MDCard(
            orientation='vertical',
            padding=dp(12),
            radius=[dp(12)] * 4,
            elevation=1,
        )
        self.infection_rate_card.add_widget(MDLabel(text="Infection Rate", theme_text_color="Secondary", font_style="Caption", halign='center'))
        self.infection_rate_value = MDLabel(text="0.0%", theme_text_color="Custom", text_color=INFECTED, font_style="H4", bold=True, halign='center')
        self.infection_rate_card.add_widget(self.infection_rate_value)
        stats_grid.add_widget(self.infection_rate_card)
        
        content.add_widget(stats_grid)
        
        # Charts
        content.add_widget(
            MDLabel(
                text="VISUAL ANALYSIS",
                theme_text_color="Secondary",
                font_style="Overline",
                bold=True,
                size_hint_y=None,
                height=dp(24),
            )
        )
        
        charts_box = MDBoxLayout(
            orientation='vertical',
            spacing=dp(12),
            size_hint_y=None,
            height=dp(360),
        )
        
        # Trend chart
        self.trend_chart = TrendChart(
            size_hint_y=None,
            height=dp(180),
        )
        charts_box.add_widget(self.trend_chart)
        
        # Distribution chart
        self.dist_chart = DistributionChart(
            size_hint_y=None,
            height=dp(180),
            chart_type="donut",
        )
        charts_box.add_widget(self.dist_chart)
        
        content.add_widget(charts_box)
        
        # Generate report button
        content.add_widget(
            MDRaisedButton(
                text="GENERATE PDF REPORT",
                icon="file-pdf-box",
                theme_text_color="Custom",
                text_color=TEXT_ON_PRIMARY,
                md_bg_color=PRIMARY_GREEN,
                size_hint=(1, None),
                height=dp(50),
                pos_hint={'center_x': 0.5},
                radius=[dp(12), dp(12), dp(12), dp(12)],
                on_release=self._on_generate_report,
            )
        )
        
        # Recent reports
        content.add_widget(
            MDLabel(
                text="RECENT REPORTS",
                theme_text_color="Secondary",
                font_style="Overline",
                bold=True,
                size_hint_y=None,
                height=dp(24),
            )
        )
        
        self.reports_container = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            size_hint_y=None,
        )
        content.add_widget(self.reports_container)
        
        layout.add_widget(content)
        self.add_widget(layout)
    
    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def load_data(self):
        """Load report data"""
        user_id = self.current_user.get('id', 1)
        
        # Get statistics
        stats = scan_repo.get_scan_statistics(user_id)
        self.total_scans_value.text = str(stats['total_scans'])
        self.infection_rate_value.text = f"{stats['infection_rate']:.1f}%"
        
        # Update distribution chart
        if stats['total_scans'] > 0:
            self.dist_chart.values = [stats['healthy_count'], stats['infected_count']]
            self.dist_chart.labels = ['Healthy', 'Infected']
            self.dist_chart.colors_list = ['#22C55E', '#DC2626']
        
        # Generate trend data
        self._load_trend_data(user_id)
        
        # Load recent reports
        self._load_recent_reports(user_id)
    
    def _load_trend_data(self, user_id: int):
        """Load trend chart data"""
        try:
            scans = scan_repo.get_user_scans(user_id, limit=30)
            
            from collections import defaultdict
            from datetime import datetime
            
            daily = defaultdict(lambda: {'total': 0, 'healthy': 0, 'infected': 0})
            
            for scan in scans:
                date_str = ''
                scan_date = scan.get('scan_date', '')
                if isinstance(scan_date, str):
                    date_str = scan_date[:10]
                else:
                    date_str = str(scan_date)[:10]
                
                daily[date_str]['total'] += 1
                if scan.get('classification') == 'Healthy':
                    daily[date_str]['healthy'] += 1
                else:
                    daily[date_str]['infected'] += 1
            
            sorted_dates = sorted(daily.keys())[-7:]  # Last 7 days
            
            self.trend_chart.dates = sorted_dates
            self.trend_chart.values = [daily[d]['total'] for d in sorted_dates]
            self.trend_chart.healthy_values = [daily[d]['healthy'] for d in sorted_dates]
            self.trend_chart.infected_values = [daily[d]['infected'] for d in sorted_dates]
            
        except Exception as e:
            print(f"Trend data error: {e}")
    
    def _load_recent_reports(self, user_id: int):
        """Load recent generated reports"""
        self.reports_container.clear_widgets()
        
        reports = report_repo.get_user_reports(user_id)
        
        if not reports:
            self.reports_container.add_widget(
                MDLabel(
                    text="No reports generated yet",
                    theme_text_color="Secondary",
                    font_style="Caption",
                    halign='center',
                    size_hint_y=None,
                    height=dp(40),
                )
            )
            self.reports_container.height = dp(50)
            return
        
        self.reports_container.height = len(reports) * dp(70) + dp(20)
        
        for report in reports:
            card = MDCard(
                orientation='horizontal',
                padding=dp(12),
                radius=[dp(8)] * 4,
                elevation=1,
                size_hint_y=None,
                height=dp(60),
            )
            
            info = MDBoxLayout(orientation='vertical')
            info.add_widget(MDLabel(
                text=report.get('report_title', 'Untitled'),
                theme_text_color="Primary",
                font_style="Subtitle2",
                bold=True,
                size_hint_y=None,
                height=dp(20),
            ))
            info.add_widget(MDLabel(
                text=format_datetime(report.get('created_at', '')),
                theme_text_color="Secondary",
                font_style="Caption",
                size_hint_y=None,
                height=dp(16),
            ))
            card.add_widget(info)
            
            card.add_widget(MDIconButton(
                icon="file-pdf-box",
                theme_text_color="Custom",
                text_color=PRIMARY_GREEN,
                on_release=lambda x, r=report: self._open_report(r),
            ))
            
            self.reports_container.add_widget(card)
    
    def _on_generate_report(self, instance):
        """Generate PDF report"""
        content = ReportConfigDialogContent()
        
        dialog = DialogManager.show_confirm(
            "Generate Report",
            "Configure your report settings",
            on_confirm=lambda: self._do_generate(content),
        )
    
    def _do_generate(self, content):
        """Actually generate the report"""
        try:
            config = content.get_config()
            user_id = self.current_user.get('id', 1)
            
            # Get scan data
            date_from = config.get('date_from', '')
            date_to = config.get('date_to', '')
            
            scans = scan_repo.search_scans(user_id, date_from=date_from, date_to=date_to)
            
            # Calculate statistics
            total = len(scans)
            healthy = sum(1 for s in scans if s.get('classification') == 'Healthy')
            infected = total - healthy
            rate = (infected / total * 100) if total > 0 else 0
            
            stats = {
                'total_scans': total,
                'healthy_count': healthy,
                'infected_count': infected,
                'infection_rate': rate,
            }
            
            user_info = {
                'fullname': self.current_user.get('fullname', 'User'),
                'organization': self.current_user.get('organization', ''),
            }
            
            # Generate report
            report_gen = get_report_generator()
            pdf_path = report_gen.generate_summary_report(
                config, stats, scans, user_info
            )
            
            # Save report record
            report_repo.create_report(
                user_id=user_id,
                report_title=config['title'],
                date_from=date_from,
                date_to=date_to,
                total_scans=total,
                healthy_count=healthy,
                infected_count=infected,
                infection_rate=rate,
                comments=config.get('comments', ''),
                pdf_file=pdf_path,
            )
            
            DialogManager.show_success(f"Report generated:\n{pdf_path}")
            Clock.schedule_once(lambda dt: self.load_data(), 0.5)
            
        except Exception as e:
            DialogManager.show_error(f"Report generation failed: {str(e)}")
    
    def _open_report(self, report: dict):
        """Open generated report"""
        pdf_file = report.get('pdf_file', '')
        if pdf_file and os.path.exists(pdf_file):
            DialogManager.show_alert("Report", f"Report located at:\n{pdf_file}")
        else:
            DialogManager.show_error("Report file not found")
    
    def _on_new_report(self):
        """Create new report"""
        self._on_generate_report(None)
    
    def _on_back(self):
        """Go back to dashboard"""
        if self.manager:
            self.manager.current = "dashboard"
    
    def on_enter(self):
        """Load data when entering"""
        Clock.schedule_once(lambda dt: self.load_data(), 0.1)
