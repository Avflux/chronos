import os
import sys
import logging
import customtkinter as ctk
from tkinter import filedialog
from datetime import datetime
from PIL import Image
from app.core.printer.templates.dashboard_printer import DashboardPrinter
from app.core.printer.query.dashboard_query import DashboardQuery
from app.config.settings import APP_CONFIG


logger = logging.getLogger(__name__)

class DashboardDaily(ctk.CTkToplevel):
    def __init__(self, parent, db_connection=None, user_data=None):
        super().__init__(parent)
        
        # Inicializar dicionário de imagens ANTES de qualquer configuração de interface
        self.images = {}
        
        # Configurar janela
        self.title("Interest Dashboard Dailys 2025")
        
        # Definir dimensões iniciais
        self.largura_janela = 1300
        self.altura_janela = 700
        
        # Permitir redimensionamento
        self.resizable(True, True)
        
        # Configurar tamanho mínimo
        self.minsize(1300, 700)
        
        # Obter dimensões do monitor
        largura_tela = self.winfo_screenwidth()
        altura_tela = self.winfo_screenheight()
        
        # Calcular posição para centralizar
        pos_x = (largura_tela - self.largura_janela) // 2
        pos_y = (altura_tela - self.altura_janela) // 2
        
        # Configurar geometria (tamanho e posição)
        self.geometry(f"{self.largura_janela}x{self.altura_janela}+{pos_x}+{pos_y}")
        
        # Fazer a janela modal
        self.grab_set()
        self.focus_force()
        
        logger.info("[THEME] Inicializando DashboardDaily")
        
        # Armazenar referências importantes
        self.parent = parent
        self.db = db_connection
        self.user_data = user_data
        
        # Criar instância do DashboardQuery
        self.dashboard_query = DashboardQuery(self.db)
        
        # Inicializar dados_atrasos com dicionário vazio
        self.dados_atrasos = {}
        
        # Configurar cores antes de qualquer coisa
        self.setup_cores()
        
        # Inicializar container principal
        self.container = ctk.CTkFrame(self, fg_color=self.cores['fundo'])
        self.container.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Registrar callback para mudanças de tema
        self._on_theme_change_callback_id = self.after(100, self._on_theme_change)
        ctk.AppearanceModeTracker.add(self._on_theme_change_callback, self)
        logger.debug("[THEME] Callback de tema registrado")
        
        # Primeiro carregar os dados, depois criar a interface
        self.carregar_dados_atrasos()
        
        # Forçar atualização inicial do tema
        self._on_theme_change()
        
        # Criar interface após configuração inicial
        self.setup_interface()

    def criar_title_bar(self):
        """Cria a barra de título personalizada"""
        title_bar = ctk.CTkFrame(self, height=35)
        title_bar.pack(fill="x", pady=0)
        title_bar.pack_propagate(False)
        
        # Título
        title_label = ctk.CTkLabel(
            title_bar,
            text="Interest Dashboard Dailys 2025",
            font=("Arial", 12, "bold")
        )
        title_label.pack(side="left", padx=10)
        
        # Frame para botões
        buttons_frame = ctk.CTkFrame(title_bar, fg_color="transparent")
        buttons_frame.pack(side="right", padx=5)
        
        # Botão Minimizar
        min_btn = ctk.CTkButton(
            buttons_frame,
            text="—",
            width=35,
            height=25,
            command=self.iconify
        )
        min_btn.pack(side="left", padx=2)
        
        # Botão Maximizar
        self.max_btn = ctk.CTkButton(
            buttons_frame,
            text="□",
            width=35,
            height=25,
            command=self.toggle_maximize
        )
        self.max_btn.pack(side="left", padx=2)
        
        # Botão Fechar
        close_btn = ctk.CTkButton(
            buttons_frame,
            text="✕",
            width=35,
            height=25,
            command=self.destroy,
            fg_color="#D41919",
            hover_color="#AA1515"
        )
        close_btn.pack(side="left", padx=2)
        
        # Variável para controlar estado maximizado
        self.is_maximized = False

    def toggle_maximize(self):
        """Alterna entre janela maximizada e normal"""
        if self.is_maximized:
            self.restore_window()
        else:
            self.maximize_window()

    def maximize_window(self):
        """Maximiza a janela"""
        self.is_maximized = True
        self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
        self.max_btn.configure(text="❐")
        self.atualizar_layout(None)

    def restore_window(self):
        """Restaura a janela ao tamanho normal"""
        self.is_maximized = False
        self.geometry(f"{self.largura_janela}x{self.altura_janela}+{self.winfo_x()}+{self.winfo_y()}")
        self.max_btn.configure(text="□")
        self.atualizar_layout(None)

    def carregar_dados_atrasos(self):
        """Carrega os dados de atrasos do banco de dados"""
        try:
            if self.db is None:
                logger.error("Conexão com banco de dados não inicializada")
                return
                
            # Usar o DashboardQuery para buscar os dados
            dados = self.dashboard_query.get_dashboard_data(
                user_id=None,  # Remover para ver dados da equipe
                team_id=self.user_data['equipe_id'] if self.user_data else None,
                period='week'
            )
            
            if dados and 'atrasos' in dados:
                # Pegar apenas os dados da semana atual para a lista de controle
                self.dados_atrasos = dados['atrasos'].get('semana_atual', {})
                
                # Armazenar todos os períodos para uso em gráficos
                self.dados_atrasos_periodos = dados['atrasos']
                
                logger.info(f"Dados de atrasos carregados: {len(self.dados_atrasos)} registros da semana atual")
                logger.info(f"Períodos carregados: {list(self.dados_atrasos_periodos.keys())}")
            else:
                logger.warning("Nenhum dado de atraso encontrado")
                self.dados_atrasos = {}
                self.dados_atrasos_periodos = {}
                
        except Exception as e:
            logger.error(f"Erro ao carregar dados de atrasos: {e}")
            self.dados_atrasos = {}
            self.dados_atrasos_periodos = {}

    def setup_cores(self):
        """Configura as cores baseadas no tema atual"""
        is_light = ctk.get_appearance_mode().lower() == "light"
        logger.debug(f"[THEME] Configurando cores para modo: {'Light' if is_light else 'Dark'}")
        
        self.cores = {
            'primaria': "#FF5722",     # Laranja Interest (mantido fixo)
            'secundaria': "#343333" if is_light else "#FFFFFF",
            'destaque': "#DE2020",     # Vermelho
            'sucesso': "#107C10",      # Verde (modificado)
            'fundo': "#FFFFFF" if is_light else "#2B2B2B",
            'texto': "#333333" if is_light else "#FFFFFF",
            'texto_card': "#FF5722",    # Laranja Interest (mantido fixo)
            'fundo_card': "#FFFFFF" if is_light else "#2B2B2B",
            'borda': "#E0E0E0" if is_light else "#555555"
        }
    
    def setup_interface(self):
        """Configura a interface do usuário"""
        # Atualizar a cor do container existente
        self.container.configure(fg_color=self.cores['fundo'])
        
        # Cabeçalho com logo e informações
        self.criar_cabecalho()
        
        # Área principal dividida em duas colunas
        self.criar_area_principal()

    def criar_cabecalho(self):
        """Cria o cabeçalho com logo e informações"""
        header = ctk.CTkFrame(self.container, fg_color=self.cores['fundo'], height=60)
        header.pack(fill="x", pady=0)
        header.pack_propagate(False)
        
        # Frame para a logo
        logo_frame = ctk.CTkFrame(header, fg_color="transparent")
        logo_frame.pack(side="left", padx=20)
        
        # Carregando e exibindo a logo
        try:
            # Obter caminho base do projeto
            if hasattr(sys, '_MEIPASS'):
                base_path = sys._MEIPASS
            else:
                # Subir 4 níveis: dialogs -> ui -> app -> raiz do projeto
                current_dir = os.path.dirname(__file__)  # dialogs
                ui_dir = os.path.dirname(current_dir)    # ui
                app_dir = os.path.dirname(ui_dir)        # app
                base_path = os.path.dirname(app_dir)     # raiz do projeto
            
            # Construir caminhos das imagens usando APP_CONFIG
            logo_light = os.path.join(base_path, APP_CONFIG['icons']['logo_light'])
            logo_dark = os.path.join(base_path, APP_CONFIG['icons']['logo_dark'])
            
            logger.debug(f"[LOGO] Caminho base: {base_path}")
            logger.debug(f"[LOGO] Caminho light: {logo_light}")
            logger.debug(f"[LOGO] Caminho dark: {logo_dark}")
            
            if os.path.exists(logo_light) and os.path.exists(logo_dark):
                # Carregar imagens
                light_image = Image.open(logo_light)
                dark_image = Image.open(logo_dark)
                
                # Definir tamanho para o logo
                logo_width = 200
                logo_height = int(logo_width * (65.2/318.6))
                
                # Criar e armazenar a referência da imagem
                self.images['logo'] = ctk.CTkImage(
                    light_image=light_image,
                    dark_image=dark_image,
                    size=(logo_width, logo_height)
                )
                
                # Criar label com a imagem
                logo_label = ctk.CTkLabel(
                    logo_frame,
                    image=self.images['logo'],
                    text=""
                )
                logo_label.pack()
                logger.info("[LOGO] Logo carregado com sucesso")
                
            else:
                raise FileNotFoundError(f"Arquivos de logo não encontrados. Light: {os.path.exists(logo_light)}, Dark: {os.path.exists(logo_dark)}")
            
        except Exception as e:
            logger.error(f"[LOGO] Erro ao carregar logo: {str(e)}")
            # Fallback para texto
            ctk.CTkLabel(
                logo_frame,
                text="INTEREST ENGENHARIA",
                font=("Arial Black", 24),
                text_color=self.cores['primaria']
            ).pack()
        
        # Informações do relatório
        info_frame = ctk.CTkFrame(header, fg_color="transparent")
        info_frame.pack(side="right", padx=20)
        
        # Buscar informações do banco
        equipe = "N/A"
        gerador = "N/A"
        
        try:
            # Buscar nome da equipe
            if self.user_data and self.user_data.get('equipe_id'):
                equipe_query = "SELECT nome FROM equipes WHERE id = %s"
                equipe_result = self.db.execute_query(equipe_query, (self.user_data['equipe_id'],))
                if equipe_result and equipe_result[0]:
                    equipe = equipe_result[0]['nome']
            
            # Usar nome do usuário como gerador
            if self.user_data and self.user_data.get('name_id'):
                gerador = self.user_data['name_id']
        except Exception as e:
            logger.error(f"Erro ao buscar informações do relatório: {e}")
        
        info = [
            ("Equipe:", equipe),
            ("Gerado Por:", gerador),
            ("Data:", datetime.now().strftime("%d/%m/%Y"))
        ]
        
        for label, valor in info:
            frame = ctk.CTkFrame(info_frame, fg_color="transparent")
            frame.pack(side="left", padx=15)
            
            ctk.CTkLabel(
                frame,
                text=label,
                font=("Arial", 12),
                text_color=self.cores['secundaria']  # Mudando a cor do texto
            ).pack(side="left", padx=5)
            
            ctk.CTkLabel(
                frame,
                text=valor,
                font=("Arial", 12, "bold"),
                text_color=self.cores['secundaria']  # Mudando a cor do texto
            ).pack(side="left")
        
        # Alterar o botão de impressão para seguir o tema
        print_button = ctk.CTkButton(
            info_frame,
            text="Salvar PDF",
            command=self.salvar_relatorio,
            font=("Arial", 12),
            fg_color=self.cores['primaria'],
            hover_color="#CE461B",  # Cor de hover padrão do projeto
            width=80
        )
        print_button.pack(side="left", padx=15)
    
    def criar_area_principal(self):
        # Frame principal com duas colunas
        main_frame = ctk.CTkFrame(self.container, fg_color=self.cores['fundo'])
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Configurar o grid do main_frame
        main_frame.grid_columnconfigure(0, weight=7)  # 70% para coluna esquerda
        main_frame.grid_columnconfigure(1, weight=3)  # 30% para coluna direita
        main_frame.grid_rowconfigure(0, weight=1)     # Permite expansão vertical
        
        # Frame geral da coluna esquerda
        frame_esquerda = ctk.CTkFrame(
            main_frame,
            fg_color=self.cores['fundo_card'],
            border_width=1,
            border_color=self.cores['borda']
        )
        frame_esquerda.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Configurar grid do frame esquerda para expansão
        frame_esquerda.grid_rowconfigure(1, weight=1)  # Row do frame_grafico expande
        frame_esquerda.grid_columnconfigure(0, weight=1)
        
        # Indicadores principais (row 0)
        frame_indicadores = ctk.CTkFrame(frame_esquerda, fg_color=self.cores['fundo_card'], height=100)
        frame_indicadores.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        frame_indicadores.grid_propagate(False)
        self.criar_indicadores_principais(frame_indicadores)
        
        # Container do gráfico (row 1 - expansível)
        frame_grafico = ctk.CTkFrame(frame_esquerda, fg_color=self.cores['fundo_card'])
        frame_grafico.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))
        self.criar_grafico_combinado(frame_grafico)
        
        # Legendas (row 2)
        frame_legendas = ctk.CTkFrame(
            frame_esquerda,
            fg_color=self.cores['fundo_card'],
            height=60,
            border_width=1,            # Adiciona borda
            border_color=self.cores['borda']  # Usa a cor de borda padrão
        )
        frame_legendas.grid(row=2, column=0, sticky="ew", padx=5, pady=(0, 5))
        frame_legendas.grid_propagate(False)
        self.criar_legenda_unificada(frame_legendas)
        
        # Frame geral da coluna direita
        frame_direita = ctk.CTkFrame(
            main_frame,
            fg_color=self.cores['fundo_card'],
            border_width=1,
            border_color=self.cores['borda']
        )
        frame_direita.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        # Configurar grid do frame direita para expansão
        frame_direita.grid_rowconfigure(0, weight=1)
        frame_direita.grid_columnconfigure(0, weight=1)
        
        # Frame para controle de atrasos
        frame_atrasos = ctk.CTkFrame(
            frame_direita,
            fg_color=self.cores['fundo_card']
        )
        frame_atrasos.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.criar_controle_atrasos(frame_atrasos)
        
        # Vincular evento de redimensionamento da janela
        self.bind('<Configure>', self.atualizar_layout)

    def atualizar_layout(self, event=None):
        """Atualiza as proporções quando a janela é redimensionada"""
        if event and event.widget == self:
            largura = event.width
            altura = event.height
            
            # Garantir tamanho mínimo
            if largura < 1300 or altura < 700:
                return
            
            # Atualizar larguras das colunas
            for widget in self.container.winfo_children():
                if isinstance(widget, ctk.CTkFrame):
                    for col in widget.winfo_children():
                        if col.winfo_name() == '!ctkframe':  # Coluna esquerda
                            col.configure(width=int(largura * 0.7))
                        elif col.winfo_name() == '!ctkframe2':  # Coluna direita
                            col.configure(width=int(largura * 0.3))
            
            # Forçar atualização do canvas do gráfico
            if hasattr(self, 'canvas'):
                self.atualizar_grafico()

    def criar_indicadores_principais(self, parent):
        # Frame principal dos indicadores sem borda
        frame = ctk.CTkFrame(
            parent,
            fg_color=self.cores['fundo_card'],
            border_width=0  # Removida a borda intermediária
        )
        frame.pack(fill="x", pady=(0, 5))
        
        # Container interno para os cards com padding
        container = ctk.CTkFrame(frame, fg_color="transparent")
        container.pack(fill="x", padx=10, pady=10)
        
        # Calcular valores dos indicadores
        indicadores = [
            ("Indicador Semana Anterior", self.calcular_valor_periodo('semana_anterior'), "▲" if self.calcular_valor_periodo('semana_anterior') >= self.calcular_valor_periodo('semana_atual') else "▼"),
            ("Indicador Semana Atual", self.calcular_valor_periodo('semana_atual'), "▲" if self.calcular_valor_periodo('semana_atual') >= self.calcular_valor_periodo('semana_anterior') else "▼"),
            ("Indicador Média Semestral", self.calcular_valor_periodo('semestral'), "▲" if self.calcular_valor_periodo('semestral') >= self.calcular_valor_periodo('anual') else "▼"),
            ("Indicador Média Anual", self.calcular_valor_periodo('anual'), "▲" if self.calcular_valor_periodo('anual') >= self.calcular_valor_periodo('semestral') else "▼")
        ]

        for titulo, valor, tendencia in indicadores:
            # Card individual com borda mais suave
            card = ctk.CTkFrame(
                container,
                fg_color=self.cores['fundo_card'],
                border_width=1,
                border_color=self.cores['borda']
            )
            card.pack(side="left", expand=True, fill="both", padx=5)
            
            ctk.CTkLabel(
                card,
                text=titulo,
                font=("Arial", 12),
                text_color=self.cores['texto_card']
            ).pack(pady=(10, 5))
            
            valor_frame = ctk.CTkFrame(card, fg_color="transparent")
            valor_frame.pack(pady=(0, 10))
            
            ctk.CTkLabel(
                valor_frame,
                text=f"{valor:.1f}%",  # Formatando para uma casa decimal
                font=("Arial Black", 24),
                text_color=self.cores['primaria']
            ).pack(side="left", padx=5)
            
            # Modificado: Cor fixa para cada símbolo
            cor_tendencia = self.cores['sucesso'] if tendencia == "▲" else self.cores['destaque']  # Verde para ▲, Vermelho para ▼
            ctk.CTkLabel(
                valor_frame,
                text=tendencia,
                font=("Arial", 24),  # Aumentado de 18 para 24
                text_color=cor_tendencia
            ).pack(side="left")
    
    def criar_grafico_combinado(self, parent):
        frame = ctk.CTkFrame(
            parent, 
            fg_color=self.cores['fundo_card'], 
            border_width=1, 
            border_color=self.cores['borda']
        )
        frame.pack(fill="both", expand=True)
        
        # Título do gráfico
        ctk.CTkLabel(
            frame,
            text="ANÁLISE INTEGRADA DE INDICADORES E ATRASOS",
            font=("Arial Black", 14),
            text_color=self.cores['texto_card']
        ).pack(pady=10)
        
        # Canvas para o gráfico
        self.canvas = ctk.CTkCanvas(
            frame,
            bg=self.cores['fundo_card'],
            height=500,
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Converter dados do banco para o formato do gráfico
        self.dados_grafico = {
            'Semana Anterior': {
                'valor': self.calcular_valor_periodo('semana_anterior'),
                'tempo': self.calcular_tempo_periodo('semana_anterior'),
                'atrasos': self.calcular_atrasos_periodo('semana_anterior'),
                'cor': '#015BFF'
            },
            'Semana Atual': {
                'valor': self.calcular_valor_periodo('semana_atual'),
                'tempo': self.calcular_tempo_periodo('semana_atual'),
                'atrasos': self.calcular_atrasos_periodo('semana_atual'),
                'cor': '#DE2020'
            },
            'Média Semestral': {
                'valor': self.calcular_valor_periodo('semestral'),
                'tempo': self.calcular_tempo_periodo('semestral'),
                'atrasos': self.calcular_atrasos_periodo('semestral'),
                'cor': '#0F510C'
            },
            'Média Anual': {
                'valor': self.calcular_valor_periodo('anual'),
                'tempo': self.calcular_tempo_periodo('anual'),
                'atrasos': self.calcular_atrasos_periodo('anual'),
                'cor': '#FFB800'
            }
        }
        
        # Vincular evento de redimensionamento
        self.canvas.bind('<Configure>', self.atualizar_grafico)

    def calcular_valor_periodo(self, periodo):
        """Calcula o valor percentual para o período"""
        try:
            dados_periodo = self.dados_atrasos_periodos.get(periodo, {})
            if not dados_periodo:
                return 0
            
            # Calcular média dos valores de eficiência
            total_atividades = sum(item['quantidade'] for item in dados_periodo.values())
            if total_atividades == 0:
                return 100
            
            return round((1 - (total_atividades / 100)) * 100, 2)
        except Exception as e:
            logger.error(f"Erro ao calcular valor do período {periodo}: {e}")
            return 0

    def calcular_tempo_periodo(self, periodo):
        """Calcula o tempo total de atrasos para o período"""
        try:
            dados_periodo = self.dados_atrasos_periodos.get(periodo, {})
            if not dados_periodo:
                return 0
            
            # Somar todos os tempos de atraso
            return sum(item['tempo'] for item in dados_periodo.values())
        except Exception as e:
            logger.error(f"Erro ao calcular tempo do período {periodo}: {e}")
            return 0

    def calcular_atrasos_periodo(self, periodo):
        """Calcula os atrasos agrupados por motivo para o período"""
        try:
            dados_periodo = self.dados_atrasos_periodos.get(periodo, {})
            if not dados_periodo:
                return {'material': 0, 'equipamento': 0, 'mao_obra': 0}
            
            # Agrupar atrasos por categoria
            atrasos = {
                'material': 0,
                'equipamento': 0,
                'mao_obra': 0
            }
            
            for motivo, dados in dados_periodo.items():
                # Classificar o motivo em uma das categorias
                if 'material' in motivo.lower():
                    atrasos['material'] += dados['quantidade']
                elif 'equip' in motivo.lower():
                    atrasos['equipamento'] += dados['quantidade']
                else:
                    atrasos['mao_obra'] += dados['quantidade']
            
            return atrasos
        except Exception as e:
            logger.error(f"Erro ao calcular atrasos do período {periodo}: {e}")
            return {'material': 0, 'equipamento': 0, 'mao_obra': 0}

    def atualizar_grafico(self, event=None):
        """Atualiza o gráfico quando o canvas é redimensionado"""
        if hasattr(self, 'dados_grafico'):
            self.desenhar_grafico(self.dados_grafico)

    def desenhar_grafico(self, dados):
        # Limpar canvas
        self.canvas.delete('all')
        
        # Dimensões do gráfico
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        if width <= 1 or height <= 1:
            return
        
        margem = 60
        grafico_width = width - 2 * margem
        grafico_height = height - 2 * margem
        
        # Ajustar cores baseadas no tema
        is_light = ctk.get_appearance_mode().lower() == "light"
        cor_texto = "#333333" if is_light else "#FFFFFF"
        cor_grade = "#E0E0E0" if is_light else "#555555"
        
        # Desenhar eixos
        self.canvas.create_line(margem, height-margem, width-margem, height-margem, fill=cor_texto, width=2)  # X
        self.canvas.create_line(margem, height-margem, margem, margem, fill=cor_texto, width=2)  # Y
        self.canvas.create_line(width-margem, height-margem, width-margem, margem, fill=cor_texto, width=2)  # Y direito
        
        # Desenhar linhas de grade e valores dos eixos
        num_linhas = 10
        for i in range(num_linhas + 1):
            y = height - margem - (i * grafico_height / num_linhas)
            self.canvas.create_line(margem-5, y, width-margem, y, fill=cor_grade, dash=(2,4))
            
            # Valor percentual (esquerda)
            valor_percent = i * 10
            self.canvas.create_text(
                margem-20, y, 
                text=f'{valor_percent}%', 
                anchor='e',
                fill=cor_texto
            )
            
            # Valor tempo (direita)
            valor_tempo = i
            self.canvas.create_text(
                width-margem+20, y, 
                text=f'{valor_tempo}d', 
                anchor='w',
                fill=cor_texto
            )
        
        # Cores para tipos de atrasos
        cores_atrasos = {
            'motivo': '#FF6B6B',
            'tempo': '#4ECDC4'
        }
        
        # Ajuste das larguras das barras
        bar_width_principal = grafico_width / (len(dados) * 3)
        bar_width_atraso = bar_width_principal * 0.4
        
        x = margem + bar_width_principal
        
        # Lista para armazenar pontos da linha de tempo
        pontos_linha = []
        
        for nome, info in dados.items():
            # Calcular alturas
            altura_valor = (info['valor'] * grafico_height) / 100
            altura_tempo = (info['tempo'] * grafico_height) / 10
            
            # Desenhar barra principal (valor)
            self.canvas.create_rectangle(
                x, height-margem-altura_valor,
                x + bar_width_principal, height-margem,
                fill=info['cor'],
                outline='white'
            )
            
            # Valor percentual
            self.canvas.create_text(
                x + bar_width_principal/2, height-margem-altura_valor-10,
                text=f'{info["valor"]}%',
                anchor='s',
                font=('Arial', 8, 'bold'),
                fill=cor_texto
            )
            
            # Desenhar barras de atraso
            if 'atrasos' in info:
                x_atraso = x + bar_width_principal + 5
                
                # Motivo do atraso
                total_motivos = sum(info['atrasos'].values())
                altura_motivo = (total_motivos * grafico_height) / 100
                
                self.canvas.create_rectangle(
                    x_atraso, height-margem-altura_motivo,
                    x_atraso + bar_width_atraso, height-margem,
                    fill=cores_atrasos['motivo'],
                    outline='white'
                )
                
                if total_motivos > 0:
                    self.canvas.create_text(
                        x_atraso + bar_width_atraso/2, height-margem-altura_motivo-5,
                        text=str(total_motivos),
                        anchor='s',
                        font=('Arial', 7),
                        fill=cor_texto
                    )
                
                # Barra de tempo
                altura_tempo_atraso = (info['tempo'] * grafico_height) / 10
                self.canvas.create_rectangle(
                    x_atraso + bar_width_atraso + 2, height-margem-altura_tempo_atraso,
                    x_atraso + 2*bar_width_atraso + 2, height-margem,
                    fill=cores_atrasos['tempo'],
                    outline='white'
                )
                
                if info['tempo'] > 0:
                    self.canvas.create_text(
                        x_atraso + 1.5*bar_width_atraso + 2, height-margem-altura_tempo_atraso-5,
                        text=f"{info['tempo']}d",
                        anchor='s',
                        font=('Arial', 7),
                        fill=cor_texto
                    )
            
            # Adicionar ponto para linha de tempo
            centro_x = x + bar_width_principal/2
            centro_y = height-margem-altura_tempo
            pontos_linha.extend([centro_x, centro_y])
            
            # Círculo indicador de tempo
            self.canvas.create_oval(
                centro_x-4, centro_y-4,
                centro_x+4, centro_y+4,
                fill='white',
                outline=info['cor'],
                width=2
            )
            
            x += bar_width_principal * 3
        
        # Desenhar linha conectando os pontos de tempo
        if len(pontos_linha) >= 4:
            self.canvas.create_line(
                pontos_linha,
                fill=cor_texto,
                width=2,
                smooth=True,
                dash=(5,2)
            )
        
        # Atualizar cores dos textos
        for texto_id in self.canvas.find_withtag('text'):
            self.canvas.itemconfig(texto_id, fill=cor_texto)

    def criar_legenda_unificada(self, frame):
        # Título da legenda
        ctk.CTkLabel(
            frame,
            text="LEGENDAS",
            font=("Arial Black", 14),
            text_color=self.cores['texto_card']
        ).pack(pady=10)
        
        # Frame único para todas as legendas
        legendas_container = ctk.CTkFrame(frame, fg_color="transparent")
        legendas_container.pack(fill="x", padx=10, pady=5)
        
        # Frame para linha única de legendas
        linha_frame = ctk.CTkFrame(legendas_container, fg_color="transparent")
        linha_frame.pack(fill="x")
        
        # Tamanho aumentado para os quadrados de cor
        square_size = 20  # Aumentado de 12 para 20
        
        # Todos os indicadores em uma linha
        for nome, info in self.dados_grafico.items():
            item_frame = ctk.CTkFrame(linha_frame, fg_color="transparent")
            item_frame.pack(side="left", padx=5, fill="x", expand=True)
            
            cor_box = ctk.CTkCanvas(
                item_frame,
                width=square_size,
                height=square_size,
                highlightthickness=0
            )
            cor_box.pack(side="left", padx=2)
            cor_box.create_rectangle(0, 0, square_size, square_size, fill=info['cor'], outline='')
            
            ctk.CTkLabel(
                item_frame,
                text=nome,
                font=("Arial", 15),
                text_color=self.cores['texto_card']
            ).pack(side="left", padx=2)
        
        # Adicionar indicadores de atraso na mesma linha
        indicadores_atraso = {
            'Motivo do Atraso': '#FF6B6B',
            'Tempo de Atraso': '#4ECDC4'
        }
        
        for tipo, cor in indicadores_atraso.items():
            item_frame = ctk.CTkFrame(linha_frame, fg_color="transparent")
            item_frame.pack(side="left", padx=5, fill="x", expand=True)
            
            cor_box = ctk.CTkCanvas(
                item_frame,
                width=square_size,
                height=square_size,
                highlightthickness=0
            )
            cor_box.pack(side="left", padx=2)
            cor_box.create_rectangle(0, 0, square_size, square_size, fill=cor, outline='')
            
            ctk.CTkLabel(
                item_frame,
                text=tipo,
                font=("Arial", 15),
                text_color=self.cores['texto_card']
            ).pack(side="left", padx=2)
        
        # Ajustar cores dos textos da legenda
        for widget in frame.winfo_children():
            if isinstance(widget, ctk.CTkLabel):
                widget.configure(text_color=self.cores['texto_card'])
    
    def criar_controle_atrasos(self, parent):
        frame = ctk.CTkFrame(parent, fg_color=self.cores['fundo_card'])
        frame.pack(fill="both", expand=True)
        
        # Título com período
        titulo_frame = ctk.CTkFrame(frame, fg_color="transparent")
        titulo_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            titulo_frame,
            text="CONTROLE DE ATRASOS",
            font=("Arial Black", 14),
            text_color=self.cores['texto_card']
        ).pack(side="left", padx=10)
        
        ctk.CTkLabel(
            titulo_frame,
            text="(Semana Atual)",
            font=("Arial", 12),
            text_color=self.cores['texto_card']
        ).pack(side="left")
        
        # Container para a lista com scroll
        lista_container = ctk.CTkFrame(frame, fg_color="transparent")
        lista_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Cabeçalho
        header_frame = ctk.CTkFrame(lista_container, fg_color=self.cores['primaria'], height=35)
        header_frame.pack(fill="x", pady=(0, 5))
        header_frame.pack_propagate(False)
        
        # Ajuste nas proporções das colunas
        colunas = [
            ('Motivo', 0.4, "w"),      # 40%
            ('Qtd.', 0.15, "center"),  # 15%
            ('Tempo', 0.15, "center"), # 15%
            ('Impacto', 0.3, "center") # 30%
        ]
        
        # Largura base para cálculos
        largura_base = 350
        
        for texto, largura, anchor in colunas:
            col_frame = ctk.CTkFrame(header_frame, fg_color="transparent", width=int(largura_base*largura))
            col_frame.pack(side="left", fill="y", padx=2)
            col_frame.pack_propagate(False)
            
            label = ctk.CTkLabel(
                col_frame,
                text=texto,
                font=("Arial", 12, "bold"),
                text_color="white"
            )
            label.pack(expand=True, padx=5, pady=5)
        
        # Lista de atrasos
        lista_frame = ctk.CTkScrollableFrame(lista_container, fg_color="transparent")
        lista_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Cores para níveis de impacto
        cores_impacto = {
            'Alto': '#DE2020',    # Vermelho
            'Médio': '#FFB800',   # Amarelo
            'Baixo': '#0F510C'    # Verde
        }
        
        if not self.dados_atrasos:
            # Mostrar mensagem quando não houver dados
            ctk.CTkLabel(
                lista_frame,
                text="Nenhum registro de atraso encontrado",
                font=("Arial", 12),
                text_color=self.cores['texto_card']
            ).pack(pady=20)
            return
        
        # Usar dados do banco
        for motivo, dados in self.dados_atrasos.items():
            item_frame = ctk.CTkFrame(
                lista_frame, 
                fg_color=self.cores['fundo_card'],
                height=39,  # Aumentado um pouco mais
                border_width=1,
                border_color=self.cores['borda']
            )
            item_frame.pack(fill="x", pady=(0, 3))  # Aumentado o espaço entre itens
            item_frame.pack_propagate(False)
            
            # Container interno com padding ajustado
            content_frame = ctk.CTkFrame(
                item_frame, 
                fg_color="transparent"
            )
            content_frame.pack(fill="both", expand=True, padx=3, pady=3)  # Aumentado padding para mostrar a borda
            
            # Motivo (40%)
            motivo_frame = ctk.CTkFrame(content_frame, fg_color="transparent", width=int(largura_base*0.4))
            motivo_frame.pack(side="left", fill="y", padx=(2, 0))  # Adicionado padding à esquerda
            motivo_frame.pack_propagate(False)
            ctk.CTkLabel(
                motivo_frame,
                text=str(motivo) if motivo else "Sem motivo",
                font=("Arial", 11),
                text_color=self.cores['texto_card']
            ).pack(side="left", padx=5, pady=5)
            
            # Quantidade (15%)
            qtd_frame = ctk.CTkFrame(content_frame, fg_color="transparent", width=int(largura_base*0.15))
            qtd_frame.pack(side="left", fill="y")
            qtd_frame.pack_propagate(False)
            ctk.CTkLabel(
                qtd_frame,
                text=str(dados['quantidade']),
                font=("Arial", 11),
                text_color=self.cores['texto_card']
            ).pack(expand=True, pady=5)
            
            # Tempo (15%)
            tempo_frame = ctk.CTkFrame(content_frame, fg_color="transparent", width=int(largura_base*0.15))
            tempo_frame.pack(side="left", fill="y")
            tempo_frame.pack_propagate(False)
            ctk.CTkLabel(
                tempo_frame,
                text=f"{dados['tempo']}d",
                font=("Arial", 11),
                text_color=self.cores['texto_card']
            ).pack(expand=True, pady=5)
            
            # Impacto (30%)
            impacto_frame = ctk.CTkFrame(content_frame, fg_color="transparent", width=int(largura_base*0.3))
            impacto_frame.pack(side="left", fill="y")
            impacto_frame.pack_propagate(False)
            ctk.CTkLabel(
                impacto_frame,
                text=dados['impacto'],
                font=("Arial", 11),
                text_color=cores_impacto[dados['impacto']]
            ).pack(expand=True, pady=5)

    def salvar_relatorio(self):
        """Prepara os dados e salva o relatório PDF"""
        # Coletar dados do dashboard
        dados_dashboard = {
            'equipe': 'SPCS',
            'gerado_por': 'WRP',
            'indicadores': {
                'semana_anterior': '100%',
                'semana_atual': '90%',
                'media_semestral': '20%',
                'media_anual': '0.5%'
            },
            'atrasos': self.dados_atrasos
        }
        
        # Criar instância do printer
        printer = DashboardPrinter(dados_dashboard)
        
        # Abrir diálogo para salvar arquivo
        arquivo = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        if arquivo:
            printer.gerar_relatorio(arquivo)

    def _on_theme_change_callback(self, *args):
        """Callback para mudanças no tema"""
        try:
            logger.info(f"[THEME] Detectada mudança de tema para: {ctk.get_appearance_mode()}")
            if hasattr(self, '_on_theme_change_callback_id'):
                self.after_cancel(self._on_theme_change_callback_id)
            self._on_theme_change_callback_id = self.after(100, self._on_theme_change)
        except Exception as e:
            logger.error(f"[THEME] Erro no callback de tema: {e}")
            
    def _on_theme_change(self):
        """Atualiza a interface quando o tema muda"""
        try:
            logger.info(f"[THEME] Atualizando interface para tema: {ctk.get_appearance_mode()}")
            
            # Atualizar cores
            self.setup_cores()
            
            # Atualizar container principal
            if hasattr(self, 'container'):
                self.container.configure(fg_color=self.cores['fundo'])
            
            # Atualizar todos os frames e labels
            self._update_widget_colors(self)
            
            # Forçar atualização do canvas e lista de atrasos
            if hasattr(self, 'canvas'):
                self.canvas.configure(bg=self.cores['fundo_card'])
                if hasattr(self, 'dados_grafico'):
                    self.desenhar_grafico(self.dados_grafico)
            
            if hasattr(self, 'lista_frame'):
                for item in self.lista_frame.winfo_children():
                    if isinstance(item, ctk.CTkFrame):
                        item.configure(
                            fg_color=self.cores['fundo_card'],
                            border_color=self.cores['borda']
                        )
                        for label in item.winfo_children():
                            if isinstance(label, ctk.CTkLabel):
                                label.configure(text_color=self.cores['texto'])
            
            logger.info("[THEME] Atualização de tema concluída com sucesso")
            
        except Exception as e:
            logger.error(f"[THEME] Erro ao atualizar tema: {e}")
            
    def _update_widget_colors(self, widget):
        """Atualiza recursivamente as cores de todos os widgets"""
        try:
            for child in widget.winfo_children():
                # Atualizar cor do frame
                if isinstance(child, ctk.CTkFrame):
                    if 'transparent' not in str(child.cget('fg_color')):
                        child.configure(fg_color=self.cores['fundo_card'])
                
                # Atualizar cor do label
                elif isinstance(child, ctk.CTkLabel):
                    if not child.cget('image'):
                        texto = child.cget('text')
                        # Preservar cores dos indicadores de tendência
                        if texto in ["▲", "▼"]:
                            cor = self.cores['sucesso'] if texto == "▲" else self.cores['destaque']
                            child.configure(text_color=cor)
                        # Preservar cores dos indicadores de impacto
                        elif texto in ["Alto", "Médio", "Baixo"]:
                            cores_impacto = {
                                'Alto': self.cores['destaque'],    # Vermelho
                                'Médio': '#FFB800',   # Amarelo
                                'Baixo': self.cores['sucesso']    # Verde
                            }
                            child.configure(text_color=cores_impacto[texto])
                        # Verificar se é um label de título ou cabeçalho
                        elif "Arial Black" in str(child.cget('font')):
                            child.configure(text_color=self.cores['texto_card'])
                        else:
                            child.configure(text_color=self.cores['texto'])
                
                # Atualizar cor do botão
                elif isinstance(child, ctk.CTkButton):
                    if child.cget('fg_color') != self.cores['primaria']:
                        child.configure(text_color=self.cores['texto'])
                
                # Atualizar canvas do gráfico
                elif isinstance(child, ctk.CTkCanvas):
                    child.configure(bg=self.cores['fundo_card'])
                    if hasattr(self, 'dados_grafico'):
                        self.desenhar_grafico(self.dados_grafico)
                
                # Recursivamente atualizar widgets filhos
                if child.winfo_children():
                    self._update_widget_colors(child)
                    
        except Exception as e:
            logger.error(f"[THEME] Erro ao atualizar cores do widget: {e}")

    def cleanup(self):
        """Limpa todos os recursos antes de destruir a janela"""
        try:
            logger.info("Iniciando limpeza de recursos do DashboardDaily")
            
            # Cancelar callbacks pendentes
            if hasattr(self, '_on_theme_change_callback_id'):
                self.after_cancel(self._on_theme_change_callback_id)
                
            # Remover callback de tema
            ctk.AppearanceModeTracker.remove(self._on_theme_change_callback)
            
            # Limpar referências cíclicas
            self.parent = None
            self.db = None
            self.user_data = None
            
            # Limpar dados
            self.dados_atrasos.clear()
            self.dados_atrasos_periodos.clear()
            
            # Limpar imagens
            for img in self.images.values():
                img = None
            self.images.clear()
            
            # Forçar coleta de lixo
            import gc
            gc.collect()
            
            logger.info("Limpeza de recursos do DashboardDaily concluída")
            
        except Exception as e:
            logger.error(f"Erro durante limpeza de recursos: {e}", exc_info=True)

    def destroy(self):
        """Sobrescreve o método destroy para garantir limpeza de recursos"""
        try:
            self.cleanup()
        finally:
            super().destroy()

    def __del__(self):
        """Destrutor da classe"""
        try:
            # Limpar referências das imagens
            self.images.clear()
            
            # Remover callback ao destruir a janela
            if hasattr(self, '_on_theme_change_callback_id'):
                self.after_cancel(self._on_theme_change_callback_id)
            ctk.AppearanceModeTracker.remove(self._on_theme_change_callback)
            logger.debug("[THEME] Callback de tema removido")
        except Exception as e:
            logger.error(f"[THEME] Erro ao limpar recursos: {e}")