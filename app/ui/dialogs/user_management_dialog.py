import customtkinter as ctk
from tkinter import ttk, messagebox
import tkinter as tk
import logging
from ...database.connection import DatabaseConnection
from datetime import datetime
import bcrypt

logger = logging.getLogger(__name__)

class UserManagementFrame(ctk.CTkFrame):
    def __init__(self, parent, user_data):
        super().__init__(parent)
        
        # Armazenar dados do usuário logado
        self.user_data = user_data
        self.parent = parent
        
        # Configurar pesos do grid para responsividade
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.db = DatabaseConnection()
        
        # Dicionários para armazenar widgets
        self.entry_widgets = {}
        self.current_user_id = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Configura a interface principal com abas"""
        # Frame principal com padding reduzido
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Configurar pesos do grid no main_frame
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        
        # Tabs container
        self.tab_view = ctk.CTkTabview(self.main_frame)
        self.tab_view.pack(expand=True, fill="both")
        
        # Criar abas
        self.tab_users = self.tab_view.add("Usuários")
        self.tab_teams = self.tab_view.add("Equipes")
        self.tab_blocks = self.tab_view.add("Bloqueios")
        
        # Configurar pesos do grid em cada aba
        for tab in [self.tab_users, self.tab_teams, self.tab_blocks]:
            tab.grid_columnconfigure(0, weight=1)
            tab.grid_rowconfigure(0, weight=1)
        
        # Configurar cada aba
        self.setup_users_tab()
        self.setup_teams_tab()
        self.setup_blocks_tab()
        
    def setup_users_tab(self):
        """Configura a aba de usuários"""
        # Título da aba em negrito e laranja
        title_label = ctk.CTkLabel(
            self.tab_users,
            text="Gerenciamento de Usuários",
            font=("Roboto", 16, "bold"),
            text_color="#ff5722"
        )
        title_label.pack(pady=(10, 20))

        users_frame = ctk.CTkFrame(self.tab_users)
        users_frame.pack(expand=True, fill="both", padx=2, pady=2)
        
        # Ajustar pesos do grid para divisão 70/30
        users_frame.grid_columnconfigure(0, weight=70)  # 70% para lista
        users_frame.grid_columnconfigure(1, weight=30)  # 30% para formulário
        users_frame.grid_rowconfigure(0, weight=1)
        
        # Frame esquerdo (lista de usuários)
        left_frame = ctk.CTkFrame(users_frame, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 2), pady=0)
        
        # Frame direito (formulário)
        right_frame = ctk.CTkFrame(users_frame, fg_color="transparent")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(2, 0), pady=0)
        
        # Configurar pesos internos dos frames
        left_frame.grid_columnconfigure(0, weight=1)
        left_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)
        right_frame.grid_rowconfigure(1, weight=1)
        
        # Barra de pesquisa
        search_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        search_frame.grid(row=0, column=0, sticky="ew", padx=2, pady=(0, 2))
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text=" Buscar usuário...",
            height=32
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 2))
        self.search_entry.bind("<Return>", lambda event: self.search_users())
        
        search_btn = ctk.CTkButton(
            search_frame,
            text="Buscar",
            width=80,
            height=32,
            command=self.search_users,
            fg_color="#ff5722",
            hover_color="#ce461b"
        )
        search_btn.pack(side="right")
        
        # Lista de usuários
        self.setup_users_list(left_frame)
        
        # Formulário de usuário
        self.setup_user_form(right_frame)
        
        # Carregar usuários
        self.load_users()

    def setup_user_form(self, parent):
        """Configura o formulário de usuário com novo layout"""
        # Frame para o formulário com padding reduzido
        form_frame = ctk.CTkFrame(parent)
        form_frame.grid(row=0, column=0, sticky="nsew", pady=2)
        
        # Título do formulário
        title = ctk.CTkLabel(
            form_frame,
            text="Dados do Usuário",
            font=("Roboto", 14, "bold"),
            text_color=("#ff5722", "#ff5722")  # Definindo a cor para modo claro e escuro
        )
        title.pack(pady=(10, 15))
        
        # Frame para os campos
        fields_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        fields_frame.pack(fill="both", expand=True, padx=5)
        
        # Configuração dos campos
        fields = [
            ("nome", "Nome"),
            ("email", "Email"),
            ("name_id", "Name ID"),
            ("senha", "Senha"),
            ("equipe", "Equipe"),
            ("tipo_usuario", "Tipo"),
            ("data_entrada", "Data Entrada")
        ]
        
        for field, label in fields:
            field_frame = ctk.CTkFrame(fields_frame, fg_color="transparent")
            field_frame.pack(fill="x", pady=1)
            
            if field in ["equipe", "tipo_usuario"]:
                if field == "equipe":
                    widget = ctk.CTkComboBox(
                        field_frame,
                        values=self.get_equipes(),
                        height=28
                    )
                else:
                    widget = ctk.CTkComboBox(
                        field_frame,
                        values=["admin", "comum"],
                        height=28
                    )
            else:
                widget = ctk.CTkEntry(
                    field_frame,
                    placeholder_text=label,
                    height=28
                )
                if field == "senha":
                    widget.configure(show="*")
            
            widget.pack(fill="x")
            self.entry_widgets[field] = widget
        
        # Frame para botões lado a lado
        btn_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=5, pady=10)
        
        # Configurar grid para 2 colunas
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        
        # Botões na primeira linha
        save_btn = ctk.CTkButton(
            btn_frame,
            text="Salvar",
            height=28,
            command=self.save_user,
            fg_color="#ff5722",
            hover_color="#ce461b"
        )
        save_btn.grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        
        clear_btn = ctk.CTkButton(
            btn_frame,
            text="Limpar",
            height=28,
            command=self.clear_form,
            fg_color="transparent",
            border_width=1,
            border_color="#ff5722",
            text_color="#ff5722",
            hover_color="#fff1eb"
        )
        clear_btn.grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        
        # Botão excluir na segunda linha
        delete_btn = ctk.CTkButton(
            btn_frame,
            text="Excluir",
            height=28,
            command=self.delete_user,
            fg_color="#dc2626",
            hover_color="#991b1b"
        )
        delete_btn.grid(row=1, column=0, columnspan=2, padx=2, pady=(2,0), sticky="ew")
        
    def setup_teams_tab(self):
        """Configura a aba de equipes"""
        # Título da aba em negrito e laranja
        title_label = ctk.CTkLabel(
            self.tab_teams,
            text="Gerenciamento de Equipes",
            font=("Roboto", 16, "bold"),
            text_color=("#ff5722", "#ff5722")
        )
        title_label.pack(pady=(10, 20))

        teams_frame = ctk.CTkFrame(self.tab_teams)
        teams_frame.pack(expand=True, fill="both", padx=2, pady=2)
        
        # Ajustar pesos do grid para divisão 70/30
        teams_frame.grid_columnconfigure(0, weight=70)  # 70% para lista
        teams_frame.grid_columnconfigure(1, weight=30)  # 30% para ações
        teams_frame.grid_rowconfigure(0, weight=1)
        
        # Frame esquerdo (lista de equipes)
        left_frame = ctk.CTkFrame(teams_frame, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 2), pady=0)
        
        # Configurar peso da linha no left_frame
        left_frame.grid_columnconfigure(0, weight=1)
        left_frame.grid_rowconfigure(0, weight=0)  # Search frame
        left_frame.grid_rowconfigure(1, weight=1)  # Tree frame
        
        # Barra de pesquisa
        search_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        search_frame.grid(row=0, column=0, sticky="ew", padx=2, pady=(0, 2))
        
        self.teams_search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text=" Buscar equipe...",
            height=32
        )
        self.teams_search_entry.pack(side="left", fill="x", expand=True, padx=(0, 2))
        self.teams_search_entry.bind("<Return>", lambda event: self.search_teams())
        
        search_btn = ctk.CTkButton(
            search_frame,
            text="Buscar",
            width=80,
            height=32,
            command=self.search_teams,
            fg_color="#ff5722",
            hover_color="#ce461b"
        )
        search_btn.pack(side="right")
        
        # Lista de equipes
        tree_frame = ctk.CTkFrame(left_frame)
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)
        
        # Frame direito (ações)
        right_frame = ctk.CTkFrame(teams_frame, fg_color="transparent")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(2, 0), pady=0)
        
        # Lista de equipes
        self.teams_tree = ttk.Treeview(
            tree_frame,
            columns=("ID", "Nome", "Membros", "Data Criação"),
            show="headings",
            style="Custom.Treeview"
        )
        
        # Configurar colunas
        columns = {
            "ID": 60,
            "Nome": 200,
            "Membros": 100,
            "Data Criação": 150
        }
        
        for col, width in columns.items():
            self.teams_tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(self.teams_tree, c))
            self.teams_tree.column(col, width=width, minwidth=width)
        
        # Adicionar scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.teams_tree.yview)
        self.teams_tree.configure(yscrollcommand=scrollbar.set)
        
        # Grid para lista e scrollbar
        self.teams_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Frame direito - Gerenciamento de Equipes
        title = ctk.CTkLabel(
            right_frame,
            text="Nova Equipe",
            font=("Roboto", 14, "bold"),
            text_color=("#ff5722", "#ff5722")
        )
        title.pack(pady=(10, 15))
        
        # Frame para nova equipe
        new_team_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        new_team_frame.pack(fill="x", padx=10, pady=5)
        
        # Entrada para nova equipe
        self.team_entry = ctk.CTkEntry(
            new_team_frame,
            placeholder_text="Nome da nova equipe",
            height=28
        )
        self.team_entry.pack(fill="x", pady=5)
        self.team_entry.bind("<Return>", lambda event: self.add_team())
        
        # Frame para botões lado a lado
        btn_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        # Configurar grid para 2 colunas
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        
        # Botões na primeira linha
        add_team_btn = ctk.CTkButton(
            btn_frame,
            text="Adicionar",
            height=28,
            command=self.add_team,
            fg_color="#ff5722",
            hover_color="#ce461b"
        )
        add_team_btn.grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        
        clear_btn = ctk.CTkButton(
            btn_frame,
            text="Limpar",
            height=28,
            command=lambda: self.team_entry.delete(0, 'end'),
            fg_color="transparent",
            border_width=1,
            border_color="#ff5722",
            text_color="#ff5722",
            hover_color="#fff1eb"
        )
        clear_btn.grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        
        # Separador
        separator = ctk.CTkFrame(right_frame, height=2, fg_color="#e5e7eb")
        separator.pack(fill="x", padx=10, pady=15)
        
        # Botão excluir equipe na segunda linha
        delete_team_btn = ctk.CTkButton(
            right_frame,
            text="Excluir Equipe",
            height=32,
            command=self.delete_selected_team,
            fg_color="#dc2626",
            hover_color="#991b1b"
        )
        delete_team_btn.pack(padx=10, pady=5, fill="x")
        
        # Manter menu de contexto
        self.teams_tree.bind("<Button-3>", self.show_team_context_menu)
        
        # Carregar dados
        self.load_teams()

    def setup_blocks_tab(self):
        """Configura a aba de bloqueios"""
        # Título da aba em negrito e laranja
        title_label = ctk.CTkLabel(
            self.tab_blocks,
            text="Gerenciamento de Bloqueios",
            font=("Roboto", 16, "bold"),
            text_color=("#ff5722", "#ff5722")
        )
        title_label.pack(pady=(10, 20))

        blocks_frame = ctk.CTkFrame(self.tab_blocks)
        blocks_frame.pack(expand=True, fill="both", padx=2, pady=2)
        
        # Ajustar pesos do grid para divisão 70/30
        blocks_frame.grid_columnconfigure(0, weight=70)  # 70% para lista
        blocks_frame.grid_columnconfigure(1, weight=30)  # 30% para ações
        blocks_frame.grid_rowconfigure(0, weight=1)
        
        # Frame esquerdo (lista de bloqueios)
        left_frame = ctk.CTkFrame(blocks_frame, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 2), pady=0)
        
        # Configurar peso da linha no left_frame
        left_frame.grid_columnconfigure(0, weight=1)
        left_frame.grid_rowconfigure(0, weight=0)  # Search frame
        left_frame.grid_rowconfigure(1, weight=1)  # Tree frame
        
        # Barra de pesquisa
        search_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        search_frame.grid(row=0, column=0, sticky="ew", padx=2, pady=(0, 2))
        
        self.blocks_search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text=" Buscar usuário bloqueado...",
            height=32
        )
        self.blocks_search_entry.pack(side="left", fill="x", expand=True, padx=(0, 2))
        self.blocks_search_entry.bind("<Return>", lambda event: self.search_blocks())
        
        search_btn = ctk.CTkButton(
            search_frame,
            text="Buscar",
            width=80,
            height=32,
            command=self.search_blocks,
            fg_color="#ff5722",
            hover_color="#ce461b"
        )
        search_btn.pack(side="right")
        
        # Lista de bloqueios
        tree_frame = ctk.CTkFrame(left_frame)
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)
        
        # Frame direito (ações)
        right_frame = ctk.CTkFrame(blocks_frame, fg_color="transparent")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(2, 0), pady=0)
        
        # Lista de bloqueios
        self.blocks_tree = ttk.Treeview(
            tree_frame,
            columns=("ID", "Nome", "Equipe", "Status", "Controle"),
            show="headings",
            style="Custom.Treeview"
        )
        
        # Configurar colunas
        columns = {
            "ID": 60,
            "Nome": 200,
            "Equipe": 150,
            "Status": 100,
            "Controle": 100
        }
        
        for col, width in columns.items():
            self.blocks_tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(self.blocks_tree, c))
            self.blocks_tree.column(col, width=width, minwidth=width)
        
        # Adicionar scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.blocks_tree.yview)
        self.blocks_tree.configure(yscrollcommand=scrollbar.set)
        
        # Grid para lista e scrollbar
        self.blocks_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Frame direito - Status do Sistema
        status_title = ctk.CTkLabel(
            right_frame,
            text="Status do Sistema",
            font=("Roboto", 14, "bold"),
            text_color=("#ff5722", "#ff5722")
        )
        status_title.pack(pady=(10, 15))
        
        # Frame para indicadores
        indicators_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        indicators_frame.pack(fill="x", padx=10, pady=5)
        
        # Indicadores de status com estilo melhorado
        self.status_indicators = {}
        for status in ["Usuários Ativos", "Usuários Bloqueados", "Tentativas de Login"]:
            indicator_frame = ctk.CTkFrame(indicators_frame, fg_color="transparent")
            indicator_frame.pack(fill="x", pady=3)
            
            ctk.CTkLabel(
                indicator_frame,
                text=status,
                font=("Roboto", 12),
                anchor="w"
            ).pack(side="left", padx=2)
            
            self.status_indicators[status] = ctk.CTkLabel(
                indicator_frame,
                text="0",
                font=("Roboto", 12, "bold"),
                text_color=("#ff5722", "#ff5722")
            )
            self.status_indicators[status].pack(side="right", padx=2)
        
        # Separador
        separator = ctk.CTkFrame(right_frame, height=2, fg_color="#e5e7eb")
        separator.pack(fill="x", padx=10, pady=15)
        
        # Frame para botões
        btn_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        # Botão de alternar bloqueio
        self.block_btn = ctk.CTkButton(
            btn_frame,
            text="Bloquear/Desbloquear",
            command=self.toggle_user_lock,
            height=32,
            fg_color="#dc2626",
            hover_color="#991b1b"
        )
        self.block_btn.pack(fill="x", pady=2)
        
        # Binding para menu de contexto
        self.blocks_tree.bind("<Button-3>", self.show_block_context_menu)
        
        # Carregar bloqueios
        self.load_blocks()
        
    # Métodos auxiliares para cada aba
    def add_team(self):
        """Adiciona uma nova equipe e atualiza o ComboBox"""
        team_name = self.team_entry.get().strip()
        if not team_name:
            messagebox.showwarning("Aviso", "Digite um nome para a equipe!")
            return
                
        try:
            query = "INSERT INTO equipes (nome) VALUES (%s)"
            self.db.execute_query(query, (team_name,))
            messagebox.showinfo("Sucesso", "Equipe adicionada com sucesso!")
            self.team_entry.delete(0, 'end')
            self.load_teams()
            
            # Atualiza o ComboBox na aba de usuários
            self.update_equipes_combobox()
            
        except Exception as e:
            logger.error(f"Erro ao adicionar equipe: {e}")
            messagebox.showerror("Erro", "Erro ao adicionar equipe")

    def load_teams(self):
        """Carrega lista de equipes"""
        for item in self.teams_tree.get_children():
            self.teams_tree.delete(item)
            
        try:
            query = """
                SELECT e.id, e.nome, COUNT(u.id) as membros, e.created_at
                FROM equipes e
                LEFT JOIN usuarios u ON e.id = u.equipe_id AND u.status = TRUE
                GROUP BY e.id, e.nome, e.created_at
                ORDER BY e.nome
            """
            teams = self.db.execute_query(query)
            
            # Verificar se teams não é None e tem resultados
            if teams:
                for team in teams:
                    self.teams_tree.insert("", "end", values=(
                        team['id'],
                        team['nome'],
                        team['membros'],
                        team['created_at'].strftime('%d/%m/%Y %H:%M')
                    ))
            else:
                logger.info("Nenhuma equipe encontrada no banco de dados")
            
        except Exception as e:
            logger.error(f"Erro ao carregar equipes: {e}")
            messagebox.showerror("Erro", "Erro ao carregar equipes")

    def load_blocks(self):
        """Carrega lista de bloqueios filtrada pela equipe do usuário logado"""
        for item in self.blocks_tree.get_children():
            self.blocks_tree.delete(item)
            
        try:
            # Query sempre filtra pela equipe do usuário logado
            query = """
                SELECT ul.id, u.nome, e.nome as equipe, ul.lock_status, ul.unlock_control
                FROM user_lock_unlock ul
                JOIN usuarios u ON ul.user_id = u.id
                JOIN equipes e ON u.equipe_id = e.id
                WHERE u.status = TRUE
                AND u.equipe_id = %s
                ORDER BY u.nome
            """
            blocks = self.db.execute_query(query, (self.user_data['equipe_id'],))
            
            if blocks:
                for block in blocks:
                    status = "Bloqueado" if block['lock_status'] else "Desbloqueado"
                    controle = "Liberado" if block['unlock_control'] else "Bloqueado"
                    
                    self.blocks_tree.insert("", "end", values=(
                        block['id'],
                        block['nome'],
                        block['equipe'],
                        status,
                        controle
                    ))
                    
                # Atualizar indicadores apenas da equipe atual
                self.update_status_indicators()
                
        except Exception as e:
            logger.error(f"Erro ao carregar bloqueios: {e}")
            messagebox.showerror("Erro", "Erro ao carregar lista de bloqueios")

    def update_status_indicators(self):
        """Atualiza os indicadores de status apenas para a equipe atual"""
        try:
            # Usuários ativos da equipe atual
            query_active = """
                SELECT COUNT(*) as count 
                FROM usuarios 
                WHERE is_logged_in = TRUE
                AND equipe_id = %s
            """
            active_users = self.db.execute_query(query_active, (self.user_data['equipe_id'],))[0]['count']
            self.status_indicators["Usuários Ativos"].configure(text=str(active_users))
            
            # Usuários bloqueados da equipe atual
            query_blocked = """
                SELECT COUNT(*) as count 
                FROM user_lock_unlock ul
                JOIN usuarios u ON ul.user_id = u.id
                WHERE ul.unlock_control = FALSE
                AND u.equipe_id = %s
            """
            blocked_users = self.db.execute_query(query_blocked, (self.user_data['equipe_id'],))[0]['count']
            self.status_indicators["Usuários Bloqueados"].configure(text=str(blocked_users))
            
            # Tentativas de login da equipe atual
            self.status_indicators["Tentativas de Login"].configure(text="0")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar indicadores: {e}")
            messagebox.showerror("Erro", "Erro ao atualizar indicadores")

    def load_users(self):
        """Carrega todos os usuários na treeview"""
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        query = """
            SELECT u.id, u.nome, u.email, e.nome as equipe, u.tipo_usuario
            FROM usuarios u
            LEFT JOIN equipes e ON u.equipe_id = e.id
            WHERE u.equipe_id = %s
        """
        
        try:
            users = self.db.execute_query(query, (self.user_data['equipe_id'],))
            for user in users:
                self.tree.insert("", "end", values=(
                    user['id'],
                    user['nome'],
                    user['email'],
                    user['equipe'],
                    user['tipo_usuario']
                ))
        except Exception as e:
            logger.error(f"Erro ao carregar usuários: {e}")
            messagebox.showerror("Erro", "Erro ao carregar lista de usuários")
    
    def search_users(self):
        """Pesquisa usuários com base no termo de busca"""
        search_term = self.search_entry.get()
        
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        if not search_term:
            self.load_users()
            return
            
        query = """
            SELECT u.id, u.nome, u.email, e.nome as equipe, u.tipo_usuario
            FROM usuarios u
            LEFT JOIN equipes e ON u.equipe_id = e.id
            WHERE u.equipe_id = %s
            AND u.nome LIKE %s
        """
        
        try:
            users = self.db.execute_query(query, (self.user_data['equipe_id'], f"%{search_term}%"))
            for user in users:
                self.tree.insert("", "end", values=(
                    user['id'],
                    user['nome'],
                    user['email'],
                    user['equipe'],
                    user['tipo_usuario']
                ))
        except Exception as e:
            logger.error(f"Erro ao pesquisar usuários: {e}")
            messagebox.showerror("Erro", "Erro ao pesquisar usuários")
            
    def on_user_select(self, event):
        """Carrega os dados do usuário selecionado no formulário"""
        selected_item = self.tree.selection()
        if not selected_item:
            return
            
        user_id = self.tree.item(selected_item)['values'][0]
        
        query = """
            SELECT u.*, e.nome as equipe_nome
            FROM usuarios u
            LEFT JOIN equipes e ON u.equipe_id = e.id
            WHERE u.id = %s
        """
        
        try:
            result = self.db.execute_query(query, (user_id,))
            if result:
                user = result[0]
                self.current_user_id = user_id
                
                # Preencher formulário
                self.entry_widgets['nome'].delete(0, 'end')
                self.entry_widgets['nome'].insert(0, user['nome'])
                
                self.entry_widgets['email'].delete(0, 'end')
                self.entry_widgets['email'].insert(0, user['email'])
                
                self.entry_widgets['name_id'].delete(0, 'end')
                self.entry_widgets['name_id'].insert(0, user['name_id'])
                
                self.entry_widgets['senha'].delete(0, 'end')
                self.entry_widgets['senha'].insert(0, user['senha'])
                
                if user['equipe_nome']:
                    self.entry_widgets['equipe'].set(user['equipe_nome'])
                
                self.entry_widgets['tipo_usuario'].set(user['tipo_usuario'])
                
                self.entry_widgets['data_entrada'].delete(0, 'end')
                if user['data_entrada']:
                    formatted_date = user['data_entrada'].strftime('%d/%m/%Y')
                    self.entry_widgets['data_entrada'].insert(0, formatted_date)
                
        except Exception as e:
            logger.error(f"Erro ao carregar dados do usuário: {e}")
            messagebox.showerror("Erro", "Erro ao carregar dados do usuário")
    
    def save_user(self):
        """Salva ou atualiza um usuário"""
        try:
            data = {field: widget.get() for field, widget in self.entry_widgets.items()}
            
            # Validações
            required_fields = ['nome', 'email', 'name_id', 'senha']
            if not all(data[field] for field in required_fields):
                messagebox.showerror("Erro", "Todos os campos são obrigatórios!")
                return
            
            # Tratamento da data
            try:
                # Converter data do formato dd/mm/aaaa para aaaa-mm-dd
                date_parts = data['data_entrada'].split('/')
                if len(date_parts) == 3:
                    data['data_entrada'] = f"{date_parts[2]}-{date_parts[1]}-{date_parts[0]}"
                else:
                    raise ValueError("Formato de data inválido")
            except ValueError as e:
                messagebox.showerror("Erro", "Data inválida! Use o formato dd/mm/aaaa")
                return
            
            # Buscar ID da equipe
            equipe_query = "SELECT id FROM equipes WHERE nome = %s"
            equipe_result = self.db.execute_query(equipe_query, (data['equipe'],))
            if not equipe_result:
                messagebox.showerror("Erro", "Equipe não encontrada!")
                return
            
            equipe_id = equipe_result[0]['id']
            
            # Hash da senha com bcrypt
            senha_hash = bcrypt.hashpw(data['senha'].encode('utf-8'), bcrypt.gensalt())
            
            if self.current_user_id:  # Atualização
                # Verificar se a senha foi alterada
                senha_query = "SELECT senha FROM usuarios WHERE id = %s"
                senha_result = self.db.execute_query(senha_query, (self.current_user_id,))
                senha_atual = senha_result[0]['senha']
                
                # Se a senha não mudou, manter a senha atual
                if data['senha'] == senha_atual:
                    senha_final = senha_atual
                else:
                    senha_final = senha_hash
                
                query = """
                    UPDATE usuarios SET
                        nome = %s,
                        email = %s,
                        name_id = %s,
                        senha = %s,
                        equipe_id = %s,
                        tipo_usuario = %s,
                        data_entrada = %s
                    WHERE id = %s
                """
                params = (
                    data['nome'],
                    data['email'],
                    data['name_id'],
                    senha_final,
                    equipe_id,
                    data['tipo_usuario'],
                    data['data_entrada'],
                    self.current_user_id
                )
                message = "Usuário atualizado com sucesso!"
            else:  # Novo usuário
                query = """
                    INSERT INTO usuarios (
                        nome, email, name_id, senha, equipe_id,
                        tipo_usuario, data_entrada, status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
                """
                params = (
                    data['nome'],
                    data['email'],
                    data['name_id'],
                    senha_hash,
                    equipe_id,
                    data['tipo_usuario'],
                    data['data_entrada']
                )
                message = "Usuário cadastrado com sucesso!"
                
                # Execute a inserção do usuário e obtenha o ID gerado
                cursor = self.db.connection.cursor(dictionary=True)
                cursor.execute(query, params)
                new_user_id = cursor.lastrowid
                
                # O trigger after_usuario_insert irá criar automaticamente o registro na tabela user_lock_unlock
                self.db.connection.commit()
                cursor.close()
            
            messagebox.showinfo("Sucesso", message)
            
            # Atualizar todas as listas e indicadores
            self.clear_form()
            self.load_users()
            self.load_blocks()  # Atualizar lista de bloqueios
            self.update_status_indicators()  # Atualizar indicadores
            
        except Exception as e:
            logger.error(f"Erro ao salvar usuário: {e}")
            messagebox.showerror("Erro", f"Erro ao salvar usuário: {e}")
    
    def delete_user(self):
        """Remove um usuário do sistema"""
        if not self.current_user_id:
            messagebox.showwarning("Aviso", "Selecione um usuário para deletar!")
            return
        
        if messagebox.askyesno("Confirmar", "Deseja realmente deletar este usuário?"):
            try:
                # Deletar usuário em vez de marcar como inativo
                query = "DELETE FROM usuarios WHERE id = %s"
                self.db.execute_query(query, (self.current_user_id,))
                
                messagebox.showinfo("Sucesso", "Usuário deletado com sucesso!")
                
                # Limpar formulário e atualizar todas as listas
                self.clear_form()
                self.load_users()
                self.load_blocks()
                self.update_status_indicators()
                
            except Exception as e:
                logger.error(f"Erro ao deletar usuário: {e}")
                messagebox.showerror("Erro", f"Erro ao deletar usuário: {e}")
    
    def clear_form(self):
        """Limpa o formulário e prepara para novo cadastro"""
        self.current_user_id = None
        
        # Limpar campos de texto
        for field in ['nome', 'email', 'name_id', 'senha']:
            self.entry_widgets[field].delete(0, 'end')
        
        # Resetar comboboxes
        self.entry_widgets['equipe'].set(self.get_equipes()[0] if self.get_equipes() else '')
        self.entry_widgets['tipo_usuario'].set('comum')
        
        # Resetar data para atual
        self.entry_widgets['data_entrada'].delete(0, 'end')
        self.entry_widgets['data_entrada'].insert(0, datetime.now().strftime('%d/%m/%Y'))
        
    def get_equipes(self):
        """Retorna lista de todas as equipes do banco"""
        try:
            # Query simplificada para trazer todas as equipes
            query = """
                SELECT nome 
                FROM equipes 
                ORDER BY nome
            """
            result = self.db.execute_query(query)
            
            # Debug para verificar o resultado
            logger.debug(f"Equipes encontradas: {result}")
            
            return [row['nome'] for row in result] if result else []
        except Exception as e:
            logger.error(f"Erro ao buscar equipes: {e}")
            return []

    def update_equipes_combobox(self):
        """Atualiza o ComboBox de equipes com dados do banco"""
        try:
            equipes = self.get_equipes()
            if 'equipe' in self.entry_widgets:
                self.entry_widgets['equipe'].configure(values=equipes)
                # Se o ComboBox estiver vazio, seleciona a primeira equipe
                if not self.entry_widgets['equipe'].get() and equipes:
                    self.entry_widgets['equipe'].set(equipes[0])
        except Exception as e:
            logger.error(f"Erro ao atualizar ComboBox de equipes: {e}")

    def setup_users_list(self, parent):
        """Configura a lista de usuários"""
        # Frame para a lista
        list_frame = ctk.CTkFrame(parent)
        list_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 2))
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)
        
        # Criar Treeview com estilo moderno
        self.tree = ttk.Treeview(
            list_frame,
            columns=("ID", "Nome", "Email", "Equipe", "Tipo"),
            show="headings",
            style="Custom.Treeview"
        )
        
        # Configurar colunas com proporções adequadas
        columns = {
            "ID": 60,
            "Nome": 200,
            "Email": 200,
            "Equipe": 150,
            "Tipo": 100
        }
        
        for col, width in columns.items():
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(self.tree, c))
            self.tree.column(col, width=width, minwidth=width)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Grid
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Binding para seleção
        self.tree.bind("<<TreeviewSelect>>", self.on_user_select)

    def sort_treeview(self, tree, col):
        """Ordena o treeview quando clica no cabeçalho"""
        # Obtém todos os itens da árvore
        items = [(tree.set(item, col), item) for item in tree.get_children("")]
        
        # Reverte a ordem se clicar na mesma coluna
        reverse = False
        if self.sort_order["column"] == col:
            reverse = not self.sort_order["reverse"]
        
        # Atualiza a ordem de classificação
        self.sort_order["column"] = col
        self.sort_order["reverse"] = reverse
        
        # Ordena os itens
        items.sort(reverse=reverse)
        
        # Move os itens na ordem classificada
        for index, (val, item) in enumerate(items):
            tree.move(item, "", index)
        
        # Adiciona seta indicadora no cabeçalho
        for header in tree["columns"]:
            if header == col:
                tree.heading(header, text=f"{header} {'↓' if reverse else '↑'}")
            else:
                tree.heading(header, text=header)

    def setup_user_form(self, parent):
        """Configura o formulário de usuário com novo layout"""
        # Frame para o formulário com padding reduzido
        form_frame = ctk.CTkFrame(parent)
        form_frame.grid(row=0, column=0, sticky="nsew", pady=2)
        
        # Título do formulário
        title = ctk.CTkLabel(
            form_frame,
            text="Dados do Usuário",
            font=("Roboto", 14, "bold"),
            text_color=("#ff5722", "#ff5722")
        )
        title.pack(pady=(10, 15))
        
        # Frame para os campos
        fields_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        fields_frame.pack(fill="both", expand=True, padx=5)
        
        # Definição dos campos
        fields = [
            ("nome", "Nome"),
            ("email", "Email"),
            ("name_id", "Name ID"),
            ("senha", "Senha"),
            ("equipe", "Equipe"),
            ("tipo_usuario", "Tipo"),
            ("data_entrada", "Data Entrada")
        ]
        
        # Criação dos campos do formulário
        for field, label in fields:
            field_frame = ctk.CTkFrame(fields_frame, fg_color="transparent")
            field_frame.pack(fill="x", pady=1)
            
            if field in ["equipe", "tipo_usuario"]:
                if field == "equipe":
                    widget = ctk.CTkComboBox(
                        field_frame,
                        values=self.get_equipes(),
                        height=28
                    )
                else:
                    widget = ctk.CTkComboBox(
                        field_frame,
                        values=["admin", "comum"],
                        height=28
                    )
            else:
                widget = ctk.CTkEntry(
                    field_frame,
                    placeholder_text=label,
                    height=28
                )
                if field == "senha":
                    widget.configure(show="*")
            
            widget.pack(fill="x")
            self.entry_widgets[field] = widget
        
        # Frame para botões lado a lado
        btn_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=5, pady=10)
        
        # Configurar grid para 2 colunas
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        
        # Botões na primeira linha
        save_btn = ctk.CTkButton(
            btn_frame,
            text="Salvar",
            height=28,
            command=self.save_user,
            fg_color="#ff5722",
            hover_color="#ce461b"
        )
        save_btn.grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        
        clear_btn = ctk.CTkButton(
            btn_frame,
            text="Limpar",
            height=28,
            command=self.clear_form,
            fg_color="transparent",
            border_width=1,
            border_color="#ff5722",
            text_color="#ff5722",
            hover_color="#fff1eb"
        )
        clear_btn.grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        
        # Botão excluir na segunda linha
        delete_btn = ctk.CTkButton(
            btn_frame,
            text="Excluir",
            height=28,
            command=self.delete_user,
            fg_color="#dc2626",
            hover_color="#991b1b"
        )
        delete_btn.grid(row=1, column=0, columnspan=2, padx=2, pady=(2,0), sticky="ew")
        
    def show_team_context_menu(self, event):
        """Exibe menu de contexto para equipes"""
        try:
            # Identificar item clicado
            item = self.teams_tree.identify_row(event.y)
            if not item:
                return
            
            # Selecionar o item
            self.teams_tree.selection_set(item)
            
            # Criar menu
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="Excluir Equipe", 
                            command=lambda: self.delete_team(self.teams_tree.item(item)['values'][0]))
            
            # Exibir menu
            menu.post(event.x_root, event.y_root)
            
        except Exception as e:
            logger.error(f"Erro ao exibir menu de contexto: {e}")

    def delete_team(self, team_id):
        """Exclui uma equipe"""
        try:
            # Verificar se há usuários ativos na equipe
            check_query = """
                SELECT COUNT(*) as count 
                FROM usuarios 
                WHERE equipe_id = %s AND status = TRUE
            """
            result = self.db.execute_query(check_query, (team_id,))
            
            if result[0]['count'] > 0:
                messagebox.showerror(
                    "Erro",
                    "Não é possível excluir esta equipe pois existem usuários ativos vinculados a ela."
                )
                return
            
            # Confirmar exclusão
            if messagebox.askyesno("Confirmar", "Deseja realmente excluir esta equipe?"):
                delete_query = "DELETE FROM equipes WHERE id = %s"
                self.db.execute_query(delete_query, (team_id,))
                
                messagebox.showinfo("Sucesso", "Equipe excluída com sucesso!")
                self.load_teams()
                
        except Exception as e:
            logger.error(f"Erro ao excluir equipe: {e}")
            messagebox.showerror("Erro", "Erro ao excluir equipe")

    def delete_selected_team(self):
        """Exclui a equipe selecionada"""
        selected_items = self.teams_tree.selection()
        if not selected_items:
            messagebox.showwarning("Aviso", "Selecione uma equipe para excluir!")
            return
        
        team_id = self.teams_tree.item(selected_items[0])['values'][0]
        self.delete_team(team_id)

    def toggle_user_lock(self):
        """Altera o status de bloqueio do usuário selecionado"""
        selected_items = self.blocks_tree.selection()
        if not selected_items:
            messagebox.showwarning("Aviso", "Selecione um usuário para alterar o status!")
            return
        
        try:
            block_id = self.blocks_tree.item(selected_items[0])['values'][0]
            
            # Buscar status atual
            status_query = "SELECT unlock_control FROM user_lock_unlock WHERE id = %s"
            result = self.db.execute_query(status_query, (block_id,))
            
            if result:
                current_status = result[0]['unlock_control']
                new_status = not current_status
                
                # Atualizar status
                update_query = """
                    UPDATE user_lock_unlock 
                    SET unlock_control = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """
                self.db.execute_query(update_query, (new_status, block_id))
                
                status_text = "desbloqueado" if new_status else "bloqueado"
                messagebox.showinfo("Sucesso", f"Usuário {status_text} com sucesso!")
                
                # Recarregar lista
                self.load_blocks()
                
        except Exception as e:
            logger.error(f"Erro ao alterar status de bloqueio: {e}")
            messagebox.showerror("Erro", "Erro ao alterar status de bloqueio")

    def search_blocks(self):
        """Pesquisa usuários bloqueados com base no texto inserido"""
        search_text = self.blocks_search_entry.get().strip()
        
        # Limpar a árvore
        for item in self.blocks_tree.get_children():
            self.blocks_tree.delete(item)
        
        if not search_text:
            self.load_blocks()
            return
            
        try:
            # Query de busca sempre filtra pela equipe do usuário logado
            query = """
                SELECT ul.id, u.nome, e.nome as equipe, ul.lock_status, ul.unlock_control
                FROM user_lock_unlock ul
                JOIN usuarios u ON ul.user_id = u.id
                JOIN equipes e ON u.equipe_id = e.id
                WHERE u.status = TRUE
                AND u.equipe_id = %s
                AND u.nome LIKE %s
                ORDER BY u.nome
            """
            blocks = self.db.execute_query(query, (self.user_data['equipe_id'], f"%{search_text}%"))
            
            if blocks:
                for block in blocks:
                    status = "Bloqueado" if block['lock_status'] else "Desbloqueado"
                    controle = "Liberado" if block['unlock_control'] else "Bloqueado"
                    
                    self.blocks_tree.insert("", "end", values=(
                        block['id'],
                        block['nome'],
                        block['equipe'],
                        status,
                        controle
                    ))
                    
        except Exception as e:
            logger.error(f"Erro ao buscar bloqueios: {str(e)}")
            messagebox.showerror(
                "Erro",
                "Ocorreu um erro ao buscar os bloqueios. Por favor, tente novamente."
            )

    def search_teams(self):
        """Pesquisa equipes com base no nome"""
        search_text = self.teams_search_entry.get().strip()
        
        # Limpar a árvore
        for item in self.teams_tree.get_children():
            self.teams_tree.delete(item)
        
        if not search_text:
            self.load_teams()
            return
        
        try:
            query = """
                SELECT e.id, e.nome, COUNT(u.id) as membros, e.created_at
                FROM equipes e
                LEFT JOIN usuarios u ON e.id = u.equipe_id AND u.status = TRUE
                WHERE LOWER(e.nome) LIKE LOWER(%s)
                GROUP BY e.id, e.nome, e.created_at
                ORDER BY e.nome
            """
            
            search_pattern = f"%{search_text}%"
            teams = self.db.execute_query(query, (search_pattern,))
            
            if teams:
                for team in teams:
                    self.teams_tree.insert(
                        "",
                        "end",
                        values=(
                            team['id'],
                            team['nome'],
                            team['membros'],
                            team['created_at'].strftime('%d/%m/%Y %H:%M')
                        )
                    )
                    
        except Exception as e:
            logger.error(f"Erro ao buscar equipes: {str(e)}")
            messagebox.showerror(
                "Erro",
                "Ocorreu um erro ao buscar as equipes. Por favor, tente novamente."
            )

    def show_block_context_menu(self, event):
        """Exibe menu de contexto para bloqueios"""
        try:
            # Identificar item clicado
            item = self.blocks_tree.identify_row(event.y)
            if not item:
                return
            
            # Selecionar o item
            self.blocks_tree.selection_set(item)
            
            # Criar menu
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="Alterar Status", 
                            command=lambda: self.toggle_user_lock())
            
            # Exibir menu
            menu.post(event.x_root, event.y_root)
            
        except Exception as e:
            logger.error(f"Erro ao exibir menu de contexto: {e}")
