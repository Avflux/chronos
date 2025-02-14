import customtkinter as ctk
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw
import threading
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TrayApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Teste Bandeja")
        self.geometry("400x300")
        self.is_minimized = False
        self.tray_icon = None

        self.label = ctk.CTkLabel(self, text="Janela Principal", font=("Roboto", 20))
        self.label.pack(pady=20)

        self.minimize_button = ctk.CTkButton(
            self, text="Minimizar para Bandeja", command=self.minimize_to_tray
        )
        self.minimize_button.pack(pady=10)

        self.close_button = ctk.CTkButton(self, text="Fechar", command=self.quit_app)
        self.close_button.pack(pady=10)

        self.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)

    def create_tray_icon(self):
        def create_image():
            """Cria um ícone básico para a bandeja."""
            image = Image.new("RGB", (64, 64), color=(255, 255, 255))
            draw = ImageDraw.Draw(image)
            draw.rectangle((16, 16, 48, 48), fill="black")
            return image

        def on_restore(icon, item):
            logger.debug("Evento de restaurar acionado pelo clique esquerdo no ícone.")
            self.after(0, self.restore_window)
            icon.stop()

        def on_quit(icon, item):
            logger.debug("Evento de sair acionado pelo menu do ícone.")
            self.after(0, self.quit_app)
            icon.stop()

        # Criar o ícone e o menu
        self.tray_icon = Icon(
            "Teste Bandeja",
            create_image(),
            "Aplicativo Teste",
            menu=Menu(
                MenuItem("Restaurar", on_restore),
                MenuItem("Sair", on_quit),
            )
        )

        # Configurar o clique esquerdo
        self.tray_icon._on_left_click = on_restore

    def minimize_to_tray(self):
        if not self.is_minimized:
            logger.debug("Minimizando para bandeja...")
            self.is_minimized = True
            self.withdraw()
            
            if not self.tray_icon:
                self.create_tray_icon()
            
            if not getattr(self.tray_icon, "active", False):
                threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def restore_window(self):
        logger.debug("Função restore_window chamada.")
        try:
            self.is_minimized = False
            if self.tray_icon and getattr(self.tray_icon, "active", False):
                self.tray_icon.stop()
            self.tray_icon = None
            self.deiconify()
            logger.debug("Janela restaurada com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao restaurar janela: {e}")


    def quit_app(self):
        logger.debug("Encerrando aplicação...")
        if self.tray_icon:
            self.tray_icon.stop()
        self.destroy()

if __name__ == "__main__":
    app = TrayApp()
    app.mainloop()
