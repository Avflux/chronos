import win32gui
import win32con
import win32api
import threading
import logging
import os
import sys
from queue import Queue
from ...config.settings import APP_CONFIG
from ...utils.helpers import get_base_path
import time

logger = logging.getLogger(__name__)

# Definir constantes
WM_MYMSG = win32con.WM_USER + 20
WM_NOTIFY_ICON = WM_MYMSG + 1

class SystemTrayIcon:
    _class_registered = False  # Variável de classe para controlar registro
    _class_name = "SystemTrayMessageWindow"
    
    def __init__(self, window, on_quit_callback=None):
        self.window = window
        self.on_quit_callback = on_quit_callback
        self.is_active = False
        self.notification_id = 1
        self.hwnd = None
        self.message_queue = Queue()
        
        # Obter caminho do ícone considerando execução como exe ou script
        base_path = get_base_path()
        icon_path = os.path.join(base_path, APP_CONFIG['icons']['app'])
        self.icon_path = icon_path
        self.tooltip = "Sistema Chronos"
        
        # Criar janela oculta para receber mensagens
        self.create_message_window()
        
    def create_message_window(self):
        """Cria uma janela oculta para receber mensagens do sistema"""
        def message_loop():
            wc = win32gui.WNDCLASS()
            wc.lpfnWndProc = self.message_handler
            wc.lpszClassName = self._class_name
            wc.hInstance = win32api.GetModuleHandle(None)
            
            try:
                # Verifica se a classe já está registrada
                if not SystemTrayIcon._class_registered:
                    try:
                        class_atom = win32gui.RegisterClass(wc)
                        SystemTrayIcon._class_registered = True
                        logger.debug("Classe de janela registrada com sucesso")
                    except win32gui.error as e:
                        if e.winerror != 1410:  # Ignora erro de classe já existente
                            raise
                        logger.debug("Classe de janela já registrada")
                
                self.hwnd = win32gui.CreateWindow(
                    self._class_name,
                    "SystemTrayWindow",
                    0,
                    0, 0, 0, 0,
                    0,
                    0,
                    wc.hInstance,
                    None
                )
                
                while True:
                    try:
                        win32gui.PumpMessages()
                    except Exception as e:
                        logger.error(f"Erro no loop de mensagens: {e}")
                        break
                        
            except Exception as e:
                logger.error(f"Erro ao criar janela de mensagens: {e}")
        
        thread = threading.Thread(target=message_loop, daemon=True)
        thread.start()
        
    def message_handler(self, hwnd, msg, wparam, lparam):
        """Trata mensagens recebidas pela janela oculta"""
        if msg == WM_NOTIFY_ICON:
            if lparam == win32con.WM_LBUTTONUP:
                self.restore_window()
            elif lparam == win32con.WM_RBUTTONUP:
                self.show_menu()
            return True
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)
    
    def show_menu(self):
        """Exibe menu de contexto da bandeja"""
        try:
            menu = win32gui.CreatePopupMenu()
            items = [
                (1, "Restaurar"),
                (2, "Fechar")
            ]
            
            for id, text in items:
                win32gui.AppendMenu(menu, win32con.MF_STRING, id, text)
            
            pos = win32gui.GetCursorPos()
            win32gui.SetForegroundWindow(self.hwnd)
            
            cmd = win32gui.TrackPopupMenu(
                menu,
                win32con.TPM_LEFTALIGN | win32con.TPM_RIGHTBUTTON | win32con.TPM_RETURNCMD,
                pos[0],
                pos[1],
                0,
                self.hwnd,
                None
            )
            
            if cmd == 1:
                self.restore_window()
            elif cmd == 2:
                self.quit_app()
                
            win32gui.DestroyMenu(menu)
            
        except Exception as e:
            logger.error(f"Erro ao exibir menu: {e}")
    
    def minimize_to_tray(self):
        """Minimiza a janela para a bandeja"""
        if not self.is_active:
            self.window.withdraw()
            self.add_icon()
    
    def add_icon(self):
        """Adiciona ícone na bandeja do sistema"""
        try:
            if self.icon_path:
                icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
                hicon = win32gui.LoadImage(
                    None,
                    self.icon_path,
                    win32con.IMAGE_ICON,
                    0,
                    0,
                    icon_flags
                )
            else:
                hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
            
            flags = win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP | win32gui.NIF_INFO
            nid = (self.hwnd, self.notification_id, flags, WM_NOTIFY_ICON, hicon, self.tooltip)
            
            win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)
            self.is_active = True
            return True
            
        except Exception as e:
            logger.error(f"Erro ao adicionar ícone: {e}")
            return False
    
    def remove_icon(self):
        """Remove ícone da bandeja do sistema"""
        if self.hwnd:
            try:
                nid = (self.hwnd, self.notification_id)
                win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
                self.is_active = False
            except Exception as e:
                logger.error(f"Erro ao remover ícone: {e}")
    
    def cleanup(self):
        """Limpa recursos do ícone"""
        try:
            # Primeiro, remover o ícone da bandeja
            if hasattr(self, 'notification_id'):
                win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, (self.hwnd, self.notification_id))
                del self.notification_id
                
            # Dar um pequeno delay para garantir que o Windows processou a remoção
            time.sleep(0.1)
            
            # Depois destruir a janela
            if hasattr(self, 'hwnd') and self.hwnd:
                win32gui.PostMessage(self.hwnd, win32con.WM_QUIT, 0, 0)
                win32gui.DestroyWindow(self.hwnd)
                self.hwnd = None
                
            # Tenta desregistrar a classe apenas se foi registrada
            if SystemTrayIcon._class_registered:
                try:
                    win32gui.UnregisterClass(self._class_name, win32api.GetModuleHandle(None))
                    SystemTrayIcon._class_registered = False
                    logger.debug("Classe de janela desregistrada com sucesso")
                except Exception as e:
                    logger.error(f"Erro ao desregistrar classe de janela: {e}")
                    
        except Exception as e:
            logger.error(f"Erro durante cleanup: {str(e)}")
        finally:
            # Garantir que a referência da janela seja limpa mesmo em caso de erro
            self.hwnd = None
    
    def restore_window(self, *args):
        """Restaura a janela principal"""
        self.remove_icon()
        self.window.deiconify()
        self.window.lift()
        self.window.state('normal')
    
    def quit_app(self, *args):
        """Fecha a aplicação"""
        self.cleanup()
        if self.on_quit_callback:
            self.on_quit_callback()
        self.window.quit()