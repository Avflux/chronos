from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class TimeObserver(ABC):
    @abstractmethod
    def update_daily_time(self, daily_time: timedelta) -> None:
        """
        Atualiza o display do tempo diário acumulado
        
        Args:
            daily_time: Tempo total acumulado no dia
        """
        pass

    @abstractmethod
    def update_timer_display(self, timer_value: timedelta, total_time: timedelta) -> None:
        """
        Atualiza o display do timer com os novos valores de tempo
        
        Args:
            timer_value: Valor atual do timer (tempo restante ou decorrido)
            total_time: Tempo total acumulado
        """
        pass
        
    @abstractmethod
    def update_activity_status(self, activity_info: Optional[Dict]) -> None:
        """
        Atualiza o status da atividade atual
        
        Args:
            activity_info: Dicionário com informações da atividade ou None se não houver atividade
        """
        pass

    @abstractmethod
    def notify_time_exceeded(self, activity_info: Dict) -> None:
        """
        Notifica quando o tempo da atividade foi excedido (sem exibir mensagem)
        
        Args:
            activity_info: Informações da atividade que excedeu o tempo
        """
        pass

    @abstractmethod
    def update_idle_status(self, status: str):
        """Atualiza o status de ociosidade"""
        pass

class TimeObservable:
    def __init__(self):
        self._observers = []

    def notify_observers_daily_time(self, daily_time: timedelta) -> None:
        """Notifica todos os observadores sobre mudanças no tempo diário"""
        for observer in self._observers:
            try:
                observer.update_daily_time(daily_time)
            except Exception as e:
                logger.error(f"Erro ao notificar observer sobre tempo diário {observer.__class__.__name__}: {e}")
        
    def add_observer(self, observer: TimeObserver) -> None:
        """Adiciona um novo observador"""
        if observer not in self._observers:
            self._observers.append(observer)
            logger.debug(f"Observer adicionado: {observer.__class__.__name__}")
            
    def remove_observer(self, observer: TimeObserver) -> None:
        """Remove um observador"""
        if observer in self._observers:
            self._observers.remove(observer)
            logger.debug(f"Observer removido: {observer.__class__.__name__}")
            
    def notify_observers_timer(self, timer_value: timedelta, total_time: timedelta) -> None:
        """Notifica todos os observadores sobre mudanças no timer"""
        for observer in self._observers:
            try:
                observer.update_timer_display(timer_value, total_time)
            except Exception as e:
                logger.error(f"Erro ao notificar observer {observer.__class__.__name__}: {e}")
                
    def notify_observers_activity(self, activity_info: Optional[Dict]) -> None:
        """Notifica todos os observadores sobre mudanças no status da atividade"""
        for observer in self._observers:
            try:
                observer.update_activity_status(activity_info)
            except Exception as e:
                logger.error(f"Erro ao notificar observador {observer.__class__.__name__}: {e}")
                
    def notify_time_exceeded(self, activity_info: Dict) -> None:
        """Notifica os observadores que o tempo foi excedido (sem exibir mensagem)"""
        for observer in self._observers:
            try:
                observer.notify_time_exceeded(activity_info)
            except Exception as e:
                logger.error(f"Erro ao notificar tempo excedido para {observer.__class__.__name__}: {e}")