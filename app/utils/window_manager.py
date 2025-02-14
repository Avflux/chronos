import win32api
import json
import os
import logging
from typing import Tuple
import ctypes
from ctypes import wintypes
import win32con

logger = logging.getLogger(__name__)

class WindowManager:
    def __init__(self):
        self.config_file = "window_positions.json"
        self.positions = self._load_positions()
        self.last_monitor = self.positions.get('last_monitor', None)  # Carrega o último monitor usado
        logger.debug(f"[WINDOW] Carregou último monitor: {self.last_monitor}")

    def _load_positions(self) -> dict:
        """Carrega as posições salvas das janelas"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar posições das janelas: {e}")
        return {}

    def _save_positions(self):
        """Salva as posições das janelas"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.positions, f)
        except Exception as e:
            logger.error(f"Erro ao salvar posições das janelas: {e}")

    def _save_monitor_position(self, monitor_rect):
        """Salva a posição do monitor"""
        try:
            self.last_monitor = monitor_rect
            self.positions['last_monitor'] = monitor_rect
            self._save_positions()
            logger.debug(f"[WINDOW] Salvou posição do monitor: {monitor_rect}")
        except Exception as e:
            logger.error(f"[WINDOW] Erro ao salvar posição do monitor: {e}")

    def get_cursor_pos(self) -> Tuple[int, int]:
        """Obtém a posição atual do cursor usando ctypes"""
        try:
            point = wintypes.POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
            return (point.x, point.y)
        except Exception as e:
            logger.error(f"Erro ao obter posição do cursor: {e}")
            return (0, 0)

    def get_current_monitor(self) -> Tuple[int, int, int, int]:
        """Retorna as dimensões do monitor onde o mouse está"""
        try:
            # Pega a posição atual do mouse usando ctypes
            cursor_x, cursor_y = self.get_cursor_pos()
            logger.debug(f"Posição do cursor: x={cursor_x}, y={cursor_y}")
            
            # Pega o monitor onde o mouse está
            monitor = win32api.MonitorFromPoint((cursor_x, cursor_y), win32api.MONITOR_DEFAULTTONEAREST)
            monitor_info = win32api.GetMonitorInfo(monitor)
            monitor_rect = monitor_info['Monitor']
            
            logger.debug(f"Monitor encontrado: {monitor_rect}")
            return monitor_rect
            
        except Exception as e:
            logger.error(f"Erro ao obter monitor atual: {e}")
            return None

    def get_monitor_from_window(self, window) -> Tuple[int, int, int, int]:
        """Obtém o monitor onde a janela está"""
        try:
            # Pega o handle da janela
            hwnd = window.winfo_id()
            # Obtém o monitor onde a janela está
            monitor = win32api.MonitorFromWindow(hwnd, win32con.MONITOR_DEFAULTTONEAREST)
            monitor_info = win32api.GetMonitorInfo(monitor)
            return monitor_info['Monitor']
        except Exception as e:
            logger.error(f"[WINDOW] Erro ao obter monitor da janela: {e}")
            return None

    def position_window(self, window, parent=None):
        """Posiciona a janela no monitor correto"""
        try:
            # Define as dimensões da janela
            if window.__class__.__name__ == 'LoginWindow':
                width, height = 900, 600
            elif window.__class__.__name__ in ['AdminWindow', 'UserWindow']:
                width, height = 1400, 700
            else:
                width = window.winfo_reqwidth()
                height = window.winfo_reqheight()

            # Determina o monitor correto
            if parent and parent.winfo_exists():
                # Se tem pai e ele existe, pega o monitor dele
                monitor_rect = self.get_monitor_from_window(parent)
                if monitor_rect:
                    self._save_monitor_position(monitor_rect)
                    logger.debug(f"[WINDOW] Usando monitor da janela pai: {monitor_rect}")
            elif window.__class__.__name__ == 'LoginWindow':
                if self.last_monitor:
                    # Se tiver um monitor salvo, usa ele para a janela de login
                    monitor_rect = self.last_monitor
                    logger.debug(f"[WINDOW] Login window usando último monitor salvo: {monitor_rect}")
                else:
                    # Se não tiver, usa o monitor primário
                    monitor = win32api.MonitorFromWindow(window.winfo_id(), win32con.MONITOR_DEFAULTTOPRIMARY)
                    monitor_rect = win32api.GetMonitorInfo(monitor)['Monitor']
                    self._save_monitor_position(monitor_rect)
                    logger.debug(f"[WINDOW] Login window usando monitor primário: {monitor_rect}")
            else:
                # Usa o último monitor conhecido
                monitor_rect = self.last_monitor
                logger.debug(f"[WINDOW] Usando último monitor conhecido: {monitor_rect}")

            if not monitor_rect:
                logger.warning(f"[WINDOW] Nenhum monitor encontrado para {window.__class__.__name__}")
                raise ValueError("Monitor não encontrado")

            # Extrai as coordenadas do monitor
            monitor_left, monitor_top, monitor_right, monitor_bottom = monitor_rect
            
            # Calcula o centro do monitor
            monitor_width = monitor_right - monitor_left
            monitor_height = monitor_bottom - monitor_top
            
            # Calcula a posição centralizada
            x = monitor_left + (monitor_width - width) // 2
            y = monitor_top + (monitor_height - height) // 2
            
            # Força a janela para a posição calculada
            window.geometry(f"{width}x{height}+{x}+{y}")
            window.update_idletasks()  # Força atualização imediata
            
            # Registra a posição para debug
            logger.debug(f"[WINDOW] Posicionando {window.__class__.__name__} em monitor {monitor_rect}")
            logger.debug(f"[WINDOW] Geometria calculada: {width}x{height}+{x}+{y}")
            
        except Exception as e:
            logger.error(f"[WINDOW] Erro ao posicionar janela: {e}")
            # Fallback para centro do monitor primário
            try:
                screen_width = win32api.GetSystemMetrics(0)
                screen_height = win32api.GetSystemMetrics(1)
                x = (screen_width - width) // 2
                y = (screen_height - height) // 2
                window.geometry(f"{width}x{height}+{x}+{y}")
            except:
                window.geometry(f"{width}x{height}+0+0") 