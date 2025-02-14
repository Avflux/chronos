import customtkinter as ctk
from tkinter import messagebox
import os
import logging
import sys

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LoginWindow(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        window_width = 300
        window_height = 400
        screen_width = master.winfo_screenwidth()
        screen_height = master.winfo_screenheight()
        x = int((screen_width - window_width) / 2)
        y = int((screen_height - window_height) / 2)
        master.geometry(f"{window_width}x{window_height}+{x}+{y}")
        master.title("Login - Teste")
        
        # Tentar configurar ícone
        try:
            icon_path = os.path.join('app', 'resources', 'icons', 'app.ico')
            if os.path.exists(icon_path):
                master.iconbitmap(icon_path)
                logger.debug(f"Ícone configurado na LoginWindow: {icon_path}")
            else:
                logger.warning(f"Ícone não encontrado: {icon_path}")
        except Exception as e:
            logger.error(f"Erro ao configurar ícone na LoginWindow: {e}")

        self.pack(fill="both", expand=True)
        self.setup_ui()

    def setup_ui(self):
        btn = ctk.CTkButton(
            self, 
            text="Abrir UserWindow",
            command=self.open_user_window
        )
        btn.pack(expand=True)

    def open_user_window(self):
        self.master.withdraw()
        user_window = UserWindow()  # Criação da UserWindow
        user_window.deiconify()  # Garante que a janela seja exibida
        user_window.protocol("WM_DELETE_WINDOW", lambda: self.on_user_window_close(user_window))



    def on_user_window_close(self, user_window):
        user_window.destroy()
        self.master.deiconify()

class UserWindow(ctk.CTk):  # Substituímos CTkToplevel por CTk
    def __init__(self):
        super().__init__()

        # Configurações da janela
        window_width = 800
        window_height = 600
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = int((screen_width - window_width) / 2)
        y = int((screen_height - window_height) / 2)
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.title("UserWindow - Teste")

        logger.debug("Janela UserWindow criada como CTk")

        # Configurar ícone
        icon_path = os.path.join("app", "resources", "icons", "app.ico")
        try:
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
                logger.debug(f"Ícone configurado na UserWindow: {icon_path}")
            else:
                logger.warning(f"Ícone não encontrado: {icon_path}")
        except Exception as e:
            logger.error(f"Erro ao configurar ícone na UserWindow: {e}")

        self.setup_ui()

    def setup_ui(self):
        label = ctk.CTkLabel(
            self, 
            text="Janela de Teste - UserWindow",
            font=("Roboto", 24, "bold")
        )
        label.pack(expand=True)

        btn = ctk.CTkButton(
            self,
            text="Fechar",
            command=self.destroy
        )
        btn.pack(pady=20)

        logger.debug("Interface da UserWindow configurada")



class App:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Aplicação de Teste")
        self.login_window = LoginWindow(self.root)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    try:
        app = App()
        app.run()
    except Exception as e:
        logger.error(f"Erro na aplicação: {e}")
        messagebox.showerror("Erro", f"Erro na aplicação: {e}")
        sys.exit(1)