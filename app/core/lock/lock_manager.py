import logging
from datetime import datetime
from ..time.time_manager import TimeManager

logger = logging.getLogger(__name__)

class LockManager:
    def __init__(self, db):
        self.db = db
        self.time_manager = TimeManager()
    
    def should_lock_controls(self, user_id: int) -> bool:
        """Verifica se os controles devem ser bloqueados"""
        try:
            # Verificar bloqueio manual primeiro
            is_manually_unlocked = self.db.check_lock_status(user_id)
            
            # Se estiver desbloqueado manualmente (unlock_control=1), não bloqueia
            if is_manually_unlocked:
                return False
                
            # Verificar horário comercial
            current_status = self.time_manager.check_company_hours()
            # Bloqueia se for depois do expediente OU horário de almoço
            return current_status in ["after_hours", "lunch_break"]
            
        except Exception as e:
            logger.error(f"Erro na verificação de bloqueio: {e}")
            return False 