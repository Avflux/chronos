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
    _instances = 0  # Contador de instâncias ativas
    
    def __init__(self, window, on_quit_callback=None):
        SystemTrayIcon._instances += 1
        self.instance_id = SystemTrayIcon._instances
        self._class_name = f"{self._class_name}_{self.instance_id}"  # Nome único para cada instância
        
        self.window = window
        self.on_quit_callback = on_quit_callback
        self.is_active = False
        self.notification_id = 1
        self.hwnd = None
        self.message_queue = Queue()
        
        # Obter caminho do ícone
        base_path = get_base_path()
        icon_path = os.path.join(base_path, APP_CONFIG['icons']['app'])
        self.icon_path = icon_path
        self.tooltip = "Sistema Chronos"
        
        # Criar janela oculta para receber mensagens
        self.create_message_window()
        
    def create_message_window(self):
        """Cria uma janela oculta para receber mensagens do sistema"""
        def message_loop():
            try:
                # Sempre registrar uma nova classe para cada instância
                wc = win32gui.WNDCLASS()
                wc.lpfnWndProc = self.message_handler
                wc.lpszClassName = self._class_name
                wc.hInstance = win32api.GetModuleHandle(None)
                
                try:
                    win32gui.RegisterClass(wc)
                    logger.debug(f"Classe de janela registrada com sucesso: {self._class_name}")
                except win32gui.error as e:
                    if e.winerror != 1410:  # Ignora erro de classe já existente
                        raise
                    logger.debug(f"Classe de janela já registrada: {self._class_name}")

                # Criar a janela com nome único
                self.hwnd = win32gui.CreateWindow(
                    self._class_name,
                    f"SystemTrayWindow_{self.instance_id}",
                    0,
                    0, 0, 0, 0,
                    0,
                    0,
                    win32api.GetModuleHandle(None),
                    None
                )
                
                if not self.hwnd:
                    raise Exception("Falha ao criar janela de mensagens")

                logger.debug(f"Janela de mensagens criada com hwnd: {self.hwnd}")
                
                while True:
                    try:
                        win32gui.PumpMessages()
                    except Exception as e:
                        logger.error(f"Erro no loop de mensagens: {e}")
                        break
                        
            except Exception as e:
                logger.error(f"Erro ao criar janela de mensagens: {e}")
                self.hwnd = None

        thread = threading.Thread(target=message_loop, daemon=True)
        thread.start()
        
        for _ in range(10):
            if self.hwnd:
                break
            time.sleep(0.1)
        
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
            # Verificar se o handle da janela é válido
            if not self.hwnd or not win32gui.IsWindow(self.hwnd):
                logger.warning("Handle da janela inválido, recriando janela de mensagens")
                self.create_message_window()
                # Aguardar um pouco para a janela ser criada
                time.sleep(0.1)
                if not self.hwnd:
                    logger.error("Não foi possível recriar a janela de mensagens")
                    return

            menu = win32gui.CreatePopupMenu()
            items = [
                (1, "Restaurar"),
                (2, "Fechar")
            ]
            
            for id, text in items:
                win32gui.AppendMenu(menu, win32con.MF_STRING, id, text)
            
            pos = win32gui.GetCursorPos()
            
            # Tentar definir a janela como foreground
            try:
                win32gui.SetForegroundWindow(self.hwnd)
            except Exception as e:
                logger.warning(f"Erro ao definir janela como foreground: {e}")
                # Tentar alternativa
                win32gui.BringWindowToTop(self.hwnd)
            
            try:
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
                
            finally:
                win32gui.DestroyMenu(menu)
                # Enviar mensagem de cancelamento do menu
                win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)
            
        except Exception as e:
            logger.error(f"Erro ao exibir menu: {e}")
            # Tentar recriar o ícone
            self.remove_icon()
            time.sleep(0.1)
            self.add_icon()
    
    def minimize_to_tray(self):
        """Minimiza a janela para a bandeja"""
        try:
            if not self.is_active:
                # Verificar se a janela ainda existe
                if self.window and self.window.winfo_exists():
                    self.window.withdraw()
                    if self.add_icon():
                        logger.debug("Janela minimizada para bandeja com sucesso")
                    else:
                        logger.error("Falha ao minimizar para bandeja")
                        self.window.deiconify()
                else:
                    logger.error("Janela não existe mais")
                    self.cleanup()
        except Exception as e:
            logger.error(f"Erro ao minimizar para bandeja: {e}")
    
    def add_icon(self):
        """Adiciona ícone na bandeja do sistema"""
        try:
            # Verificar se já existe um ícone ativo
            if self.is_active:
                logger.debug("Ícone já está ativo")
                return True
            
            # Verificar se o handle é válido
            if not self.hwnd or not isinstance(self.hwnd, int):
                logger.warning("Handle inválido, recriando janela de mensagens")
                self.create_message_window()
                if not self.hwnd:
                    return False

            if self.icon_path:
                icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
                try:
                    hicon = win32gui.LoadImage(
                        None,
                        self.icon_path,
                        win32con.IMAGE_ICON,
                        0,
                        0,
                        icon_flags
                    )
                except Exception as e:
                    logger.error(f"Erro ao carregar ícone: {e}")
                    hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
            else:
                hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
            
            flags = win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP | win32gui.NIF_INFO
            nid = (self.hwnd, self.notification_id, flags, WM_NOTIFY_ICON, hicon, self.tooltip)
            
            win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)
            self.is_active = True
            logger.debug("Ícone adicionado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao adicionar ícone: {e}")
            self.is_active = False
            return False
    
    def remove_icon(self):
        """Remove ícone da bandeja do sistema"""
        try:
            if not self.is_active:
                return
            
            if self.hwnd and isinstance(self.hwnd, int):
                try:
                    nid = (self.hwnd, self.notification_id)
                    win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
                    self.is_active = False
                    logger.debug("Ícone removido com sucesso")
                except Exception as e:
                    logger.error(f"Erro ao remover ícone: {e}")
            else:
                logger.warning("Handle da janela inválido ao tentar remover ícone")
            
        except Exception as e:
            logger.error(f"Erro ao remover ícone: {e}")
        finally:
            self.is_active = False
    
    def cleanup(self):
        """Limpa recursos do ícone"""
        try:
            if not self.is_active and not self.hwnd:
                return

            # Remover ícone
            try:
                if self.is_active and self.hwnd:
                    nid = (self.hwnd, self.notification_id)
                    win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
                    self.is_active = False
                    logger.debug("Ícone removido da bandeja com sucesso")
            except Exception as e:
                logger.warning(f"Erro ao remover ícone da bandeja: {e}")

            time.sleep(0.1)
            
            # Destruir janela
            try:
                if self.hwnd:
                    win32gui.PostMessage(self.hwnd, win32con.WM_QUIT, 0, 0)
                    win32gui.DestroyWindow(self.hwnd)
                    logger.debug("Janela destruída com sucesso")
            except Exception as e:
                logger.warning(f"Erro ao destruir janela: {e}")
            
            # Desregistrar classe
            try:
                win32gui.UnregisterClass(self._class_name, win32api.GetModuleHandle(None))
                logger.debug(f"Classe desregistrada com sucesso: {self._class_name}")
            except Exception as e:
                logger.warning(f"Erro ao desregistrar classe: {e}")
            
        except Exception as e:
            logger.error(f"Erro durante cleanup: {e}")
        finally:
            SystemTrayIcon._instances -= 1
            self.hwnd = None
            self.notification_id = None
            self.is_active = False
    
    def restore_window(self, *args):
        """Restaura a janela principal"""
        try:
            # Primeiro verificar se a janela ainda existe
            if not self.window:
                logger.error("Referência da janela principal perdida")
                self.cleanup()
                return

            # Verificar se a janela tem método show_window
            if hasattr(self.window, 'show_window'):
                try:
                    self.remove_icon()
                    self.window.show_window()
                    logger.debug("Janela restaurada usando show_window()")
                    return
                except Exception as e:
                    logger.error(f"Erro ao usar show_window(): {e}")

            # Fallback para método padrão
            try:
                self.remove_icon()
                self.window.deiconify()
                self.window.lift()
                self.window.state('normal')
                self.window.focus_force()
                logger.debug("Janela restaurada usando método padrão")
            except Exception as e:
                logger.error(f"Erro ao restaurar janela: {e}")
                self.cleanup()
            
        except Exception as e:
            logger.error(f"Erro ao restaurar janela: {e}")
            self.cleanup()
    
    def quit_app(self, *args):
        """Fecha a aplicação"""
        self.cleanup()
        if self.on_quit_callback:
            self.on_quit_callback()
        self.window.quit()