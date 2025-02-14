from datetime import datetime, time
import logging
from typing import Optional
from ...database.connection import DatabaseConnection

logger = logging.getLogger(__name__)

class LockStateObserver:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.db = DatabaseConnection()
            self._initialized = True
            self._observers = []
            self._check_timer_id = None
            self._start_monitoring()

    def add_observer(self, observer):
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_observer(self, observer):
        if observer in self._observers:
            self._observers.remove(observer)

    def check_lock_state(self, user_id: int) -> bool:
        """
        Verifica o estado de bloqueio do usuário
        Returns: True se desbloqueado, False se bloqueado
        """
        try:
            query = """
                SELECT unlock_control 
                FROM user_lock_unlock 
                WHERE user_id = %s
            """
            result = self.db.execute_query(query, (user_id,))
            
            if result:
                state = bool(result[0]['unlock_control'])
                logger.debug(f"[LOCK] Estado atual do usuário {user_id}: {state}")
                return state
            logger.debug(f"[LOCK] Nenhum estado encontrado para usuário {user_id}")
            return False
            
        except Exception as e:
            logger.error(f"Erro ao verificar estado de bloqueio: {e}")
            return False

    def notify_observers(self, is_unlocked: bool):
        """Notifica todos os observadores sobre mudança no estado de bloqueio"""
        for observer in self._observers:
            try:
                observer.on_lock_state_changed(is_unlocked)
            except Exception as e:
                logger.error(f"Erro ao notificar observer sobre bloqueio: {e}")

    def _start_monitoring(self):
        """Inicia monitoramento periódico do estado de bloqueio"""
        try:
            def check_changes():
                for observer in self._observers:
                    if hasattr(observer, 'user_data'):
                        current_state = self.check_lock_state(observer.user_data['id'])
                        
                        # Se o estado mudou para bloqueado
                        if hasattr(observer, 'is_unlocked') and observer.is_unlocked != current_state:
                            if not current_state:  # Se vai bloquear
                                # Pausar atividades ativas antes do bloqueio
                                if hasattr(observer, '_pause_active_activities'):
                                    observer._pause_active_activities()
                            
                            logger.debug(f"[LOCK] Estado mudou de {observer.is_unlocked} para {current_state}")
                            observer.is_unlocked = current_state  # Atualiza o estado
                            observer.on_lock_state_changed(current_state)  # Notifica mudança
                        
                        # Força atualização da UI independente de mudança
                        if hasattr(observer, 'update_button_states'):
                            observer.update_button_states()
                        
                        # Agendar próxima verificação
                        if hasattr(observer, 'after'):
                            observer.after(2000, check_changes)
                            break

            check_changes()
        except Exception as e:
            logger.error(f"Erro ao monitorar mudanças de bloqueio: {e}")
 