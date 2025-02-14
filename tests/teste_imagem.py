import os
import sys

# Adicionar diretório raiz ao PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.insert(0, project_root)

import logging
import customtkinter as ctk
from PIL import Image
from app.config.settings import APP_CONFIG

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TesteImagem(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Teste de Carregamento de Imagem")
        self.geometry("600x400")
        
        # Dicionário para manter referências das imagens
        self.images = {}
        
        # Frame principal
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Tentar carregar a imagem
        self.carregar_imagem()
        
        # Adicionar botão para trocar tema
        theme_button = ctk.CTkButton(
            self.main_frame,
            text="Trocar Tema",
            command=self.toggle_theme
        )
        theme_button.pack(pady=10)
        
    def carregar_imagem(self):
        """Testa diferentes métodos de carregamento de imagem"""
        try:
            # 1. Obter caminhos possíveis
            if hasattr(sys, '_MEIPASS'):
                base_path = sys._MEIPASS
            else:
                base_path = project_root  # Usar a variável global que definimos
            
            # Criar label para mostrar informações
            info_label = ctk.CTkLabel(
                self.main_frame,
                text="Informações de Carregamento:",
                font=("Arial", 14, "bold")
            )
            info_label.pack(pady=10)
            
            # Mostrar caminhos
            logger.debug(f"Diretório atual: {os.getcwd()}")
            logger.debug(f"Arquivo atual: {__file__}")
            logger.debug(f"Base path: {base_path}")
            logger.debug(f"Python path: {sys.path}")
            
            # 2. Tentar carregar usando APP_CONFIG
            logo_light = os.path.join(base_path, APP_CONFIG['icons']['logo_light'])
            logo_dark = os.path.join(base_path, APP_CONFIG['icons']['logo_dark'])
            
            # Adicionar informações ao GUI
            paths_text = (
                f"Diretório atual: {os.getcwd()}\n"
                f"Arquivo atual: {__file__}\n"
                f"Base path: {base_path}\n"
                f"Logo light: {logo_light} (existe: {os.path.exists(logo_light)})\n"
                f"Logo dark: {logo_dark} (existe: {os.path.exists(logo_dark)})\n"
                f"Python path: {sys.path[0]}"
            )
            
            paths_label = ctk.CTkLabel(
                self.main_frame,
                text=paths_text,
                font=("Arial", 12),
                justify="left"
            )
            paths_label.pack(pady=10)
            
            # 3. Tentar carregar a imagem
            if os.path.exists(logo_light) and os.path.exists(logo_dark):
                light_image = Image.open(logo_light)
                dark_image = Image.open(logo_dark)
                
                # Criar CTkImage
                self.images['logo'] = ctk.CTkImage(
                    light_image=light_image,
                    dark_image=dark_image,
                    size=(200, int(200 * (65.2/318.6)))
                )
                
                # Criar label com a imagem
                image_label = ctk.CTkLabel(
                    self.main_frame,
                    image=self.images['logo'],
                    text=""
                )
                image_label.pack(pady=20)
                
                status_label = ctk.CTkLabel(
                    self.main_frame,
                    text="✅ Imagem carregada com sucesso!",
                    font=("Arial", 14, "bold"),
                    text_color="green"
                )
                status_label.pack(pady=10)
            else:
                status_label = ctk.CTkLabel(
                    self.main_frame,
                    text="❌ Arquivos de imagem não encontrados!",
                    font=("Arial", 14, "bold"),
                    text_color="red"
                )
                status_label.pack(pady=10)
            
        except Exception as e:
            error_text = f"Erro ao carregar imagem:\n{str(e)}"
            logger.error(error_text)
            
            error_label = ctk.CTkLabel(
                self.main_frame,
                text=error_text,
                font=("Arial", 14),
                text_color="red"
            )
            error_label.pack(pady=10)

    def toggle_theme(self):
        current_theme = ctk.get_appearance_mode().lower()
        new_theme = "Light" if current_theme == "dark" else "Dark"
        ctk.set_appearance_mode(new_theme)

if __name__ == "__main__":
    app = TesteImagem()
    app.mainloop()
