from datetime import datetime, time
from typing import Dict, Tuple, Optional
import re
import logging
from ..time.time_manager import TimeManager

logger = logging.getLogger(__name__)

class ActivityValidator:
    @classmethod
    def _parse_time(cls, time_str: str) -> Tuple[int, int]:
        """
        Converte string de tempo em tupla (hora, minuto)
        """
        parts = time_str.split(':')
        return (int(parts[0]), int(parts[1]))

    @classmethod
    def _get_company_hours(cls) -> Dict[str, time]:
        """
        Obtém horários da empresa do TimeManager como objetos time
        """
        return {
            'start': TimeManager.get_time_object(TimeManager.COMPANY_START_TIME),
            'break_start': TimeManager.get_time_object(TimeManager.BREAK_START_TIME),
            'break_end': TimeManager.get_time_object(TimeManager.BREAK_END_TIME),
            'end': TimeManager.get_time_object(TimeManager.COMPANY_END_TIME)
        }

    @classmethod
    def _get_company_hours_tuple(cls) -> Dict[str, Tuple[int, int]]:
        """
        Obtém horários da empresa do TimeManager como tuplas (hora, minuto)
        """
        return {
            'start': TimeManager.get_time_tuple(TimeManager.COMPANY_START_TIME),
            'break_start': TimeManager.get_time_tuple(TimeManager.BREAK_START_TIME),
            'break_end': TimeManager.get_time_tuple(TimeManager.BREAK_END_TIME),
            'end': TimeManager.get_time_tuple(TimeManager.COMPANY_END_TIME)
        }

    @classmethod
    def _get_time_messages(cls) -> Dict[str, Tuple[str, str]]:
        """
        Gera mensagens usando os horários atuais do TimeManager
        """
        hours = cls._get_company_hours_tuple()
        start_h, start_m = hours['start']
        break_start_h, break_start_m = hours['break_start']
        break_end_h, break_end_m = hours['break_end']
        end_h, end_m = hours['end']

        return {
            "before_hours": (
                "Início Antecipado",
                f"Você está iniciando uma atividade antes do horário de funcionamento da empresa ({start_h:02d}:{start_m:02d}).\n"
                "Deseja computar este tempo?"
            ),
            "break_time": (
                "Horário de Intervalo",
                f"Você está no horário de intervalo ({break_start_h:02d}:{break_start_m:02d} - {break_end_h:02d}:{break_end_m:02d}).\n"
                "Deseja continuar computando o tempo?"
            ),
            "after_hours": (
                "Fim do Expediente",
                f"O expediente da empresa se encerra às {end_h:02d}:{end_m:02d}.\n"
                "Deseja continuar computando o tempo?"
            )
        }

    @classmethod
    def validate_activity_data(cls, data: Dict) -> Tuple[bool, str]:
        """
        Valida os dados completos de uma atividade.
        """
        try:
            # Validação de campos obrigatórios
            required_fields = ['description', 'activity', 'end_time']
            for field in required_fields:
                if not data.get(field):
                    return False, f"O campo {field} é obrigatório!"

            # Validação de tamanho dos campos
            if len(data['description']) < 10:
                return False, "A descrição deve ter pelo menos 10 caracteres!"
            
            if len(data['activity']) < 3:
                return False, "O nome da atividade deve ter pelo menos 3 caracteres!"

            # Validação de data/hora
            if not isinstance(data['end_time'], datetime):
                return False, "Data/hora de finalização inválida!"

            now = datetime.now()
            end_time = data['end_time']
            
            if end_time > now:
                return True, ""
                
            return False, "O horário de finalização deve ser maior que o horário atual!"

        except Exception as e:
            logger.error(f"Erro ao validar dados da atividade: {e}")
            return False, "Erro ao validar dados da atividade"

    @classmethod
    def validate_time_range(cls, time_val: time) -> str:
        """
        Valida o horário em relação ao expediente.
        """
        company_hours = cls._get_company_hours()
        
        if time_val < company_hours['start']:
            return "before_hours"
        elif company_hours['break_start'] <= time_val <= company_hours['break_end']:
            return "break_time"
        elif time_val > company_hours['end']:
            return "after_hours"
        return "working_hours"

    @classmethod
    def validate_concurrent_activities(cls, user_id: int, db_connection) -> Tuple[bool, Optional[Dict]]:
        """
        Verifica se o usuário tem atividades concorrentes.
        
        Args:
            user_id (int): ID do usuário
            db_connection: Conexão com o banco de dados
        
        Returns:
            Tuple[bool, Optional[Dict]]: (tem_atividade_ativa, dados_atividade)
        """
        try:
            query = """
                SELECT * FROM atividades
                WHERE user_id = %s 
                AND ativo = TRUE 
                AND concluido = FALSE
                ORDER BY start_time DESC
                LIMIT 1
            """
            result = db_connection.execute_query(query, (user_id,))
            return bool(result), result[0] if result else None
        except Exception as e:
            logger.error(f"Erro ao verificar atividades concorrentes: {e}")
            return False, None

    @classmethod
    def validate_activity_transition(cls, current_status: str, new_status: str) -> Tuple[bool, str]:
        """
        Valida se a transição de status é permitida.
        
        Args:
            current_status (str): Status atual da atividade
            new_status (str): Novo status desejado
        
        Returns:
            Tuple[bool, str]: (transição_permitida, mensagem_erro)
        """
        # Mapeamento de transições permitidas
        allowed_transitions = {
            'Em andamento': ['Pausada', 'Concluída'],
            'Pausada': ['Em andamento'],
            'Concluída': [],  # Não permite transições após concluída
            'Inativa': []     # Não permite transições de inativa
        }

        if current_status not in allowed_transitions:
            return False, "Status atual inválido!"

        if new_status not in allowed_transitions.get(current_status, []):
            return False, f"Não é possível mudar de {current_status} para {new_status}!"

        return True, ""

    @classmethod
    def get_time_status_message(cls, status: str) -> Tuple[str, str]:
        """
        Retorna a mensagem apropriada para cada status de horário.
        """
        messages = cls._get_time_messages()
        return messages.get(status, (None, None))

    @classmethod
    def validate_activity_description(cls, description: str) -> Tuple[bool, str]:
        """
        Valida o formato e conteúdo da descrição da atividade.
        
        Args:
            description (str): Descrição da atividade
        
        Returns:
            Tuple[bool, str]: (é_válido, mensagem_erro)
        """
        # Remove espaços extras
        description = description.strip()

        # Verifica tamanho mínimo
        if len(description) < 10:
            return False, "A descrição deve ter pelo menos 10 caracteres!"

        # Verifica tamanho máximo
        if len(description) > 500:
            return False, "A descrição não pode ter mais de 500 caracteres!"

        # Verifica caracteres especiais indesejados
        if re.search(r'[<>{}]', description):
            return False, "A descrição contém caracteres inválidos!"

        # Verifica se não contém apenas números
        if description.replace(" ", "").isdigit():
            return False, "A descrição não pode conter apenas números!"

        return True, ""

    @classmethod
    def validate_working_days(cls, date_val: datetime) -> bool:
        """
        Verifica se a data é um dia útil.
        
        Args:
            date_val (datetime): Data a ser verificada
        
        Returns:
            bool: True se for dia útil, False caso contrário
        """
        # Verifica se é fim de semana
        if date_val.weekday() in [5, 6]:  # 5 = Sábado, 6 = Domingo
            return False
            
        # Aqui você poderia adicionar mais verificações:
        # - Feriados
        # - Recesso da empresa
        # - Outros dias não úteis
            
        return True