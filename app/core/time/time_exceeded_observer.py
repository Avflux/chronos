import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from ...database.connection import DatabaseConnection
from ...ui.dialogs.reason_exceeded_dialog import ReasonExceededDialog

logger = logging.getLogger(__name__)

class TimeExceededObserver:
    def __init__(self):
        self.db = DatabaseConnection()
        self._observers = []

    def add_observer(self, observer):
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_observer(self, observer):
        if observer in self._observers:
            self._observers.remove(observer)

    def check_time_exceeded(self, activity_id: int) -> Optional[Dict]:
        """Verifica se uma atividade excedeu o tempo e precisa de justificativa"""
        try:
            logger.info(f"[TIME_EXCEEDED] Verificando tempo excedido para atividade {activity_id}")
            
            query = """
                SELECT a.id, a.atividade, a.time_exceeded, a.reason
                FROM atividades a
                WHERE a.id = %s 
                AND TIME_TO_SEC(a.time_exceeded) > 0
                AND (a.reason IS NULL OR a.reason = '')
            """
            result = self.db.execute_query(query, (activity_id,))
            
            if result and result[0]:
                logger.info(f"[TIME_EXCEEDED] Atividade {activity_id} tem tempo excedido: {result[0]['time_exceeded']}")
                return result[0]
            
            logger.debug(f"[TIME_EXCEEDED] Atividade {activity_id} não tem tempo excedido ou já tem justificativa")
            return None
            
        except Exception as e:
            logger.error(f"[TIME_EXCEEDED] Erro ao verificar tempo excedido: {e}")
            return None

    def handle_activity_conclusion(self, parent_window, activity_info: Dict) -> bool:
        """
        Gerencia a conclusão de atividade, verificando tempo excedido
        Retorna True se a conclusão pode prosseguir, False caso contrário
        """
        try:
            logger.info(f"[TIME_EXCEEDED] Iniciando verificação de conclusão para atividade {activity_info['id']}")
            
            # Verificar se há tempo excedido
            exceeded_info = self.check_time_exceeded(activity_info['id'])
            
            if exceeded_info:
                logger.info(f"[TIME_EXCEEDED] Abrindo diálogo de justificativa para atividade {activity_info['id']}")
                dialog = ReasonExceededDialog(parent_window, activity_info)
                parent_window.wait_window(dialog)
                
                if dialog.result:
                    reason = dialog.result['selected_reason'] or dialog.result['other_reason']
                    if reason:
                        logger.info(f"[TIME_EXCEEDED] Salvando justificativa para atividade {activity_info['id']}: {reason}")
                        update_query = """
                            UPDATE atividades 
                            SET reason = %s 
                            WHERE id = %s
                        """
                        self.db.execute_query(update_query, (reason, activity_info['id']))
                        return True
                    
                    logger.warning(f"[TIME_EXCEEDED] Justificativa não fornecida para atividade {activity_info['id']}")
                    return False
                
                logger.warning(f"[TIME_EXCEEDED] Diálogo cancelado para atividade {activity_info['id']}")
                return False
            
            logger.info(f"[TIME_EXCEEDED] Atividade {activity_info['id']} não requer justificativa")
            return True
            
        except Exception as e:
            logger.error(f"[TIME_EXCEEDED] Erro ao gerenciar conclusão de atividade: {e}")
            return False

    def notify_observers(self, activity_info: Dict):
        """Notifica observadores sobre mudança no status de tempo excedido"""
        for observer in self._observers:
            if hasattr(observer, 'on_time_exceeded_changed'):
                observer.on_time_exceeded_changed(activity_info)

    def check_activity_state(self, activity_id: int) -> bool:
        """Verifica o estado da atividade para determinar se precisa de justificativa"""
        try:
            logger.debug(f"[OBSERVER] ---- Iniciando verificação de estado da atividade {activity_id} ----")
            
            query = """
                SELECT 
                    TIME_TO_SEC(time_exceeded) as time_exceeded_seconds,
                    reason,
                    ativo,
                    pausado,
                    concluido
                FROM atividades
                WHERE id = %s
            """
            logger.debug(f"[OBSERVER] Executando query: {query}")
            result = self.db.execute_query(query, (activity_id,))
            logger.debug(f"[OBSERVER] Resultado da query: {result}")
            
            if result and result[0]:
                activity = result[0]
                time_exceeded_seconds = activity['time_exceeded_seconds']
                reason = activity.get('reason')
                has_reason = bool(reason) if reason is not None else False
                
                logger.debug(f"[OBSERVER] Detalhes do estado:")
                logger.debug(f"[OBSERVER] - Tempo excedido (segundos): {time_exceeded_seconds}")
                logger.debug(f"[OBSERVER] - Tem justificativa: {has_reason}")
                logger.debug(f"[OBSERVER] - Justificativa: {reason}")
                
                # Verifica se tem tempo excedido e não tem justificativa
                needs_justification = (
                    time_exceeded_seconds > 0 and
                    not has_reason
                )
                
                logger.debug(f"[OBSERVER] Precisa de justificativa? {needs_justification}")
                logger.debug(f"[OBSERVER] - Condições:")
                logger.debug(f"[OBSERVER] -- Tempo excedido maior que zero? {time_exceeded_seconds > 0}")
                logger.debug(f"[OBSERVER] -- Sem justificativa? {not has_reason}")
                
                return needs_justification
                
        except Exception as e:
            logger.error(f"[OBSERVER] Erro ao verificar estado: {e}")
            return False
        finally:
            logger.debug("[OBSERVER] ---- Fim da verificação de estado ----") 