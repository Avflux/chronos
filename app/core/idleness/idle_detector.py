import time, threading, win32api, logging
from pynput import keyboard
from ..time.time_observer import TimeObserver
from datetime import timedelta, datetime

logger = logging.getLogger(__name__)

class IdleDetector:
    def __init__(self, mouse_idle_time=10, keyboard_idle_time=10):
        self.mouse_idle_time = mouse_idle_time
        self.keyboard_idle_time = keyboard_idle_time
        self.last_mouse_activity = time.time()
        self.last_keyboard_activity = time.time()
        self.last_mouse_position = win32api.GetCursorPos()
        self.observers = []
        self.is_idle = False
        self.running = False
        self.idle_start_time = None
        self.accumulated_idle_time = timedelta()
        self.BREAK_START_TIME = "12:15:00"
        self.BREAK_END_TIME = "13:15:00"
        logger.info("IdleDetector inicializado")

    def add_observer(self, observer: TimeObserver):
        self.observers.append(observer)
        logger.debug(f"Observer adicionado: {observer.__class__.__name__}")

    def start(self):
        self.running = True
        self.last_mouse_activity = time.time()
        self.last_keyboard_activity = time.time()
        self.last_mouse_position = win32api.GetCursorPos()
        
        try:
            # Iniciar apenas o listener do teclado
            self.keyboard_listener = keyboard.Listener(
                on_press=self._safe_keyboard_callback,
                suppress=False
            )
            self.keyboard_listener.start()
            
            # Iniciar threads de monitoramento
            self.idle_thread = threading.Thread(target=self.monitor_idle_status, daemon=True)
            self.mouse_thread = threading.Thread(target=self.monitor_mouse_movement, daemon=True)
            
            self.idle_thread.start()
            self.mouse_thread.start()
            
            logger.info("IdleDetector iniciado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao iniciar IdleDetector: {e}")
            raise

    def monitor_mouse_movement(self):
        """Thread dedicada para monitorar movimentos do mouse usando win32api"""
        while self.running:
            try:
                current_position = win32api.GetCursorPos()
                if current_position != self.last_mouse_position:
                    self.last_mouse_position = current_position
                    self.last_mouse_activity = time.time()
                    self.check_activity()
                time.sleep(0.1)  # Pequeno delay para não sobrecarregar a CPU
            except Exception as e:
                logger.error(f"Erro ao monitorar mouse: {e}")
                time.sleep(1)

    def _safe_keyboard_callback(self, *args):
        try:
            if self.is_idle:
                logger.info("Atividade do teclado detectada após período ocioso")
            self.last_keyboard_activity = time.time()
            self.check_activity()
        except Exception as e:
            logger.error(f"Erro no callback do teclado: {e}")

    def on_mouse_activity(self, *args):
        if self.is_idle:
            logger.info("Atividade detectada após período ocioso")
        self.last_mouse_activity = time.time()
        self.check_activity()

    def on_keyboard_activity(self, *args):
        if self.is_idle:
            logger.info("Atividade detectada após período ocioso")
        self.last_keyboard_activity = time.time()
        self.check_activity()

    def check_activity(self):
        if self.is_idle:
            self.is_idle = False
            if self.idle_start_time:
                idle_duration = time.time() - self.idle_start_time
                self.accumulated_idle_time += timedelta(seconds=idle_duration)
                logger.info(f"Tempo ocioso acumulado: {self.accumulated_idle_time}")
                self.notify_observers('active')
                self.idle_start_time = None

    def monitor_idle_status(self):
        while self.running:
            try:
                # Verificar se está no horário de intervalo
                current_time = datetime.now().time()
                break_start = datetime.strptime(self.BREAK_START_TIME, "%H:%M:%S").time()
                break_end = datetime.strptime(self.BREAK_END_TIME, "%H:%M:%S").time()
                
                # Se estiver no horário de intervalo, não registra ociosidade
                if break_start <= current_time <= break_end:
                    if self.is_idle:
                        self.is_idle = False
                        self.notify_observers('active')
                    time.sleep(1)
                    continue

                # Resto do código original de monitoramento
                current_time = time.time()
                mouse_idle_time = current_time - self.last_mouse_activity
                keyboard_idle_time = current_time - self.last_keyboard_activity
                
                is_idle = (mouse_idle_time > self.mouse_idle_time and 
                          keyboard_idle_time > self.keyboard_idle_time)
                
                if is_idle and not self.is_idle:
                    self.is_idle = True
                    self.idle_start_time = current_time
                    logger.info(f"Iniciando período ocioso após {self.mouse_idle_time} segundos")
                    self.notify_observers('idle')
                
                time.sleep(1)  # Verificar a cada segundo
                
            except Exception as e:
                logger.error(f"Erro no monitoramento de ociosidade: {e}")

    def notify_observers(self, status):
        for observer in self.observers:
            try:
                observer.update_idle_status(status)
            except Exception as e:
                logger.error(f"Erro ao notificar observer {observer.__class__.__name__}: {e}")

    def get_accumulated_idle_time(self):
        if self.is_idle and self.idle_start_time:
            current_duration = timedelta(seconds=time.time() - self.idle_start_time)
            return self.accumulated_idle_time + current_duration
        return self.accumulated_idle_time

    def reset_accumulated_idle_time(self):
        previous_time = self.accumulated_idle_time
        self.accumulated_idle_time = timedelta()
        logger.info(f"Tempo ocioso resetado. Anterior: {previous_time}")

    def reset_idle_counter(self):
        """Reseta os contadores de ociosidade"""
        try:
            self.last_mouse_activity = time.time()
            self.last_keyboard_activity = time.time()
            self.last_mouse_position = win32api.GetCursorPos()
            self.is_idle = False
            self.idle_start_time = None
            self.accumulated_idle_time = timedelta()
            logger.debug("Contadores de ociosidade resetados")
        except Exception as e:
            logger.error(f"Erro ao resetar contadores de ociosidade: {e}")

    def stop(self):
        self.running = False
        if hasattr(self, 'keyboard_listener'):
            self.keyboard_listener.stop()
        logger.info("IdleDetector parado") 