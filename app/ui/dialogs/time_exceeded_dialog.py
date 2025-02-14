import customtkinter as ctk
from PIL import Image
import os
import sys
import logging

logger = logging.getLogger(__name__)

class TimeExceededDialog(ctk.CTkToplevel):
    def __init__(self, parent, activity_name=None):
        super().__init__(parent)
        
        # Configurações básicas da janela
        self.title("Tempo Excedido")
        self.geometry("400x350")
        self.resizable(False, False)
        
        # Centralizar a janela
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
        
        # Carregar ícone de alerta
        try:
            if hasattr(sys, "_MEIPASS"):
                icons_dir = os.path.join(sys._MEIPASS, 'icons')
            else:
                icons_dir = os.path.join(os.path.abspath("."), 'icons')
                
            alert_path = os.path.join(icons_dir, 'alert.png')
            if os.path.exists(alert_path):
                alert_image = Image.open(alert_path)
                self.alert_icon = ctk.CTkImage(
                    light_image=alert_image,
                    dark_image=alert_image,
                    size=(64, 64)
                )
                
                # Adicionar ícone
                self.icon_label = ctk.CTkLabel(
                    self,
                    image=self.alert_icon,
                    text=""
                )
                self.icon_label.pack(pady=20)
        except Exception as e:
            logger.error(f"Erro ao carregar ícone: {e}")
            
        # Título
        self.title_label = ctk.CTkLabel(
            self,
            text="Tempo Excedido!",
            font=("Roboto", 24, "bold"),
            text_color="#FF5722"
        )
        self.title_label.pack(pady=10)
        
        # Mensagem
        message_text = "O tempo estimado para esta atividade foi excedido!"
        if activity_name:
            message_text += f"\n\nAtividade: {activity_name}"
        
        self.message_label = ctk.CTkLabel(
            self,
            text=message_text,
            font=("Roboto", 14),
            justify="center"
        )
        self.message_label.pack(pady=20)
        
        # Botão de OK
        self.ok_button = ctk.CTkButton(
            self,
            text="OK",
            command=self.destroy,
            fg_color="#FF5722",
            hover_color="#CE461B",
            width=120,
            height=35
        )
        self.ok_button.pack(pady=20)
        
        # Trazer janela para frente
        self.lift()
        self.focus_force()
        
        # Configurar som de notificação (se disponível)
        try:
            self.bell()
        except:
            pass
