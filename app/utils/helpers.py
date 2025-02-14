import customtkinter as ctk
import logging
import os
from ..config.settings import APP_CONFIG

logger = logging.getLogger(__name__)

def get_base_path():
    """Retorna o caminho base do projeto"""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class IconMixin:
    """Mixin para adicionar funcionalidade de ícone consistente"""
    def set_window_icon(self):
        try:
            base_path = get_base_path()
            icon_path = os.path.join(base_path, APP_CONFIG['icons']['app'])
            if os.path.exists(icon_path):
                # Usar o protocolo Tk subjacente para definir o ícone
                self.after(100, lambda: self.tk.call('wm', 'iconbitmap', self._w, icon_path))
                logger.debug(f"Ícone configurado para {self.__class__.__name__}")
            else:
                logger.warning(f"Arquivo de ícone não encontrado: {icon_path}")
        except Exception as e:
            logger.error(f"Erro ao configurar ícone para {self.__class__.__name__}: {e}")

class BaseWindow(ctk.CTkToplevel, IconMixin):
    """Classe base para janelas Toplevel"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.after(100, self.set_window_icon)  # Configura o ícone após a janela ser criada

class BaseDialog(ctk.CTkToplevel, IconMixin):
    """Classe base para diálogos"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.after(100, self.set_window_icon)