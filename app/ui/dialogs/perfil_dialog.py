import customtkinter as ctk
from ...database.connection import DatabaseConnection
from .change_password_dialog import ChangePasswordDialog

class PerfilFrame(ctk.CTkFrame):
    def __init__(self, parent, user_data):
        super().__init__(parent)
        
        self.db = DatabaseConnection()
        self.user_data = user_data
        
        # Configurações de estilo
        self.configure(fg_color="transparent")  # Fundo transparente para o frame principal
        
        self.setup_ui()
    
    def setup_ui(self):
        # Container principal com margens
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=40, pady=30)
        
        # Cabeçalho com informações principais
        header_frame = ctk.CTkFrame(main_container, fg_color="#2b2b2b", corner_radius=15)
        header_frame.pack(fill="x", pady=(0, 20))
        
        # Título e subtítulo
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(fill="x", padx=30, pady=20)
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="Perfil do Usuário",
            font=("Roboto", 28, "bold"),
            text_color="#ff5722"
        )
        title_label.pack(anchor="w")
        
        subtitle_label = ctk.CTkLabel(
            title_frame,
            text="Gerencie suas informações pessoais",
            font=("Roboto", 14),
            text_color="#888888"
        )
        subtitle_label.pack(anchor="w")
        
        try:
            # Buscar nome da equipe
            team_query = "SELECT nome FROM equipes WHERE id = %s"
            team_result = self.db.execute_query(team_query, (self.user_data['equipe_id'],))
            team_name = team_result[0]['nome'] if team_result else "Sem Equipe"
            
            # Container para as informações em cards
            info_container = ctk.CTkFrame(main_container, fg_color="transparent")
            info_container.pack(fill="both", expand=True)
            
            # Grid para os cards de informação
            info_container.grid_columnconfigure(0, weight=1)
            info_container.grid_columnconfigure(1, weight=1)
            
            # Card de Informações Pessoais
            personal_card = self._create_card(info_container, "Informações Pessoais")
            personal_card.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
            
            self._add_info_field(personal_card, "Nome", self.user_data['nome'])
            self._add_info_field(personal_card, "Email", self.user_data['email'])
            self._add_info_field(personal_card, "ID", self.user_data['name_id'])
            
            # Card de Informações Profissionais
            work_card = self._create_card(info_container, "Informações Profissionais")
            work_card.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
            
            self._add_info_field(work_card, "Equipe", team_name)
            self._add_info_field(work_card, "Data de Cadastro", 
                               self.user_data['data_entrada'].strftime('%d/%m/%Y') 
                               if self.user_data['data_entrada'] else 'Não definida')
            
            # Frame para botões
            button_container = ctk.CTkFrame(main_container, fg_color="transparent")
            button_container.pack(fill="x", pady=(20, 0))
            
            # Botão para alterar senha com ícone
            btn_change_password = ctk.CTkButton(
                button_container,
                text="Alterar Senha",
                font=("Roboto", 14),
                fg_color="#FF5722",
                hover_color="#CE461B",
                height=40,
                command=self.show_change_password_dialog
            )
            btn_change_password.pack(side="left", padx=5)
            
        except Exception as e:
            error_frame = ctk.CTkFrame(main_container, fg_color="#2b2b2b", corner_radius=15)
            error_frame.pack(fill="x", pady=20)
            
            error_label = ctk.CTkLabel(
                error_frame,
                text=f"Erro ao carregar perfil: {e}",
                font=("Roboto", 14),
                text_color="#ff4444"
            )
            error_label.pack(pady=20)
    
    def _create_card(self, parent, title):
        """Cria um card com título para agrupar informações"""
        card = ctk.CTkFrame(parent, fg_color="#2b2b2b", corner_radius=15)
        
        # Título do card
        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=("Roboto", 18, "bold"),
            text_color="#ff5722"
        )
        title_label.pack(anchor="w", padx=20, pady=(15, 5))
        
        # Linha separadora
        separator = ctk.CTkFrame(card, height=2, fg_color="#3b3b3b")
        separator.pack(fill="x", padx=15, pady=(0, 10))
        
        return card
    
    def _add_info_field(self, parent, label, value):
        """Adiciona um campo de informação ao card"""
        field_frame = ctk.CTkFrame(parent, fg_color="transparent")
        field_frame.pack(fill="x", padx=20, pady=5)
        
        label_widget = ctk.CTkLabel(
            field_frame,
            text=f"{label}:",
            font=("Roboto", 14, "bold"),
            text_color="#888888"
        )
        label_widget.pack(side="left")
        
        value_widget = ctk.CTkLabel(
            field_frame,
            text=str(value),
            font=("Roboto", 14),
            text_color="white"
        )
        value_widget.pack(side="left", padx=(10, 0))
    
    def show_change_password_dialog(self):
        """Exibe o diálogo de alteração de senha"""
        ChangePasswordDialog(self, self.user_data)