from datetime import datetime
import logging
from ....core.activity.activity_manager import ActivityManager
from ....core.activity.activity_validator import ActivityValidator

logger = logging.getLogger(__name__)

class ActivityFormLogic:
    def __init__(self, db_connection):
        self.db = db_connection
        self.activity_manager = ActivityManager()
    
    def create_activity(self, user_id: int, data: dict) -> tuple:
        """Cria uma nova atividade"""
        try:
            if not data.get('description') or not data.get('activity'):
                return False, "Preencha todos os campos!"
                
            # Garantir que end_time é um datetime correto
            end_time = data['end_time']
            now = datetime.now()

            logger.debug(f"[FORM_LOGIC] Data/hora atual: {now}")
            logger.debug(f"[FORM_LOGIC] Data/hora fim recebida: {end_time}")
            logger.debug(f"[FORM_LOGIC] Tipo do end_time: {type(end_time)}")

            # Verificar se end_time é realmente maior que now
            if isinstance(end_time, datetime) and end_time > now:
                logger.debug("[FORM_LOGIC] Data/hora fim é válida")
                return self.activity_manager.create_activity(user_id, data)
            else:
                logger.debug("[FORM_LOGIC] Data/hora fim é inválida")
                return False, "O horário de finalização deve ser maior que o horário atual!"
            
        except Exception as e:
            logger.error(f"Erro ao criar atividade: {e}")
            return False, f"Erro ao criar atividade: {e}"

    def validate_new_activity(self, data):
        """
        Valida os dados de uma nova atividade
        """
        # Validar dados básicos
        valid, message = ActivityValidator.validate_activity_data(data)
        if not valid:
            return False, message

        # Validar descrição
        valid, message = ActivityValidator.validate_activity_description(data['description'])
        if not valid:
            return False, message

        # Validar horário comercial
        time_status = ActivityValidator.validate_time_range(datetime.now().time())
        if time_status != "working_hours":
            return False, "Fora do horário de expediente"

        # Validar se é dia útil
        if not ActivityValidator.validate_working_days(data['end_time']):
            return False, "Data inválida (fim de semana ou feriado)"

        return True, ""