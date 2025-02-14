from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
from ..printer import Printer

class DashboardPrinter(Printer):
    """Classe específica para impressão do dashboard"""
    def __init__(self, dashboard_data):
        super().__init__()
        self.data = dashboard_data
    
    def gerar_relatorio(self, output_file):
        """Gera o relatório PDF do dashboard"""
        doc = self.criar_documento(output_file)
        elements = []
        
        # Cabeçalho
        elements.extend(self._criar_cabecalho())
        
        # Indicadores Principais
        elements.extend(self._criar_secao_indicadores())
        
        # Análise de Atrasos
        elements.extend(self._criar_secao_atrasos())
        
        # Construir documento
        doc.build(elements)
    
    def _criar_cabecalho(self):
        """Cria o cabeçalho específico do dashboard"""
        info_data = [
            ['Data:', datetime.now().strftime("%d/%m/%Y")],
            ['Equipe:', self.data.get('equipe', 'SPCS')],
            ['Gerado Por:', self.data.get('gerado_por', 'WRP')]
        ]
        
        return self.criar_cabecalho_base(
            "Relatório de Dashboard - Interest Engenharia",
            info_data
        )
    
    def _criar_secao_indicadores(self):
        """Cria a seção de indicadores principais"""
        elements = []
        
        subtitle = Paragraph("Indicadores Principais", self.subtitle_style)
        elements.append(subtitle)
        
        indicadores_data = [
            ['Indicador', 'Valor', 'Tendência'],
            ['Semana Anterior', self.data.get('indicadores', {}).get('semana_anterior', '100%'), '▲'],
            ['Semana Atual', self.data.get('indicadores', {}).get('semana_atual', '90%'), '▼'],
            ['Média Semestral', self.data.get('indicadores', {}).get('media_semestral', '20%'), '▲'],
            ['Média Anual', self.data.get('indicadores', {}).get('media_anual', '0.5%'), '▼']
        ]
        
        table = self.criar_tabela_base(
            indicadores_data,
            colWidths=[2.5*inch, 1.5*inch, 1*inch],
            style=TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#015BFF')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#343333')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E0E0E0'))
            ])
        )
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _criar_secao_atrasos(self):
        """Cria a seção de análise de atrasos"""
        elements = []
        
        subtitle = Paragraph("Análise de Atrasos", self.subtitle_style)
        elements.append(subtitle)
        
        atrasos_data = [
            ['Motivo', 'Quantidade', 'Tempo', 'Impacto'],
            ['Falta de Material', '15', '3d', 'Alto'],
            ['Equipamento', '8', '2d', 'Médio'],
            ['Mão de Obra', '12', '4d', 'Alto'],
            ['Clima', '5', '1d', 'Baixo'],
            ['Documentação', '10', '2d', 'Médio']
        ]
        
        table = self.criar_tabela_base(
            atrasos_data,
            colWidths=[2*inch, 1.5*inch, 1*inch, 1.5*inch],
            style=TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#015BFF')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#343333')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E0E0E0'))
            ])
        )
        
        elements.append(table)
        
        return elements 