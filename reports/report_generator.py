"""
YamGuard - PDF Report Generator
Generates professional PDF diagnostic reports using ReportLab
"""

import os
import io
import tempfile
from datetime import datetime
from typing import List, Dict, Any, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm, mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image as RLImage, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.colors import HexColor, Color as RLColor
from reportlab.graphics.shapes import Drawing, Rect, String, Circle
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.pdfgen import canvas

from utils.constants import (
    APP_NAME, APP_VERSION, REPORT_HEADER, REPORT_FOOTER,
    COMPANY_ADDRESS, COMPANY_CONTACT, EXPORTS_DIR,
)
from utils.helpers import format_datetime, get_file_size


class YamGuardReport:
    """Professional PDF report generator for YamGuard"""
    
    # Color palette
    PRIMARY_GREEN = HexColor("#16A34A")
    DARK_GREEN = HexColor("#166534")
    HEALTHY_COLOR = HexColor("#22C55E")
    WARNING_COLOR = HexColor("#F59E0B")
    INFECTED_COLOR = HexColor("#DC2626")
    TEXT_PRIMARY = HexColor("#1E293B")
    TEXT_SECONDARY = HexColor("#64748B")
    BACKGROUND = HexColor("#F8FAFC")
    BORDER_COLOR = HexColor("#E2E8F0")
    WHITE = HexColor("#FFFFFF")
    
    def __init__(self):
        self.styles = self._create_styles()
        self.temp_images = []
    
    def _create_styles(self) -> Dict[str, ParagraphStyle]:
        """Create custom paragraph styles"""
        styles = getSampleStyleSheet()
        
        # Title style
        styles.add(ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=self.DARK_GREEN,
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
        ))
        
        # Subtitle style
        styles.add(ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=self.TEXT_SECONDARY,
            alignment=TA_CENTER,
            spaceAfter=30,
        ))
        
        # Section header
        styles.add(ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=self.PRIMARY_GREEN,
            spaceBefore=20,
            spaceAfter=10,
            fontName='Helvetica-Bold',
            borderColor=self.PRIMARY_GREEN,
            borderWidth=2,
            borderPadding=5,
            leftIndent=0,
        ))
        
        # Table header
        styles.add(ParagraphStyle(
            'TableHeader',
            parent=styles['Normal'],
            fontSize=9,
            textColor=self.WHITE,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
        ))
        
        # Table cell
        styles.add(ParagraphStyle(
            'TableCell',
            parent=styles['Normal'],
            fontSize=9,
            textColor=self.TEXT_PRIMARY,
            alignment=TA_LEFT,
        ))
        
        # Info label
        styles.add(ParagraphStyle(
            'InfoLabel',
            parent=styles['Normal'],
            fontSize=10,
            textColor=self.TEXT_SECONDARY,
            fontName='Helvetica-Bold',
        ))
        
        # Info value
        styles.add(ParagraphStyle(
            'InfoValue',
            parent=styles['Normal'],
            fontSize=10,
            textColor=self.TEXT_PRIMARY,
        ))
        
        # Recommendation
        styles.add(ParagraphStyle(
            'Recommendation',
            parent=styles['Normal'],
            fontSize=11,
            textColor=self.TEXT_PRIMARY,
            backColor=HexColor("#DCFCE7"),
            borderColor=self.HEALTHY_COLOR,
            borderWidth=1,
            borderPadding=10,
            spaceBefore=10,
            spaceAfter=10,
        ))
        
        # Footer
        styles.add(ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=self.TEXT_SECONDARY,
            alignment=TA_CENTER,
        ))
        
        return styles
    
    def generate_scan_report(self, scan_data: Dict[str, Any], 
                            user_info: Dict[str, Any],
                            output_path: Optional[str] = None) -> str:
        """
        Generate a single scan diagnostic report
        
        Args:
            scan_data: Scan result data
            user_info: User information
            output_path: Optional output file path
            
        Returns:
            Path to generated PDF
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(EXPORTS_DIR, f"YamGuard_Scan_{timestamp}.pdf")
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
        )
        
        elements = []
        
        # Header
        elements.extend(self._create_header())
        
        # Report metadata
        elements.extend(self._create_metadata(user_info, scan_data.get('scan_date', datetime.now())))
        
        elements.append(Spacer(1, 20))
        
        # Classification Result
        elements.append(Paragraph("DIAGNOSTIC RESULT", self.styles['SectionHeader']))
        elements.extend(self._create_result_section(scan_data))
        
        elements.append(Spacer(1, 15))
        
        # Scan Details Table
        elements.append(Paragraph("SCAN DETAILS", self.styles['SectionHeader']))
        elements.append(self._create_scan_details_table(scan_data))
        
        elements.append(Spacer(1, 15))
        
        # Spectral Analysis
        if scan_data.get('spectral_data'):
            elements.append(Paragraph("SPECTRAL ANALYSIS", self.styles['SectionHeader']))
            elements.extend(self._create_spectral_section(scan_data['spectral_data']))
            elements.append(Spacer(1, 15))
        
        # Recommendation
        elements.append(Paragraph("RECOMMENDATION", self.styles['SectionHeader']))
        elements.append(Paragraph(
            scan_data.get('recommendation', 'No recommendation available.'),
            self.styles['Recommendation']
        ))
        
        # Footer
        elements.append(Spacer(1, 30))
        elements.append(HRFlowable(width="100%", thickness=1, color=self.BORDER_COLOR))
        elements.append(Paragraph(
            f"{REPORT_FOOTER} | {APP_NAME} v{APP_VERSION} | Generated: {format_datetime()}",
            self.styles['Footer']
        ))
        
        # Build PDF
        doc.build(elements, onFirstPage=self._add_page_decorations, 
                 onLaterPages=self._add_page_decorations)
        
        return output_path
    
    def generate_summary_report(self, report_config: Dict[str, Any],
                               statistics: Dict[str, Any],
                               scan_history: List[Dict[str, Any]],
                               user_info: Dict[str, Any],
                               output_path: Optional[str] = None) -> str:
        """
        Generate summary report with multiple scans
        
        Args:
            report_config: Report configuration
            statistics: Summary statistics
            scan_history: List of scan records
            user_info: User information
            output_path: Optional output file path
            
        Returns:
            Path to generated PDF
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(EXPORTS_DIR, f"YamGuard_Report_{timestamp}.pdf")
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
        )
        
        elements = []
        
        # Header
        elements.extend(self._create_header(report_config.get('title', 'Diagnostic Summary Report')))
        
        # Metadata
        elements.extend(self._create_metadata(user_info, datetime.now(), 
                                             report_config.get('date_from'), 
                                             report_config.get('date_to')))
        
        elements.append(Spacer(1, 20))
        
        # Statistics Summary
        elements.append(Paragraph("SUMMARY STATISTICS", self.styles['SectionHeader']))
        elements.extend(self._create_statistics_section(statistics))
        
        elements.append(Spacer(1, 15))
        
        # Charts
        if statistics:
            elements.append(Paragraph("VISUAL ANALYSIS", self.styles['SectionHeader']))
            chart_table = self._create_charts_table(statistics)
            if chart_table:
                elements.append(chart_table)
            elements.append(Spacer(1, 15))
        
        # Scan History Table
        if scan_history:
            elements.append(Paragraph("SCAN HISTORY", self.styles['SectionHeader']))
            elements.append(self._create_scan_history_table(scan_history))
            elements.append(Spacer(1, 15))
        
        # Comments
        if report_config.get('comments'):
            elements.append(Paragraph("NOTES", self.styles['SectionHeader']))
            elements.append(Paragraph(report_config['comments'], self.styles['Normal']))
        
        # Signature area
        elements.append(Spacer(1, 40))
        elements.append(self._create_signature_area())
        
        # Footer
        elements.append(Spacer(1, 30))
        elements.append(HRFlowable(width="100%", thickness=1, color=self.BORDER_COLOR))
        elements.append(Paragraph(
            f"{REPORT_FOOTER} | {APP_NAME} v{APP_VERSION} | Generated: {format_datetime()}",
            self.styles['Footer']
        ))
        
        # Build PDF
        doc.build(elements, onFirstPage=self._add_page_decorations,
                 onLaterPages=self._add_page_decorations)
        
        return output_path
    
    def _create_header(self, title: str = None) -> List:
        """Create report header"""
        elements = []
        
        # Logo and title
        header_data = [[
            Paragraph(f"<font size='28' color='#166534'><b>{APP_NAME}</b></font>", self.styles['Normal']),
            Paragraph(f"<font size='10' color='#64748B'>{REPORT_HEADER}</font><br/><font size='8' color='#94A3B8'>Version {APP_VERSION}</font>", self.styles['Normal']),
        ]]
        
        header_table = Table(header_data, colWidths=[8*cm, 8*cm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ]))
        elements.append(header_table)
        
        if title:
            elements.append(Paragraph(title, self.styles['ReportTitle']))
        else:
            elements.append(Paragraph("Diagnostic Report", self.styles['ReportTitle']))
        
        elements.append(HRFlowable(width="100%", thickness=2, color=self.PRIMARY_GREEN))
        
        return elements
    
    def _create_metadata(self, user_info: Dict, scan_date,
                        date_from: str = None, date_to: str = None) -> List:
        """Create report metadata section"""
        elements = []
        
        metadata_data = []
        
        # Left column
        left_data = [
            [Paragraph("Generated By:", self.styles['InfoLabel']), 
             Paragraph(user_info.get('fullname', 'Unknown'), self.styles['InfoValue'])],
            [Paragraph("Organization:", self.styles['InfoLabel']),
             Paragraph(user_info.get('organization', 'N/A'), self.styles['InfoValue'])],
            [Paragraph("Date:", self.styles['InfoLabel']),
             Paragraph(format_datetime(scan_date if isinstance(scan_date, datetime) else datetime.now()), 
                      self.styles['InfoValue'])],
        ]
        
        # Right column
        right_data = [
            [Paragraph("Report ID:", self.styles['InfoLabel']),
             Paragraph(f"RPT-{datetime.now().strftime('%Y%m%d-%H%M%S')}", self.styles['InfoValue'])],
            [Paragraph("Status:", self.styles['InfoLabel']),
             Paragraph("<font color='#16A34A'>● Final</font>", self.styles['InfoValue'])],
        ]
        
        if date_from and date_to:
            right_data.append([Paragraph("Period:", self.styles['InfoLabel']),
                              Paragraph(f"{date_from} to {date_to}", self.styles['InfoValue'])])
        
        # Combine columns
        metadata_data = [[
            Table(left_data, colWidths=[3*cm, 5*cm]),
            Table(right_data, colWidths=[3*cm, 5*cm]),
        ]]
        
        meta_table = Table(metadata_data, colWidths=[8*cm, 8*cm])
        meta_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (0, 0), 0),
            ('RIGHTPADDING', (1, 0), (1, 0), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        elements.append(meta_table)
        return elements
    
    def _create_result_section(self, scan_data: Dict) -> List:
        """Create classification result section"""
        elements = []
        
        classification = scan_data.get('classification', 'Unknown')
        confidence = scan_data.get('confidence_score', 0)
        severity = scan_data.get('severity_level', 'Unknown')
        
        # Determine color
        if classification == 'Healthy':
            result_color = self.HEALTHY_COLOR
            result_bg = HexColor("#DCFCE7")
        elif 'Level 1' in classification:
            result_color = self.WARNING_COLOR
            result_bg = HexColor("#FEF3C7")
        else:
            result_color = self.INFECTED_COLOR
            result_bg = HexColor("#FEE2E2")
        
        # Result box
        result_data = [
            [Paragraph(f"<font size='16'><b>{classification.upper()}</b></font>", self.styles['Normal'])],
            [Paragraph(f"Confidence: <b>{confidence:.1f}%</b> | Severity: <b>{severity}</b>", 
                      self.styles['Normal'])],
        ]
        
        result_table = Table(result_data, colWidths=[16*cm])
        result_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), result_bg),
            ('TEXTCOLOR', (0, 0), (0, 0), result_color),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (0, 0), 5),
            ('TOPPADDING', (1, 0), (1, 0), 5),
            ('ROUNDEDCORNERS', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(result_table)
        return elements
    
    def _create_scan_details_table(self, scan_data: Dict) -> Table:
        """Create scan details table"""
        data = [
            [Paragraph("Tuber ID", self.styles['TableHeader']),
             Paragraph("Classification", self.styles['TableHeader']),
             Paragraph("Severity", self.styles['TableHeader']),
             Paragraph("Confidence", self.styles['TableHeader']),
             Paragraph("Date", self.styles['TableHeader'])],
            [Paragraph(scan_data.get('tuber_id', 'N/A'), self.styles['TableCell']),
             Paragraph(scan_data.get('classification', 'N/A'), self.styles['TableCell']),
             Paragraph(scan_data.get('severity_level', 'N/A'), self.styles['TableCell']),
             Paragraph(f"{scan_data.get('confidence_score', 0):.1f}%", self.styles['TableCell']),
             Paragraph(format_datetime(scan_data.get('scan_date', datetime.now())), 
                      self.styles['TableCell'])],
        ]
        
        table = Table(data, colWidths=[4*cm, 3.5*cm, 3*cm, 2.5*cm, 4*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.PRIMARY_GREEN),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.WHITE),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), self.WHITE),
            ('TEXTCOLOR', (0, 1), (-1, -1), self.TEXT_PRIMARY),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, self.BORDER_COLOR),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [self.WHITE, HexColor("#F8FAFC")]),
        ]))
        
        return table
    
    def _create_spectral_section(self, spectral_data: Dict) -> List:
        """Create spectral analysis section"""
        elements = []
        
        # Spectral indices table
        if isinstance(spectral_data, dict) and 'indices' in spectral_data:
            indices = spectral_data['indices']
            data = [[Paragraph("Index", self.styles['TableHeader']),
                    Paragraph("Value", self.styles['TableHeader'])]]
            
            for key, value in indices.items():
                data.append([Paragraph(key, self.styles['TableCell']),
                           Paragraph(f"{value:.4f}", self.styles['TableCell'])])
            
            table = Table(data, colWidths=[8*cm, 8*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.PRIMARY_GREEN),
                ('TEXTCOLOR', (0, 0), (-1, 0), self.WHITE),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, self.BORDER_COLOR),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [self.WHITE, HexColor("#F8FAFC")]),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(table)
        
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(
            "Spectral analysis based on hyperspectral imaging simulation from 400nm to 1000nm wavelength range.",
            self.styles['Normal']
        ))
        
        return elements
    
    def _create_statistics_section(self, statistics: Dict) -> List:
        """Create statistics summary section"""
        elements = []
        
        stats_data = [
            [Paragraph("Total Scans", self.styles['InfoLabel']),
             Paragraph(str(statistics.get('total_scans', 0)), self.styles['InfoValue']),
             Paragraph("Healthy Count", self.styles['InfoLabel']),
             Paragraph(str(statistics.get('healthy_count', 0)), self.styles['InfoValue'])],
            [Paragraph("Infected Count", self.styles['InfoLabel']),
             Paragraph(str(statistics.get('infected_count', 0)), self.styles['InfoValue']),
             Paragraph("Infection Rate", self.styles['InfoLabel']),
             Paragraph(f"{statistics.get('infection_rate', 0):.1f}%", self.styles['InfoValue'])],
        ]
        
        table = Table(stats_data, colWidths=[4*cm, 4*cm, 4*cm, 4*cm])
        table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (0, -1), HexColor("#F1F5F9")),
            ('BACKGROUND', (2, 0), (2, -1), HexColor("#F1F5F9")),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        elements.append(table)
        return elements
    
    def _create_charts_table(self, statistics: Dict) -> Optional[Table]:
        """Create charts section"""
        try:
            healthy = statistics.get('healthy_count', 0)
            infected = statistics.get('infected_count', 0)
            total = statistics.get('total_scans', 0)
            
            if total == 0:
                return None
            
            # Create pie chart drawing
            drawing = Drawing(300, 150)
            
            # Detection distribution pie
            pie = Pie()
            pie.x = 75
            pie.y = 10
            pie.width = 130
            pie.height = 130
            pie.data = [healthy, infected]
            pie.labels = [f'Healthy\n{healthy}', f'Infected\n{infected}']
            pie.slices.strokeWidth = 2
            pie.slices[0].fillColor = self.HEALTHY_COLOR
            pie.slices[1].fillColor = self.INFECTED_COLOR
            pie.slices[0].strokeColor = self.WHITE
            pie.slices[1].strokeColor = self.WHITE
            
            drawing.add(pie)
            
            chart_data = [[drawing]]
            chart_table = Table(chart_data, colWidths=[16*cm])
            chart_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ]))
            
            return chart_table
            
        except Exception as e:
            print(f"Chart creation error: {e}")
            return None
    
    def _create_scan_history_table(self, scans: List[Dict]) -> Table:
        """Create scan history table"""
        data = [[
            Paragraph("Tuber ID", self.styles['TableHeader']),
            Paragraph("Date", self.styles['TableHeader']),
            Paragraph("Classification", self.styles['TableHeader']),
            Paragraph("Severity", self.styles['TableHeader']),
            Paragraph("Confidence", self.styles['TableHeader']),
        ]]
        
        for scan in scans[:50]:  # Limit to 50 rows
            classification = scan.get('classification', 'Unknown')
            if classification == 'Healthy':
                class_color = "#22C55E"
            elif 'Level 1' in classification:
                class_color = "#F59E0B"
            else:
                class_color = "#DC2626"
            
            data.append([
                Paragraph(scan.get('tuber_id', 'N/A'), self.styles['TableCell']),
                Paragraph(format_datetime(scan.get('scan_date', '')), self.styles['TableCell']),
                Paragraph(f"<font color='{class_color}'>{classification}</font>", self.styles['TableCell']),
                Paragraph(scan.get('severity_level', 'N/A'), self.styles['TableCell']),
                Paragraph(f"{scan.get('confidence_score', 0):.1f}%", self.styles['TableCell']),
            ])
        
        table = Table(data, colWidths=[4*cm, 3.5*cm, 3.5*cm, 3*cm, 2.5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.PRIMARY_GREEN),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.WHITE),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), self.WHITE),
            ('TEXTCOLOR', (0, 1), (-1, -1), self.TEXT_PRIMARY),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, self.BORDER_COLOR),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [self.WHITE, HexColor("#F8FAFC")]),
        ]))
        
        return table
    
    def _create_signature_area(self) -> Table:
        """Create signature area"""
        sig_data = [
            ["", ""],
            ["_________________________", "_________________________"],
            ["Authorized Signature", "Date"],
            ["", ""],
            [COMPANY_ADDRESS, COMPANY_CONTACT],
        ]
        
        table = Table(sig_data, colWidths=[8*cm, 8*cm])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 2), (-1, 2), self.TEXT_SECONDARY),
            ('TEXTCOLOR', (0, 4), (-1, 4), self.TEXT_SECONDARY),
            ('FONTSIZE', (0, 4), (-1, 4), 8),
        ]))
        
        return table
    
    def _add_page_decorations(self, canvas, doc):
        """Add page decorations (header/footer)"""
        canvas.saveState()
        
        # Page number
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(self.TEXT_SECONDARY)
        canvas.drawRightString(
            doc.pagesize[0] - 2*cm,
            1.5*cm,
            f"Page {doc.page}"
        )
        
        canvas.restoreState()
    
    def cleanup(self):
        """Clean up temporary files"""
        for temp_file in self.temp_images:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass


# Singleton instance
_report_generator = None

def get_report_generator() -> YamGuardReport:
    """Get singleton report generator"""
    global _report_generator
    if _report_generator is None:
        _report_generator = YamGuardReport()
    return _report_generator
