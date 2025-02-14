import customtkinter as ctk
from tkinter import ttk, messagebox
import logging
from ...database.connection import DatabaseConnection
from datetime import datetime
from ...utils.helpers import BaseDialog

logger = logging.getLogger(__name__)

class RegisterDialog(BaseDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Cadastro de Usuários")
        self.geometry("500x600")
        self.resizable(False, False)
        
        # Centralizar a janela
        window_width = 500
        window_height = 600
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = int((screen_width/2) - (window_width/2))
        y = int((screen_height/2) - (window_height/2))
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        self.db = DatabaseConnection()
        self.transient(parent)
        self.grab_set()
        
        self.setup_ui()
        
    def setup_ui(self):
        """Configura a interface do diálogo"""
        # Frame principal centralizado
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Título
        title_label = ctk.CTkLabel(
            main_frame,
            text="Cadastro de Usuário",
            font=("Roboto", 20, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Frame para campos
        fields_frame = ctk.CTkFrame(main_frame)
        fields_frame.pack(expand=True, fill="both", padx=20)
        
        # Configuração dos campos na ordem especificada
        fields = [
            ('nome', 'Nome:', 'entry'),
            ('email', 'E-mail:', 'entry'),
            ('name_id', 'ID:', 'entry'),
            ('senha', 'Senha:', 'entry'),
            ('equipe', 'Equipe:', 'combo'),
            ('tipo_usuario', 'Tipo de Usuário:', 'combo'),
            ('data_entrada', 'Data de Entrada:', 'date')
        ]
        
        self.register_entries = {}
        
        for i, (field, label, field_type) in enumerate(fields):
            label_widget = ctk.CTkLabel(fields_frame, text=label)
            label_widget.grid(row=i, column=0, padx=10, pady=5, sticky="e")
            
            if field_type == 'entry':
                widget = ctk.CTkEntry(fields_frame, width=250)
                if field == 'senha':
                    widget.configure(show="*")
            elif field_type == 'combo':
                if field == 'equipe':
                    values = self.get_equipes()
                elif field == 'tipo_usuario':
                    values = ['comum', 'admin']
                widget = ctk.CTkOptionMenu(fields_frame, values=values, width=250)
            elif field_type == 'date':
                widget = ctk.CTkEntry(fields_frame, width=250)
                widget.insert(0, datetime.now().strftime('%d/%m/%Y'))
            
            widget.grid(row=i, column=1, padx=10, pady=5, sticky="w")
            self.register_entries[field] = widget
        
        # Botões
        btn_frame = ctk.CTkFrame(main_frame)
        btn_frame.pack(pady=20)
        
        self.register_btn = ctk.CTkButton(
            btn_frame,
            text="Cadastrar",
            command=self.register_user,
            width=200
        )
        self.register_btn.pack()
    
    def get_equipes(self):
        """Retorna lista de equipes do banco"""
        try:
            query = "SELECT nome FROM equipes"
            result = self.db.execute_query(query)
            return [row['nome'] for row in result] if result else []
        except Exception as e:
            logger.error(f"Erro ao buscar equipes: {e}")
            return []
    
    def register_user(self):
        """Cadastra novo usuário"""
        try:
            data = {field: widget.get() for field, widget in self.register_entries.items()}
            
            # Validações
            required_fields = ['nome', 'email', 'name_id', 'senha']
            if not all(data[field] for field in required_fields):
                messagebox.showerror("Erro", "Todos os campos são obrigatórios!")
                return
            
            # Buscar ID da equipe
            equipe_query = "SELECT id FROM equipes WHERE nome = %s"
            equipe_result = self.db.execute_query(equipe_query, (data['equipe'],))
            if not equipe_result:
                messagebox.showerror("Erro", "Equipe não encontrada!")
                return
            
            equipe_id = equipe_result[0]['id']
            
            # Inserir usuário
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
                data['senha'],
                equipe_id,
                data['tipo_usuario'],
                data['data_entrada']
            )
            
            self.db.execute_query(query, params)
            messagebox.showinfo("Sucesso", "Usuário cadastrado com sucesso!")
            
            # Limpar campos
            for field in ['nome', 'email', 'name_id', 'senha']:
                self.register_entries[field].delete(0, 'end')
            
        except Exception as e:
            logger.error(f"Erro ao cadastrar usuário: {e}")
            messagebox.showerror("Erro", f"Erro ao cadastrar usuário: {e}")