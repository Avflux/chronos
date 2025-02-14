import customtkinter as ctk
from tkinter import messagebox
import bcrypt
from ...database.connection import DatabaseConnection

class ChangePasswordDialog(ctk.CTkToplevel):
    _instance = None  # Variável de classe para controlar a instância única
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None or not cls._instance.winfo_exists():
            cls._instance = super().__new__(cls)
            return cls._instance
        else:
            cls._instance.lift()  # Traz a janela existente para frente
            return None
    
    def __init__(self, parent, user_data):
        if not hasattr(self, '_initialized'):  # Evita reinicialização
            super().__init__(parent)
            self._initialized = True
            
            self.db = DatabaseConnection()
            self.user_data = user_data
            
            # Configuração da janela
            self.title("Alterar Senha")
            window_width = 400
            window_height = 300
            
            # Obter dimensões da tela
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            
            # Calcular posição para centralizar
            x = int((screen_width - window_width) / 2)
            y = int((screen_height - window_height) / 2)
            
            self.geometry(f"{window_width}x{window_height}+{x}+{y}")
            self.resizable(False, False)
            
            # Configurar como modal
            self.transient(parent)
            self.grab_set()
            
            # Garantir que a janela fique em primeiro plano
            self.lift()
            self.focus_force()
            
            self.setup_ui()
            
            # Protocolo para fechar a janela
            self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_ui(self):
        # Frame principal com padding
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        title = ctk.CTkLabel(
            main_frame,
            text="Alterar Senha",
            font=("Roboto", 20, "bold")
        )
        title.pack(pady=(0, 20))
        
        # Campos de senha
        self.current_password = ctk.CTkEntry(
            main_frame,
            placeholder_text="Senha atual",
            show="*",
            width=250
        )
        self.current_password.pack(pady=10)
        
        self.new_password = ctk.CTkEntry(
            main_frame,
            placeholder_text="Nova senha",
            show="*",
            width=250
        )
        self.new_password.pack(pady=10)
        
        self.confirm_password = ctk.CTkEntry(
            main_frame,
            placeholder_text="Confirmar nova senha",
            show="*",
            width=250
        )
        self.confirm_password.pack(pady=10)
        
        # Frame para botões
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(pady=20)
        
        # Botões
        ctk.CTkButton(
            button_frame,
            text="Cancelar",
            command=self.on_closing,
            fg_color="transparent",
            border_width=2,
            text_color=("gray10", "gray90"),
            width=100
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="Salvar",
            command=self.change_password,
            fg_color="#FF5722",
            hover_color="#CE461B",
            width=100
        ).pack(side="left", padx=5)
    
    def verify_password(self, current_password, stored_password):
        """Verifica a senha considerando tanto o formato antigo quanto o novo"""
        try:
            # Tenta verificar como bcrypt
            return bcrypt.checkpw(current_password.encode('utf-8'), stored_password.encode('utf-8'))
        except Exception:
            # Se falhar, verifica no formato antigo (comparação direta)
            return current_password == stored_password
    
    def change_password(self):
        current = self.current_password.get()
        new = self.new_password.get()
        confirm = self.confirm_password.get()
        
        if not all([current, new, confirm]):
            messagebox.showerror("Erro", "Todos os campos são obrigatórios")
            return
        
        if new != confirm:
            messagebox.showerror("Erro", "As senhas não coincidem")
            return
        
        if len(new) < 6:
            messagebox.showerror("Erro", "A nova senha deve ter pelo menos 6 caracteres")
            return
        
        try:
            # Verificar senha atual
            query = "SELECT senha FROM usuarios WHERE id = %s"
            result = self.db.execute_query(query, (self.user_data['id'],))
            
            if not result:
                messagebox.showerror("Erro", "Usuário não encontrado")
                return
            
            stored_password = result[0]['senha']
            
            # Verifica a senha usando o método que suporta ambos os formatos
            if not self.verify_password(current, stored_password):
                messagebox.showerror("Erro", "Senha atual incorreta")
                return
            
            # Gerar hash da nova senha usando bcrypt
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(new.encode('utf-8'), salt)
            
            # Atualizar senha no banco
            update_query = "UPDATE usuarios SET senha = %s WHERE id = %s"
            self.db.execute_query(update_query, (hashed_password.decode('utf-8'), self.user_data['id']))
            
            messagebox.showinfo("Sucesso", "Senha alterada com sucesso!")
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao alterar senha: {str(e)}")
    
    def on_closing(self):
        """Método chamado quando a janela é fechada"""
        self.destroy()
        ChangePasswordDialog._instance = None  # Limpa a instância ao fechar