import customtkinter as ctk
import logging
from PIL import Image
import os, sys
from ...config.settings import APP_CONFIG
import datetime

logger = logging.getLogger(__name__)

class LoadingWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Configurar janela
        window_width = 800
        window_height = 600
        
        # Obter dimensões da tela
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Calcular posição para centralizar
        x = int((screen_width - window_width) / 2)
        y = int((screen_height - window_height) / 2)
        
        # Configurar geometria
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.overrideredirect(True)

        # Adicionar cantos arredondados
        if sys.platform.startswith('win'):
            self.wm_attributes('-transparent', 'black')
            self._set_window_style()

        self.attributes('-topmost', True)
        self.lift()
        self.focus_force()

        # Garantir que permaneça no topo durante o carregamento
        self.grab_set()
        
        # Frame principal
        main_frame = ctk.CTkFrame(self, corner_radius=15, width=800, height=600)
        main_frame.place(relx=0.5, rely=0.5, anchor="center")
        main_frame.pack_propagate(False)

        # Logo adaptativo ao tema
        try:
            # Definir caminhos para as duas versões do logo
            if hasattr(sys, "_MEIPASS"):
                logo_dark_path = os.path.join(sys._MEIPASS, 'icons', 'logo_dark.png')
                logo_light_path = os.path.join(sys._MEIPASS, 'icons', 'logo_light.png')
            else:
                logo_dark_path = os.path.join(os.path.abspath("."), 'icons', 'logo_dark.png')
                logo_light_path = os.path.join(os.path.abspath("."), 'icons', 'logo_light.png')
            
            if os.path.exists(logo_dark_path) and os.path.exists(logo_light_path):
                # Carregar ambas as versões
                dark_image = Image.open(logo_dark_path)
                light_image = Image.open(logo_light_path)
                
                bg_image = ctk.CTkImage(
                    light_image=light_image,
                    dark_image=dark_image,
                    size=(318.6, 65.2)
                )
                logo_label = ctk.CTkLabel(main_frame, image=bg_image, text="")
                logo_label.pack(pady=20)
            else:
                logger.warning(f"Arquivos de logo não encontrados: {logo_dark_path} ou {logo_light_path}")
                # Fallback para o logo padrão se os arquivos específicos não existirem
                logo_path = APP_CONFIG['icons']['logo']
                if os.path.exists(logo_path):
                    pil_image = Image.open(logo_path)
                    bg_image = ctk.CTkImage(
                        light_image=pil_image,
                        dark_image=pil_image,
                        size=(318.6, 65.2)
                    )
                    logo_label = ctk.CTkLabel(main_frame, image=bg_image, text="")
                    logo_label.pack(pady=20)
                else:
                    logger.warning(f"Logo padrão também não encontrado: {logo_path}")
        except Exception as e:
            logger.error(f"Erro ao carregar imagens do logo: {e}")

        # Título e Versão
        title_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        title_frame.pack(pady=10)
        
        title_label = ctk.CTkLabel(
            title_frame, 
            text=APP_CONFIG['title'],
            font=("Roboto", 24, "bold")
        )
        title_label.pack()
        
        version_label = ctk.CTkLabel(
            title_frame,
            text=f"Versão {APP_CONFIG['version']}",
            font=("Roboto", 12),
            text_color="gray"
        )
        version_label.pack()

        # Barra de progresso
        self.progress_bar = ctk.CTkProgressBar(
            main_frame, 
            width=400,
            height=12,
            corner_radius=6,
            fg_color="#333333",
            progress_color="#FF5722"
        )
        self.progress_bar.pack(pady=20)
        self.progress_bar.set(0)

        # Label de status
        self.status_label = ctk.CTkLabel(
            main_frame, 
            text="Carregando...",
            font=("Roboto", 12)
        )
        self.status_label.pack(pady=10)

        # Frase inspiradora
        tip_label = ctk.CTkLabel(
            main_frame,
            text='"O tempo é o recurso mais valioso que temos.\nSaiba gerenciá-lo com sabedoria."',
            font=("Roboto", 20, "italic"),
            text_color="gray"
        )
        tip_label.pack(pady=30)

        # Frame do rodapé com informações organizadas
        footer_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        footer_frame.pack(side="bottom", pady=20, fill="x")

        # Separador
        separator = ctk.CTkFrame(footer_frame, height=1, fg_color="gray")
        separator.pack(fill="x", padx=50, pady=10)

        # Informações dos contribuidores
        contributors_text = (
            "Contribuidores:\n"
            "Roberto Oliveira • Wesdley Ramos • Igor Veloso • Claude (Anthropic)"
        )
        contributors_label = ctk.CTkLabel(
            footer_frame,
            text=contributors_text,
            font=("Roboto", 12),
            text_color="gray"
        )
        contributors_label.pack(pady=5)

        # Frame para licença e copyright
        license_frame = ctk.CTkFrame(footer_frame, fg_color="transparent")
        license_frame.pack(pady=5)
        
        license_label = ctk.CTkLabel(
            license_frame,
            text="Licença MIT",
            font=("Roboto", 12),
            text_color="gray"
        )
        license_label.pack(side="left", padx=10)
        
        # Criar referência para o label de copyright
        self.copyright_label = ctk.CTkLabel(
            license_frame,
            text=f"Copyright © {APP_CONFIG['copyright_year']}",
            font=("Roboto", 12),
            text_color="gray"
        )
        self.copyright_label.pack(side="left", padx=10)

        # Atualizar o ano automaticamente à meia-noite
        self._schedule_year_update()

    def _schedule_year_update(self):
        """Agenda a atualização do ano do copyright"""
        current_year = datetime.datetime.now().year
        if int(APP_CONFIG['copyright_year']) != current_year:
            APP_CONFIG['copyright_year'] = current_year
            self.copyright_label.configure(text=f"Copyright © {current_year}")
        
        # Verificar novamente em 24 horas
        self.after(86400000, self._schedule_year_update)  # 24h em milissegundos

    def _set_window_style(self):
        """Configura o estilo da janela com cantos arredondados no Windows"""
        try:
            from ctypes import windll, byref, sizeof, c_int
            
            DWMWA_WINDOW_CORNER_PREFERENCE = 33
            DWM_WINDOW_CORNER_PREFERENCE = c_int
            DWMWCP_ROUND = 2
            
            windll.dwmapi.DwmSetWindowAttribute(
                windll.user32.GetParent(self.winfo_id()),
                DWMWA_WINDOW_CORNER_PREFERENCE,
                byref(DWM_WINDOW_CORNER_PREFERENCE(DWMWCP_ROUND)),
                sizeof(c_int)
            )
        except Exception as e:
            logger.error(f"Erro ao configurar cantos arredondados: {e}")