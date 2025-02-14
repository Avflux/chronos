import customtkinter as ctk
import logging, os, sys, win32con, win32gui
from tkinter import messagebox
from tendo import singleton
from app.config.settings import APP_CONFIG, LOG_CONFIG
from app.ui.windows.login_window import LoginWindow
from app.utils.window_manager import WindowManager

# Desativa ajuste automático de DPI que pode causar problemas de renderização
ctk.deactivate_automatic_dpi_awareness()

# Configuração de logging
os.makedirs(LOG_CONFIG['log_dir'], exist_ok=True)
logging.basicConfig(
    filename=os.path.join(LOG_CONFIG['log_dir'], 'app.log'),
    level=getattr(logging, LOG_CONFIG['log_level']),
    format=LOG_CONFIG['log_format']
)

logger = logging.getLogger(__name__)

class App:
    def __init__(self):
        # Configuração do tema do CustomTkinter usando settings
        ctk.set_appearance_mode(APP_CONFIG['theme'])
        ctk.set_default_color_theme("green")
        
        # Manter uma lista de janelas ativas
        self.active_windows = []
        
        # Registrar callback para mudanças de tema
        ctk.AppearanceModeTracker.add(self._on_theme_change)
        
        # Adicionar o gerenciador de janelas
        self.window_manager = WindowManager()
        
        # Inicializa a janela de login como janela principal
        self.login_window = LoginWindow(window_manager=self.window_manager)
        self.active_windows.append(self.login_window)

    def _on_theme_change(self, theme=None):
        """Callback para mudanças no tema"""
        try:
            current_theme = ctk.get_appearance_mode()
            logger.info(f"[THEME] Callback de mudança de tema acionado na aplicação principal")
            logger.info(f"[THEME] Novo tema: {current_theme}")
            logger.info(f"[THEME] Parâmetro theme recebido: {theme}")
            
            # Lista temporária para evitar modificar lista durante iteração
            windows_to_remove = []
            
            # Atualizar todas as janelas ativas
            for window in self.active_windows:
                if not window.winfo_exists():
                    windows_to_remove.append(window)
                    continue
                    
                logger.debug(f"[THEME] Atualizando janela: {window}")
                if hasattr(window, '_on_theme_change'):
                    window._on_theme_change()
                
                # Procurar por janelas filhas (Toplevels)
                for child in window.winfo_children():
                    if isinstance(child, ctk.CTk):
                        logger.debug(f"[THEME] Atualizando janela filha: {child}")
                        if hasattr(child, '_on_theme_change'):
                            child._on_theme_change()
            
            # Remover janelas fechadas
            for window in windows_to_remove:
                self.cleanup_window(window)
        
        except Exception as e:
            logger.error(f"[THEME] Erro ao propagar mudança de tema: {str(e)}", exc_info=True)

    def bring_to_front(self, window_title="Sistema Chronos"):
        """Traz a janela existente para frente"""
        try:
            logger.debug("Procurando janela existente com título: %s", window_title)
            
            def enumerate_windows():
                result = []
                def callback(hwnd, _):
                    if win32gui.IsWindowVisible(hwnd):
                        text = win32gui.GetWindowText(hwnd)
                        if window_title in text:
                            result.append(hwnd)
                win32gui.EnumWindows(callback, None)
                return result

            hwnds = enumerate_windows()
            
            if hwnds:
                hwnd = hwnds[0]
                logger.debug("Janela encontrada (hwnd: %s)", hwnd)
                
                # Garante que a janela não está minimizada
                if win32gui.IsIconic(hwnd):
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                
                # Força a janela para frente
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                win32gui.SetForegroundWindow(hwnd)
                
                # Tenta forçar o foco algumas vezes
                for _ in range(3):
                    try:
                        win32gui.BringWindowToTop(hwnd)
                        win32gui.SetForegroundWindow(hwnd)
                    except:
                        pass
                
                return True
                
            logger.warning("Nenhuma janela encontrada com o título especificado")
            return False
            
        except Exception as e:
            logger.error("Erro ao manipular janela: %s", str(e), exc_info=True)
            return False

    def cleanup_window(self, window):
        """Limpa recursos de uma janela específica"""
        try:
            if window in self.active_windows:
                self.active_windows.remove(window)
                
            if hasattr(window, 'cleanup'):
                window.cleanup()
                
            # Forçar coleta de lixo após remover janela
            import gc
            gc.collect()
            
        except Exception as e:
            logger.error(f"Erro ao limpar janela: {e}", exc_info=True)

    def monitor_memory(self):
        """Monitora uso de memória do aplicativo"""
        try:
            import psutil
            process = psutil.Process()
            mem_info = process.memory_info()
            logger.info(f"Uso de memória: {mem_info.rss / 1024 / 1024:.2f} MB")
            
            # Agendar próximo monitoramento em 60 segundos
            self.login_window.after(60000, self.monitor_memory)
            
        except Exception as e:
            logger.error(f"Erro ao monitorar memória: {e}")

    try:
        logger.info("Verificando existência de outra instância do Chronos")
        me = singleton.SingleInstance()
        logger.info("Nova instância iniciada com sucesso")
    except singleton.SingleInstanceException:
        logger.warning("Detectada tentativa de iniciar segunda instância")
        if self.bring_to_front():
            logger.info("Janela existente localizada e trazida para frente")
            messagebox.showinfo("Chronos System", "Uma instância do Chronos já está em execução.")
        else:
            logger.error("Não foi possível localizar a janela do Chronos")
            messagebox.showerror("Erro", "Não foi possível localizar a janela do Chronos.")
        sys.exit(1)

        
    def run(self):
        """Inicia a aplicação"""
        self.monitor_memory()
        self.login_window.mainloop()

if __name__ == "__main__":
    app = App()
    app.run()