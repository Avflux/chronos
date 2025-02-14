import customtkinter as ctk
import win32gui
import win32con
import win32api
import threading
import logging
from queue import Queue
import os

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Definir constantes
WM_MYMSG = win32con.WM_USER + 20
WM_NOTIFY_ICON = WM_MYMSG + 1

class TestWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configuração da janela
        self.title("Teste Bandeja Chronos")
        self.geometry("400x300")
        
        # Flags de controle
        self.is_minimized = False
        self.notification_id = 1
        self.hwnd = None
        self.message_queue = Queue()
        
        # Interface básica
        self.label = ctk.CTkLabel(
            self, 
            text="Teste de Minimização para Bandeja",
            font=("Roboto", 20)
        )
        self.label.pack(pady=20)
        
        self.btn_minimize = ctk.CTkButton(
            self,
            text="Minimizar para Bandeja",
            command=self.minimize_to_tray,
            fg_color="#FF5722",
            hover_color="#CE461B"
        )
        self.btn_minimize.pack(pady=10)
        
        # Interceptar fechamento da janela
        self.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)
        
        # Criar janela oculta para receber mensagens
        self.create_message_window()
        
        # Iniciar processamento de mensagens
        self.after(100, self.process_messages)
        
    def create_message_window(self):
        """Cria uma janela oculta para receber mensagens do sistema"""
        def message_loop():
            wc = win32gui.WNDCLASS()
            wc.lpfnWndProc = self.message_handler
            wc.lpszClassName = "ChronosMessageWindow"
            wc.hInstance = win32api.GetModuleHandle(None)
            
            try:
                class_atom = win32gui.RegisterClass(wc)
                self.hwnd = win32gui.CreateWindow(
                    class_atom,
                    "ChronosWindow",
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
        
        # Iniciar loop de mensagens em uma thread separada
        thread = threading.Thread(target=message_loop, daemon=True)
        thread.start()
        
    def message_handler(self, hwnd, msg, wparam, lparam):
        """Trata mensagens recebidas pela janela oculta"""
        if msg == WM_NOTIFY_ICON:
            # Clique simples com botão esquerdo
            if lparam == win32con.WM_LBUTTONUP:
                self.message_queue.put("restaurar")
            # Menu de contexto com botão direito
            elif lparam == win32con.WM_RBUTTONUP:
                self.show_menu()
            return True
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)
    
    def show_menu(self):
        """Exibe menu de contexto da bandeja"""
        try:
            menu = win32gui.CreatePopupMenu()
            # Criar itens do menu (ID, Texto)
            items = [
                (1, "Restaurar"),
                (2, "Fechar")
            ]
            
            # Adicionar itens ao menu
            for id, text in items:
                win32gui.AppendMenu(menu, win32con.MF_STRING, id, text)
            
            # Obter posição do cursor
            pos = win32gui.GetCursorPos()
            
            # Trazer janela para frente
            win32gui.SetForegroundWindow(self.hwnd)
            
            # Exibir menu e obter seleção do usuário
            cmd = win32gui.TrackPopupMenu(
                menu,
                win32con.TPM_LEFTALIGN | win32con.TPM_RIGHTBUTTON | win32con.TPM_RETURNCMD,
                pos[0],
                pos[1],
                0,
                self.hwnd,
                None
            )
            
            # Processar seleção
            if cmd == 1:  # Restaurar
                self.message_queue.put("restaurar")
            elif cmd == 2:  # Fechar
                self.message_queue.put("fechar")
                
            # Destruir menu
            win32gui.DestroyMenu(menu)
            
        except Exception as e:
            logger.error(f"Erro ao exibir menu: {e}")

    def process_messages(self):
        """Processa mensagens na fila na thread principal"""
        try:
            while not self.message_queue.empty():
                mensagem = self.message_queue.get_nowait()
                if mensagem == "restaurar":
                    self.restore_window()
                elif mensagem == "fechar":
                    self.quit_app()
        except Exception as e:
            logger.error(f"Erro ao processar mensagens: {e}")
            
        self.after(100, self.process_messages)
        
    def add_notify_icon(self):
        """Adiciona ícone na bandeja do sistema"""
        # Obter caminho do diretório atual
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Construir caminho do ícone relativo ao arquivo atual
        icon_path = os.path.join(current_dir, "..", "icons", "app.ico")
        
        logger.debug(f"Tentando carregar ícone do caminho: {icon_path}")
        icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
        
        try:
            hicon = win32gui.LoadImage(
                None,
                icon_path,
                win32con.IMAGE_ICON,
                0,
                0,
                icon_flags
            )
        except Exception as e:
            logger.error(f"Erro ao carregar ícone: {e}")
            # Fallback para ícone padrão do Windows
            hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
        
        flags = win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP | win32gui.NIF_INFO
        nid = (
            self.hwnd,
            self.notification_id,
            flags,
            WM_NOTIFY_ICON,
            hicon,
            "Clique para restaurar"  # Dica ao passar o mouse
        )
        
        try:
            win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)
            return True
        except Exception as e:
            logger.error(f"Erro ao adicionar ícone: {e}")
            return False
            
    def remove_notify_icon(self):
        """Remove ícone da bandeja do sistema"""
        if self.hwnd:
            try:
                nid = (self.hwnd, self.notification_id)
                win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
            except Exception as e:
                logger.error(f"Erro ao remover ícone: {e}")
        
    def minimize_to_tray(self):
        """Minimiza a janela para a bandeja do sistema"""
        if not self.is_minimized:
            try:
                logger.debug("Minimizando para bandeja")
                if self.add_notify_icon():
                    self.withdraw()
                    self.is_minimized = True
                
            except Exception as e:
                logger.error(f"Erro ao minimizar: {e}")
                self.is_minimized = False

    def restore_window(self):
        """Restaura a janela do estado minimizado"""
        try:
            logger.debug("Iniciando restauração da janela")
            
            # Remover ícone e restaurar janela
            self.remove_notify_icon()
            self.deiconify()
            self.lift()
            self.state('normal')
            self.focus_force()
            
            self.is_minimized = False
            
        except Exception as e:
            logger.error(f"Erro ao restaurar janela: {e}")
        
    def quit_app(self):
        """Encerra a aplicação adequadamente"""
        try:
            logger.debug("Encerrando aplicação")
            self.remove_notify_icon()
            
            # Postar mensagem de WM_QUIT para a thread de mensagens
            if self.hwnd:
                win32gui.PostMessage(self.hwnd, win32con.WM_QUIT, 0, 0)
            
            # Destruir a janela principal
            self.destroy()
            
        except Exception as e:
            logger.error(f"Erro ao encerrar: {e}")
            self.destroy()  # Garante que a janela seja destruída mesmo com erro

if __name__ == "__main__":
    app = TestWindow()
    app.mainloop()