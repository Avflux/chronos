from datetime import timedelta, datetime
from typing import Optional, Dict
import logging
import threading

logger = logging.getLogger(__name__)

class TimeState:
   def __init__(self):
       # Timer state
       self.is_running: bool = False
       self.current_mode: str = 'regressivo'
       
       # Time markers 
       self.start_time: Optional[datetime] = None
       self.pause_start_time: Optional[datetime] = None
       self.chronometer_start: Optional[datetime] = None
       
       # Timers
       self.accumulated_time: int = 0  # em segundos
       self.total_paused_time: timedelta = timedelta()
       self.total_elapsed_time: timedelta = timedelta()
       self.initial_timer_value: timedelta = timedelta()
       self.timer_value: timedelta = timedelta()
       
       # Activity info
       self.activity_info: Optional[Dict] = None
       self._state_lock = threading.Lock()
       self.reset()

   def reset(self):
       """Reset completo do estado"""
       logger.debug("[STATE_RESET] ---- Iniciando reset completo ----")
       logger.debug("[STATE_RESET] Estado anterior:")
       logger.debug(f"  - Modo: {self.current_mode}")
       logger.debug(f"  - Timer Value: {self.timer_value}")
       logger.debug(f"  - Total Time: {self.total_elapsed_time}")

       self.is_running = False
       self.current_mode = 'regressivo'
       self.start_time = None
       self.pause_start_time = None
       self.chronometer_start = None
       self.accumulated_time = 0
       self.total_paused_time = timedelta()
       self.total_elapsed_time = timedelta()
       self.initial_timer_value = timedelta()
       self.timer_value = timedelta()
       self.activity_info = None

       # Garantir que os observadores sejam notificados do reset
       if hasattr(self, 'notify_observers_timer'):
           self.notify_observers_timer(timedelta(), timedelta())

       logger.debug("[STATE_RESET] Novo estado:")
       logger.debug(f"  - Modo: {self.current_mode}")
       logger.debug(f"  - Timer Value: {self.timer_value}")
       logger.debug(f"  - Total Time: {self.total_elapsed_time}")
       logger.debug("[STATE_RESET] ---- Reset completo finalizado ----")

   def set_activity_info(self, activity_info: Dict):
        with self._state_lock:
            self.activity_info = activity_info
            if activity_info:
                self.initial_timer_value = self._calculate_initial_time()
                self.timer_value = self.initial_timer_value
                
                # Processar tempo total já acumulado
                if 'total_time' in activity_info and activity_info['total_time']:
                    try:
                        h, m, s = map(int, activity_info['total_time'].split(':'))
                        self.accumulated_time = h * 3600 + m * 60 + s
                        self.total_elapsed_time = timedelta(seconds=self.accumulated_time)
                    except Exception as e:
                        logger.error(f"Erro ao processar tempo total: {e}")
                        self.accumulated_time = 0
                        self.total_elapsed_time = timedelta()

   def _calculate_initial_time(self) -> timedelta:
       """Calcula o tempo total entre início e fim previstos"""
       try:
           logger.debug("[TIME_CALC] ---- Iniciando cálculo de tempo inicial ----")
           
           if not self.activity_info:
               logger.debug("[TIME_CALC] Sem activity_info, retornando zero")
               return timedelta()
               
           start_time = self.activity_info['start_time']
           end_time = self.activity_info['end_time']
           
           if isinstance(start_time, str):
               start_time = datetime.strptime(start_time, '%d/%m/%Y %H:%M')
           if isinstance(end_time, str):
               end_time = datetime.strptime(end_time, '%d/%m/%Y %H:%M')
               
           initial_time = end_time - start_time
           logger.debug(f"[TIME_CALC] Tempo calculado: {initial_time}")
           logger.debug("[TIME_CALC] ---- Cálculo finalizado ----")
           
           return initial_time
           
       except Exception as e:
           logger.error(f"[TIME_CALC] Erro ao calcular tempo inicial: {e}")
           return timedelta()

   def set_user_id(self, user_id):
       """Define o ID do usuário"""
       self.user_id = user_id