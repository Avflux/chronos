import customtkinter as ctk
from tkinter import ttk, messagebox
import logging
from datetime import datetime, timedelta
from ...database.connection import DatabaseConnection

logger = logging.getLogger(__name__)

class SearchFrame(ctk.CTkFrame):
    def __init__(self, parent, user_data):
        super().__init__(parent)
        self.db = DatabaseConnection()
        self.user_data = user_data
        
        # Configurações de estilo
        self.configure(fg_color="transparent")
        
        # Lista de meses para o filtro
        self.meses = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ]
        
        # Lista de anos para o filtro
        current_year = datetime.now().year
        self.anos = [str(year) for year in range(current_year, current_year + 6)]
        
        # Lista de períodos
        self.periodos = ["Todos", "Dia Atual", "Semana Atual"]
        
        # Inicializar variáveis dos menus suspensos
        self.status_combo = None
        self.period_combo = None
        self.month_combo = None
        self.year_combo = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Configura a interface do frame"""
        # Container principal
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=15)
        
        # Frame de pesquisa com fundo escuro
        search_frame = ctk.CTkFrame(main_container, fg_color="#2b2b2b", corner_radius=15)
        search_frame.pack(fill="x", pady=(0, 10))
        
        # Título e subtítulo
        title_frame = ctk.CTkFrame(search_frame, fg_color="transparent")
        title_frame.pack(fill="x", padx=15, pady=10)
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="Pesquisar Atividades",
            font=("Roboto", 28, "bold"),
            text_color="#ff5722"
        )
        title_label.pack(anchor="w")
        
        subtitle_label = ctk.CTkLabel(
            title_frame,
            text="Pesquise e filtre atividades da sua equipe",
            font=("Roboto", 14),
            text_color="#888888"
        )
        subtitle_label.pack(anchor="w")
        
        # Frame único para pesquisa e filtros (horizontal)
        controls_frame = ctk.CTkFrame(search_frame, fg_color="transparent")
        controls_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        # Configuração dos menus suspensos
        dropdown_style = {
            "fg_color": "#ff5722",
            "button_color": "#e64a19",
            "button_hover_color": "#ff7043",
            "dropdown_hover_color": "#ff7043",
            "dropdown_fg_color": "#ff5722",
            "height": 32,
            "width": 120  # Largura fixa para os menus
        }

        # Campo de pesquisa
        self.search_entry = ctk.CTkEntry(
            controls_frame,
            placeholder_text="Pesquisar por colaborador, descrição ou atividade...",
            height=32,
            width=300  # Largura fixa para a entrada
        )
        self.search_entry.pack(side="left", padx=(0, 5))
        self.search_entry.bind("<Return>", lambda e: self.search())

        # Botão de pesquisa
        self.search_button = ctk.CTkButton(
            controls_frame,
            text="Pesquisar",
            command=self.search,
            fg_color="#ff5722",
            hover_color="#e64a19",
            height=32,
            width=100
        )
        self.search_button.pack(side="left", padx=(0, 15))
        
        # Período
        period_label = ctk.CTkLabel(controls_frame, text="Período:", width=50)
        period_label.pack(side="left", padx=(5, 2))
        self.period_combo = ctk.CTkOptionMenu(
            controls_frame,
            values=self.periodos,
            command=self.search,
            **dropdown_style
        )
        self.period_combo.pack(side="left", padx=(0, 10))
        
        # Mês
        month_label = ctk.CTkLabel(controls_frame, text="Mês:", width=35)
        month_label.pack(side="left", padx=(5, 2))
        self.month_combo = ctk.CTkOptionMenu(
            controls_frame,
            values=["Todos"] + self.meses,
            command=self.search,
            **dropdown_style
        )
        self.month_combo.pack(side="left", padx=(0, 10))
        
        # Ano
        year_label = ctk.CTkLabel(controls_frame, text="Ano:", width=35)
        year_label.pack(side="left", padx=(5, 2))
        self.year_combo = ctk.CTkOptionMenu(
            controls_frame,
            values=["Todos"] + self.anos,
            command=self.search,
            **dropdown_style
        )
        self.year_combo.pack(side="left", padx=(0, 10))
        
        # Status (movido para o final)
        status_label = ctk.CTkLabel(controls_frame, text="Status:", width=50)
        status_label.pack(side="left", padx=(5, 2))
        self.status_combo = ctk.CTkOptionMenu(
            controls_frame,
            values=["Todos", "Ativo", "Pausado", "Concluído"],
            command=self.search,
            **dropdown_style
        )
        self.status_combo.pack(side="left", padx=(0, 0))

        # Frame para a tabela
        table_container = ctk.CTkFrame(main_container)
        table_container.pack(fill="both", expand=True)
        
        # Criar container para Treeview e Scrollbar
        tree_container = ttk.Frame(table_container)
        tree_container.pack(fill="both", expand=True)
        
        # Configurar Treeview
        self.tree = ttk.Treeview(tree_container, selectmode="browse", show="headings")
        
        # Scrollbar vertical
        vsb = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        vsb.pack(side="right", fill="y")
        
        # Scrollbar horizontal
        hsb = ttk.Scrollbar(tree_container, orient="horizontal", command=self.tree.xview)
        hsb.pack(side="bottom", fill="x")
        
        # Configurar Treeview com ambas as scrollbars
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.pack(fill="both", expand=True)
        
        # Configurar colunas
        self.tree["columns"] = (
            "colaborador", "descricao", "atividade", "inicio", "fim_previsto",
            "regressivo", "excedido", "motivo", "total"
        )
        
        # Configurar cabeçalhos
        headers = {
            "colaborador": "Colaborador",
            "descricao": "Descrição",
            "atividade": "Atividade",
            "inicio": "Início",
            "fim_previsto": "Fim Previsto",
            "regressivo": "Regressivo",
            "excedido": "Excedido",
            "motivo": "Motivo Tempo Excedido",
            "total": "Total"
        }
        
        # Colunas que devem ter o conteúdo centralizado
        center_columns = ["inicio", "fim_previsto", "regressivo", "excedido", "total"]
        
        for col in self.tree["columns"]:
            self.tree.heading(col, text=headers[col])
            # Centralizar o conteúdo das colunas especificadas
            if col in center_columns:
                self.tree.column(col, width=100, anchor="center")
            else:
                self.tree.column(col, width=100)
        
        # Ajustar larguras específicas
        self.tree.column("descricao", width=200)
        self.tree.column("atividade", width=150)
        self.tree.column("motivo", width=150)
        self.tree.column("regressivo", width=60)
        self.tree.column("excedido", width=60)
        self.tree.column("total", width=60)
        
        # Configurar estilo do Treeview
        style = ttk.Style()
        style.configure("Treeview", rowheight=25)
        style.configure("Treeview.Heading", font=("Roboto", 10, "bold"))
        
        # Realizar pesquisa inicial
        self.search()
        
    def search(self, *args):
        """Realiza a pesquisa no banco de dados com os filtros aplicados"""
        try:
            # Limpar resultados anteriores
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Obter valores dos filtros
            search_term = self.search_entry.get().strip()
            status = self.status_combo.get()
            period = self.period_combo.get()
            month = self.month_combo.get()
            year = self.year_combo.get()
            
            # Construir a query base
            query = """
                SELECT 
                    u.nome as colaborador,
                    a.description as descricao,
                    a.atividade,
                    a.start_time as inicio,
                    a.end_time as fim_previsto,
                    a.time_regress as regressivo,
                    a.time_exceeded as excedido,
                    a.reason as motivo,
                    a.total_time as total
                FROM atividades a
                JOIN usuarios u ON a.user_id = u.id
                WHERE u.equipe_id = %s
            """
            params = [self.user_data['equipe_id']]
            
            # Adicionar filtro de pesquisa
            if search_term:
                query += """ AND (
                    u.nome LIKE %s OR
                    a.description LIKE %s OR
                    a.atividade LIKE %s
                )"""
                search_pattern = f"%{search_term}%"
                params.extend([search_pattern] * 3)
            
            # Adicionar filtro de status
            if status != "Todos":
                status_map = {
                    "Ativo": "ativo = 1",
                    "Pausado": "pausado = 1",
                    "Concluído": "concluido = 1"
                }
                query += f" AND {status_map[status]}"
            
            # Adicionar filtro de período
            if period != "Todos":
                today = datetime.now().date()
                if period == "Dia Atual":
                    query += """ AND (
                        DATE(a.created_at) = %s OR 
                        (DATE(a.updated_at) = %s AND a.ativo = 1)
                    )"""
                    params.extend([today, today])
                elif period == "Semana Atual":
                    # Encontrar o início da semana (segunda-feira)
                    start_of_week = today - timedelta(days=today.weekday())
                    # Fim da semana (domingo)
                    end_of_week = start_of_week + timedelta(days=6)
                    query += """ AND (
                        DATE(a.created_at) BETWEEN %s AND %s OR
                        (DATE(a.updated_at) BETWEEN %s AND %s AND a.ativo = 1)
                    )"""
                    params.extend([start_of_week, end_of_week, start_of_week, end_of_week])
            
            # Adicionar filtros de data (mês/ano)
            if month != "Todos" or year != "Todos":
                if month != "Todos":
                    month_num = self.meses.index(month) + 1
                    query += " AND MONTH(a.created_at) = %s"
                    params.append(month_num)
                
                if year != "Todos":
                    query += " AND YEAR(a.created_at) = %s"
                    params.append(year)
            
            # Ordenar por data de criação
            query += " ORDER BY a.created_at DESC"
            
            # Executar a query
            results = self.db.execute_query(query, params)
            
            if results:
                # Preencher a tabela com os resultados
                for result in results:
                    values = (
                        result['colaborador'],
                        result['descricao'],
                        result['atividade'],
                        result['inicio'],
                        result['fim_previsto'],
                        result['regressivo'],
                        result['excedido'],
                        result['motivo'] or "",
                        result['total']
                    )
                    self.tree.insert("", "end", values=values)
                
        except Exception as e:
            logger.error(f"Erro ao realizar pesquisa: {str(e)}")
            messagebox.showerror("Erro", "Ocorreu um erro ao realizar a pesquisa.")