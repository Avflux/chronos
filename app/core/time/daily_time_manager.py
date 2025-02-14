from datetime import datetime, timedelta, time
import logging
from .time_manager import TimeManager
from .time_observer import TimeObservable

logger = logging.getLogger(__name__)

class DailyTimeManager(TimeObservable):
    def __init__(self):
        super().__init__()
        self.daily_accumulated = timedelta()
        self.daily_start_time = None
        self.last_update = None
        self.is_running = False
        self.state = None
        self._timer_id = None
        
    @staticmethod
    def _parse_time_str(time_str: str) -> time:
        """Converte string de tempo no formato HH:MM:SS para objeto time"""
        hours, minutes, seconds = map(int, time_str.split(':'))
        return time(hours, minutes, seconds)
        
    def set_state(self, state):
        """Define o estado do timer"""
        self.state = state

    def update_daily_hours(self):
        """Atualiza o contador de horas diárias"""
        try:
            current_time = datetime.now()
            
            # Verificar se está rodando
            if not self.is_running:
                return
                
            # Verificar horário comercial usando TimeManager
            company_status = TimeManager.check_company_hours()
            should_compute, _ = TimeManager.should_compute_time(company_status)
            
            if not should_compute:
                return
                
            # Atualizar o tempo diário
            if not self.daily_start_time:
                self.daily_start_time = current_time
                self.last_update = current_time
                
            # Calcular tempo desde última atualização
            time_elapsed = current_time - self.last_update
            self.daily_accumulated += time_elapsed
            self.last_update = current_time
            
            # Notificar observadores
            self.notify_observers_daily_time(self.daily_accumulated)
            
        except Exception as e:
            logger.error(f"Erro ao atualizar horas diárias: {e}")

    def start_daily_timer(self):
        """Inicia ou retoma o timer diário"""
        try:
            current_time = datetime.now()
            
            # Verificar se está dentro do horário comercial
            company_status = TimeManager.check_company_hours()
            should_start, message = TimeManager.should_compute_time(company_status)
            
            if not should_start:
                logger.info(f"Não iniciando timer: {message}")
                return
                
            self.is_running = True
            self.last_update = current_time
            if not self.daily_start_time:
                self.daily_start_time = current_time
            logger.debug("Timer diário iniciado/retomado")
        except Exception as e:
            logger.error(f"Erro ao iniciar timer diário: {e}")

    def pause_daily_timer(self):
        """Pausa o timer diário"""
        try:
            if self.is_running and self.last_update:
                self.is_running = False
                current_time = datetime.now()
                
                # Verificar se deve computar o tempo
                company_status = TimeManager.check_company_hours()
                should_compute, _ = TimeManager.should_compute_time(company_status)
                
                if should_compute:
                    time_elapsed = current_time - self.last_update
                    self.daily_accumulated += time_elapsed
                
                logger.debug("Timer diário pausado")
        except Exception as e:
            logger.error(f"Erro ao pausar timer diário: {e}")

    def reset_daily_hours(self):
        """Reseta o contador de horas diárias"""
        try:
            self.daily_accumulated = timedelta()
            self.daily_start_time = None
            self.last_update = None
            self.is_running = False
            self.notify_observers_daily_time(self.daily_accumulated)
            logger.info("Contador de horas diárias resetado")
        except Exception as e:
            logger.error(f"Erro ao resetar horas diárias: {e}")

    def check_day_change(self):
        """Verifica se houve mudança de dia para resetar o contador"""
        try:
            if self.daily_start_time:
                current_date = datetime.now().date()
                if current_date > self.daily_start_time.date():
                    self.reset_daily_hours()
                    logger.info("Novo dia detectado, contador resetado")
        except Exception as e:
            logger.error(f"Erro ao verificar mudança de dia: {e}")