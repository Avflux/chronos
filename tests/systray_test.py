import win32gui
import win32con
import win32api
import threading
import logging
import os
from queue import Queue

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Definir constantes
WM_MYMSG = win32con.WM_USER + 20
WM_NOTIFY_ICON = WM_MYMSG + 1

class SystemTrayIcon:
    def __init__(self, icon_path=None, tooltip="Clique para restaurar"):
        self.is_active = False
        self.notification_id = 1
        self.hwnd = None
        self.message_queue = Queue()
        self.icon_path = icon_path
        self.tooltip = tooltip
        
        # Criar janela oculta para receber mensagens
        self.create_message_window()
        
    def create_message_window(self):
        """Cria uma janela oculta para receber mensagens do sistema"""
        def message_loop():
            wc = win32gui.WNDCLASS()
            wc.lpfnWndProc = self.message_handler
            wc.lpszClassName = "SystemTrayMessageWindow"
            wc.hInstance = win32api.GetModuleHandle(None)
            
            try:
                class_atom = win32gui.RegisterClass(wc)
                self.hwnd = win32gui.CreateWindow(
                    class_atom,
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
                self.on_restore()
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
                self.on_restore()
            elif cmd == 2:
                self.on_quit()
                
            win32gui.DestroyMenu(menu)
            
        except Exception as e:
            logger.error(f"Erro ao exibir menu: {e}")
    
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
        self.remove_icon()
        if self.hwnd:
            win32gui.PostMessage(self.hwnd, win32con.WM_QUIT, 0, 0)
    
    # Métodos que devem ser sobrescritos pela classe que herdar
    def on_restore(self):
        """Chamado quando o usuário clica para restaurar"""
        pass
    
    def on_quit(self):
        """Chamado quando o usuário seleciona sair"""
        pass

# Exemplo de uso:
if __name__ == "__main__":
    class ExampleTrayIcon(SystemTrayIcon):
        def on_restore(self):
            print("Restaurar aplicação")
            
        def on_quit(self):
            print("Fechar aplicação")
            self.cleanup()
    
    icon = ExampleTrayIcon()
    icon.add_icon()
    
    # Manter o programa rodando
    import time
    while True:
        time.sleep(1)