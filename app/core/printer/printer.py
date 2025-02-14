from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

class Printer:
    """Classe base para impressão de relatórios"""
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_styles()
    
    def setup_styles(self):
        """Configura os estilos base do documento"""
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#015BFF'),
            spaceAfter=30
        )
        
        self.subtitle_style = ParagraphStyle(
            'CustomSubTitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#343333'),
            spaceAfter=20
        )
    
    def criar_documento(self, output_file: str):
        """Cria o documento PDF com as configurações base"""
        # Aqui é onde configuramos as margens do documento
        # leftMargin, rightMargin, topMargin, bottomMargin são as margens em pontos (1 inch = 72 pontos)
        doc = SimpleDocTemplate(
            output_file,
            pagesize=A4,
            leftMargin=40,      # Reduzido de ~72 (1 inch)
            rightMargin=40,     # Reduzido de ~72 (1 inch)
            topMargin=40,       # Reduzido de ~72 (1 inch)
            bottomMargin=40     # Reduzido de ~72 (1 inch)
        )
        return doc
    
    def criar_tabela_base(self, data, colWidths, style):
        """Cria uma tabela com estilo padrão"""
        table = Table(data, colWidths=colWidths)
        table.setStyle(style)
        return table
    
    def criar_cabecalho_base(self, titulo, info_data):
        """Cria um cabeçalho padrão"""
        elements = []
        
        title = Paragraph(titulo, self.title_style)
        elements.append(title)
        
        info_table = self.criar_tabela_base(
            info_data,
            colWidths=[1.5*inch, 2*inch],
            style=TableStyle([
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#343333')),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ])
        )
        
        elements.append(info_table)
        elements.append(Spacer(1, 20))
        
        return elements 