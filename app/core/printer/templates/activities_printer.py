import logging
from ..printer import Printer
from reportlab.lib import colors
from reportlab.lib.units import inch, mm, cm
from reportlab.platypus import Table, TableStyle, Image, Spacer, Paragraph
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate
from reportlab.lib.pagesizes import A4
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class ActivitiesPrinter(Printer):
    def __init__(self):
        super().__init__()
        logger.debug("[REPORT] Inicializando ActivitiesPrinter")
        
    def generate_report(self, output_file: str, data: dict, logo_path: str = None):
        """Gera o relatório com cabeçalho e rodapé fixos e margens ABNT."""
        try:
            logger.info(f"[REPORT] Iniciando geração do relatório: {output_file}")
            
            # Margens ABNT
            margins = {
                'top': 3 * cm,     # 3cm superior
                'bottom': 2 * cm,  # 2cm inferior
                'left': 3 * cm,    # 3cm esquerda
                'right': 2 * cm    # 2cm direita
            }
            
            # Altura do rodapé
            footer_height = 1 * cm
            
            doc = BaseDocTemplate(
                output_file,
                pagesize=A4,
                rightMargin=margins['right'],
                leftMargin=margins['left'],
                topMargin=margins['top'] + (1 * cm),  # Aumentado para dar mais espaço ao cabeçalho
                bottomMargin=margins['bottom'] + footer_height
            )
            
            # Frame principal para o conteúdo
            content_frame = Frame(
                margins['left'],
                margins['bottom'] + footer_height,
                A4[0] - margins['left'] - margins['right'],
                A4[1] - margins['top'] - margins['bottom'] - footer_height - (1 * cm),
                id='normal'
            )
            
            def add_header_and_footer(canvas, doc):
                canvas.saveState()
                self._add_header(canvas, doc, data, logo_path)
                self._add_footer(canvas, doc)
                canvas.restoreState()
            
            template = PageTemplate(
                id='report',
                frames=[content_frame],
                onPage=add_header_and_footer
            )
            doc.addPageTemplates([template])
            
            elements = []
            elements.extend(self._create_activities_section(data['activities']))
            elements.append(Spacer(1, 0.5 * cm))
            elements.extend(self._create_summary_section(data['activities'], data['user_info']['base_value']))
            
            logger.info("[REPORT] Finalizando geração do PDF")
            doc.build(elements)
            
            logger.info(f"[REPORT] Relatório gerado com sucesso: {output_file}")

        except Exception as e:
            logger.error(f"[REPORT] Erro ao gerar relatório PDF: {str(e)}")
            raise

    def _add_footer(self, canvas, doc):
        """Adiciona o rodapé fixo usando uma tabela."""
        canvas.saveState()
        
        # Configurações do rodapé
        footer_y = doc.bottomMargin - (0.7 * cm)
        available_width = A4[0] - doc.leftMargin - doc.rightMargin
        
        # Dados da tabela do rodapé
        footer_data = [[
            Paragraph(f"Página: {canvas.getPageNumber()}", self.styles['Normal']),  # Modificado aqui
            Paragraph("RELATÓRIO DE ATIVIDADES", self.styles['Normal']),
            Paragraph(datetime.now().strftime("Data: %d/%m/%Y"), self.styles['Normal'])
        ]]
        
        # Define larguras das colunas
        col_widths = [
            available_width * 0.25,  # 25% para número da página
            available_width * 0.50,  # 50% para título
            available_width * 0.25   # 25% para data
        ]
        
        # Cria e estiliza a tabela
        footer_table = Table(footer_data, colWidths=col_widths)
        footer_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 1), (1, -1), 'MIDDLE'),
        ]))
        
        # Desenha a tabela no canvas
        w, h = footer_table.wrap(available_width, doc.bottomMargin)
        footer_table.drawOn(canvas, doc.leftMargin, footer_y)
        
        canvas.restoreState()
    
    def _add_header(self, canvas, doc, data: dict, logo_path: str = None):
        """Adiciona o cabeçalho fixo no topo de cada página usando uma tabela."""
        canvas.saveState()
        
        # Define o caminho do logo
        default_logo = os.path.join('icons', 'logo_light.png')
        logo_to_use = logo_path if logo_path and os.path.exists(logo_path) else default_logo
        
        # Posições para o cabeçalho - aumentado o espaço do topo
        header_y = A4[1] - (1.5 * cm)  # Ajustado para começar mais alto
        available_width = A4[0] - doc.leftMargin - doc.rightMargin
        
        # Cria dados da tabela do cabeçalho com estilos específicos
        user_style = self.styles['Normal'].clone('UserStyle')
        user_style.fontSize = 10
        user_style.leading = 14  # Espaçamento entre linhas
        
        title_style = self.styles['Normal'].clone('TitleStyle')
        title_style.fontSize = 12
        title_style.textColor = colors.HexColor('#FF4500')
        title_style.alignment = 1  # Centralizado
        title_style.fontName = 'Helvetica-Bold'
        
        # Formata o texto do período
        periodo = ""
        if 'period' in data:
            meses = [
                '', 'Janeiro', 'Fevereiro', 'Março', 'Abril',
                'Maio', 'Junho', 'Julho', 'Agosto',
                'Setembro', 'Outubro', 'Novembro', 'Dezembro'
            ]
            mes = meses[data['period']['month']]
            ano = data['period']['year']
            periodo = f"PERÍODO: {mes}/{ano}"
        
        header_data = [[
            # Primeira coluna: informações do usuário
            Paragraph(
                f"USUÁRIO: {data['user_info']['user_name']}<br/>"
                f"EQUIPE: {data['user_info']['team_name']}<br/>"
                f"{periodo}",
                user_style
            ),
            # Segunda coluna: título
            Paragraph(
                "RELATÓRIO",
                title_style
            ),
            # Terceira coluna: logo
            Image(
                logo_to_use,
                width=4.26 * 28.35,
                height=0.87 * 28.35
            ) if os.path.exists(logo_to_use) else ""
        ]]
        
        # Define larguras das colunas
        col_widths = [
            available_width * 0.40,  # 40% para informações do usuário
            available_width * 0.20,  # 20% para o título
            available_width * 0.40   # 40% para o logo
        ]
        
        # Cria e estiliza a tabela
        header_table = Table(header_data, colWidths=col_widths)
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        
        # Desenha a tabela no canvas
        w, h = header_table.wrap(available_width, doc.topMargin)
        header_table.drawOn(canvas, doc.leftMargin, header_y - h)
        
        canvas.restoreState()


    def _create_activities_section(self, activities: list) -> list:
        """Cria a seção de entrada das atividades"""
        elements = []
        
        # Larguras ajustadas para margens ABNT
        available_width = A4[0] - (5 * cm)  # 3cm esquerda + 2cm direita
        col_widths = [
            available_width * 0.40,  # 40% para descrição
            available_width * 0.40,  # 40% para atividade
            available_width * 0.20   # 20% para tempo total
        ]
        
        # Estilo para texto nas células
        cell_style = self.styles['Normal'].clone('CellStyle')
        cell_style.fontSize = 9
        cell_style.leading = 12  # Espaçamento entre linhas
        cell_style.wordWrap = 'CJK'  # Permite quebra de linha em qualquer caractere
        
        table_data = [["DESCRIÇÃO", "ATIVIDADE", "TEMPO TOTAL"]]
        
        for activity in activities:
            table_data.append([
                Paragraph(activity['description'], cell_style),
                Paragraph(activity['activity'], cell_style),
                activity['total_time']
            ])
        
        activities_table = Table(table_data, colWidths=col_widths)
        activities_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF4500')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),  # Alinhamento padrão à esquerda
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),  # Centraliza toda a coluna TEMPO TOTAL
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Alinha verticalmente ao meio
        ]))
        
        elements.append(activities_table)
        return elements

    def _create_summary_section(self, activities: list, base_value: float = 0.0) -> list:
        """Cria a seção de cálculos e totais"""
        elements = []
        
        total_activities = len(activities)
        
        def get_hours_from_timedelta(td):
            if td is None:
                logger.warning("[REPORT] total_time é None")
                return 0
                
            if isinstance(td, str):
                try:
                    # Converte string HH:MM:SS para segundos
                    h, m, s = map(int, td.split(':'))
                    total_seconds = h * 3600 + m * 60 + s
                    return total_seconds / 3600
                except Exception as e:
                    logger.error(f"[REPORT] Erro ao converter string de tempo: {str(e)}")
                    return 0
                    
            try:
                total_seconds = td.total_seconds()
                return total_seconds / 3600
            except Exception as e:
                logger.error(f"[REPORT] Erro ao converter tempo: {str(e)}")
                return 0
        
        def format_currency(value):
            """Formata valor monetário no padrão brasileiro"""
            return f"R$ {value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
        
        # Soma total de horas com tratamento de erro
        total_hours = 0
        for activity in activities:
            try:
                total_hours += get_hours_from_timedelta(activity.get('total_time'))
            except Exception as e:
                logger.error(f"[REPORT] Erro ao processar atividade: {str(e)}")
                continue
        
        # Cálculo do valor total usando a fórmula correta
        WORKDAYS = 21  # Dias úteis no mês
        WORKHOURS = 8.8  # Horas por dia
        
        if base_value > 0:
            total_value = (base_value * total_hours) / (WORKDAYS * WORKHOURS)
        else:
            total_value = (50 * total_hours) / (WORKDAYS * WORKHOURS)  # Usa 50 como fallback
        
        # Formato HH:MM:SS
        hours = int(total_hours)
        minutes = int((total_hours * 60) % 60)
        seconds = int((total_hours * 3600) % 60)
        total_time_formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        available_width = A4[0] - (5 * cm)
        col_widths = [
            available_width * 0.23,  # Reduzido para acomodar nova coluna
            available_width * 0.19,  # Tempo em HH:MM:SS
            available_width * 0.19,  # Tempo em decimal
            available_width * 0.19,  # Valor base
            available_width * 0.20   # Valor total
        ]
        
        summary_data = [
            ["ATIVIDADES TOTAIS", "TEMPO TOTAL", "HORAS", "VALOR BASE", "VALOR TOTAL"],
            [str(total_activities), total_time_formatted, f"{total_hours:.3f}", 
             format_currency(base_value), format_currency(total_value)]
        ]
        
        summary_table = Table(summary_data, colWidths=col_widths)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF4500')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, 1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(summary_table)
        return elements