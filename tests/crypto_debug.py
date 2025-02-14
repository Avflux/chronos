import customtkinter as ctk
from tkinter import messagebox
import json
from cryptography.fernet import Fernet
import os

class CryptoDebugTool(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Crypto Debug Tool")
        self.geometry("800x600")
        
        # Configuração da grid principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self.setup_ui()
        
    def setup_ui(self):
        # Frame superior
        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        # Botões de ação
        self.btn_load = ctk.CTkButton(
            self.top_frame,
            text="Carregar Dados",
            command=self.load_encrypted_data
        )
        self.btn_load.pack(side="left", padx=5, pady=5)
        
        self.btn_save = ctk.CTkButton(
            self.top_frame,
            text="Salvar Alterações",
            command=self.save_encrypted_data
        )
        self.btn_save.pack(side="left", padx=5, pady=5)
        
        # Frame principal com texto
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        
        # Frame esquerdo (dados criptografados)
        self.left_frame = ctk.CTkFrame(self.main_frame)
        self.left_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        self.lbl_encrypted = ctk.CTkLabel(self.left_frame, text="Dados Criptografados:")
        self.lbl_encrypted.pack(pady=5)
        
        self.txt_encrypted = ctk.CTkTextbox(self.left_frame)
        self.txt_encrypted.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Frame direito (dados descriptografados)
        self.right_frame = ctk.CTkFrame(self.main_frame)
        self.right_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
        self.lbl_decrypted = ctk.CTkLabel(self.right_frame, text="Dados Descriptografados:")
        self.lbl_decrypted.pack(pady=5)
        
        self.txt_decrypted = ctk.CTkTextbox(self.right_frame)
        self.txt_decrypted.pack(fill="both", expand=True, padx=5, pady=5)
        
    def load_encrypted_data(self):
        try:
            # Verificar se os arquivos existem
            if not os.path.exists("crypto.key"):
                messagebox.showerror("Erro", "Arquivo crypto.key não encontrado!")
                return
                
            if not os.path.exists(".env.encrypted"):
                messagebox.showerror("Erro", "Arquivo .env.encrypted não encontrado!")
                return
            
            # Carregar a chave
            with open("crypto.key", "rb") as key_file:
                key = key_file.read()
                f = Fernet(key)
            
            # Carregar dados criptografados
            with open(".env.encrypted", "rb") as env_file:
                encrypted_data = env_file.read()
            
            # Mostrar dados criptografados
            self.txt_encrypted.delete("0.0", "end")
            self.txt_encrypted.insert("0.0", encrypted_data.hex())
            
            # Descriptografar e mostrar
            decrypted_data = f.decrypt(encrypted_data).decode()
            self.txt_decrypted.delete("0.0", "end")
            self.txt_decrypted.insert("0.0", decrypted_data)
            
            messagebox.showinfo("Sucesso", "Dados carregados com sucesso!")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar dados: {str(e)}")
    
    def save_encrypted_data(self):
        try:
            # Verificar se crypto.key existe
            if not os.path.exists("crypto.key"):
                messagebox.showerror("Erro", "Arquivo crypto.key não encontrado!")
                return
            
            # Carregar a chave
            with open("crypto.key", "rb") as key_file:
                key = key_file.read()
                f = Fernet(key)
            
            # Pegar os dados do textbox
            decrypted_data = self.txt_decrypted.get("0.0", "end").strip()
            
            # Validar o formato dos dados
            try:
                # Verificar se cada linha tem o formato correto (chave=valor)
                for line in decrypted_data.split('\n'):
                    if line.strip() and '=' not in line:
                        raise ValueError(f"Linha inválida: {line}")
            except Exception as e:
                messagebox.showerror("Erro", f"Formato inválido: {str(e)}")
                return
            
            # Criptografar os novos dados
            encrypted_data = f.encrypt(decrypted_data.encode())
            
            # Salvar os dados criptografados
            with open(".env.encrypted", "wb") as env_file:
                env_file.write(encrypted_data)
            
            # Atualizar a visualização dos dados criptografados
            self.txt_encrypted.delete("0.0", "end")
            self.txt_encrypted.insert("0.0", encrypted_data.hex())
            
            messagebox.showinfo("Sucesso", "Dados salvos com sucesso!")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar dados: {str(e)}")

if __name__ == "__main__":
    app = CryptoDebugTool()
    app.mainloop()