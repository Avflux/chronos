from tkinter import messagebox
from datetime import datetime
import logging
from typing import Dict, List, Optional, Tuple
from ..time.time_manager import TimeManager
from ...database.connection import DatabaseConnection

logger = logging.getLogger(__name__)

class ActivityManager:
    def __init__(self):
        self.db = DatabaseConnection()
        self.time_manager = TimeManager()

    def calculate_initial_time(self, start_time, end_time) -> str:
        """
        Calcula tempo inicial considerando regras de horário comercial
        """
        try:
            # Obter horários da empresa
            company_start = TimeManager.get_time_object(TimeManager.COMPANY_START_TIME)  # 08:00
            company_end = TimeManager.get_time_object(TimeManager.COMPANY_END_TIME)      # 18:30
            break_start = TimeManager.get_time_object(TimeManager.BREAK_START_TIME)      # 12:15
            break_end = TimeManager.get_time_object(TimeManager.BREAK_END_TIME)          # 13:15

            # 1. Ajuste do horário de início
            if start_time.time() < company_start:
                # Se começar antes do expediente, ajusta para 8:00
                start_time = start_time.replace(
                    hour=company_start.hour,
                    minute=company_start.minute,
                    second=0
                )
            elif break_start <= start_time.time() <= break_end:
                # Se começar no intervalo, ajusta para 13:15
                start_time = start_time.replace(
                    hour=break_end.hour,
                    minute=break_end.minute,
                    second=0
                )

            # 2. Ajuste do horário de término
            if end_time.time() > company_end:
                # Se terminar após expediente, ajusta para 18:30
                end_time = end_time.replace(
                    hour=company_end.hour,
                    minute=company_end.minute,
                    second=0
                )
            elif break_start <= end_time.time() <= break_end:
                # Se terminar no intervalo, ajusta para 12:15
                end_time = end_time.replace(
                    hour=break_start.hour,
                    minute=break_start.minute,
                    second=0
                )

            # 3. Cálculo da duração total
            duration = end_time - start_time
            
            # 4. Desconto do intervalo de almoço
            if (start_time.time() < break_start and 
                end_time.time() > break_end):
                # Se período engloba o intervalo, desconta 1 hora
                break_duration = datetime.combine(start_time.date(), break_end) - \
                               datetime.combine(start_time.date(), break_start)
                duration -= break_duration

            # 5. Conversão para formato HH:MM:SS
            total_seconds = int(duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        except Exception as e:
            logger.error(f"Erro ao calcular tempo inicial: {e}")
            return "00:00:00"

    def create_activity(self, user_id: int, data: Dict) -> Tuple[bool, str]:
        try:
            logger.debug("[DB] Iniciando criação de atividade")
            
            current_time = datetime.now()
            
            # Calcular tempo inicial usando o formatter
            initial_time = self.time_manager.format_duration(
                current_time,  # Usar current_time como start_time
                data['end_time']
            )
            
            # Atualizar query existente
            query = """
                INSERT INTO atividades 
                (user_id, description, atividade, start_time, end_time, 
                time_regress, time_exceeded, total_time, ativo, pausado, concluido)
                VALUES (%s, %s, %s, %s, %s, %s, '00:00:00', '00:00:00', TRUE, FALSE, FALSE)
            """
            params = (
                user_id,
                data['description'],
                data['activity'],
                current_time,
                data['end_time'],
                initial_time
            )
            self.db.execute_query(query, params)
            
            # Obter ID da atividade criada
            new_id = self.db.execute_query("SELECT LAST_INSERT_ID()")[0]['LAST_INSERT_ID()']
            
            # Criar objeto de atividade completo
            activity_info = {
                'id': new_id,
                'description': data['description'],
                'atividade': data['activity'],
                'start_time': current_time,
                'end_time': data['end_time'],
                'time_regress': initial_time,
                'time_exceeded': '00:00:00',
                'ativo': True,
                'pausado': False,
                'concluido': False
            }
            
            logger.debug(f"[DB] Atividade criada com ID: {new_id}")
            
            # Iniciar o timer imediatamente
            self.time_manager.start_activity(activity_info)
            logger.debug("[TIMER] Timer iniciado para nova atividade")
            
            return True, "Atividade criada com sucesso!"
            
        except Exception as e:
            logger.error(f"Erro ao criar atividade: {e}")
            return False, f"Erro ao criar atividade: {e}"

    def get_user_activities(self, user_id: int, period: str = "day") -> List[Dict]:
        """
        Busca as atividades do usuário com filtro de período.
        Args:
            user_id: ID do usuário
            period: "day", "month" ou "year"
        Returns:
            List[Dict]: Lista de atividades
        """
        try:
            date_filter = {
                "day": "DATE(start_time) = CURDATE()",
                "month": "MONTH(start_time) = MONTH(CURDATE()) AND YEAR(start_time) = YEAR(CURDATE())",
                "year": "YEAR(start_time) = YEAR(CURDATE())"
            }
            query = f"""
                SELECT id, description, atividade, start_time, end_time,
                       time_exceeded, total_time, ativo, pausado, concluido
                FROM atividades
                WHERE user_id = %s AND {date_filter.get(period, "TRUE")}
                ORDER BY start_time DESC
            """
            return self.db.execute_query(query, (user_id,))
        except Exception as e:
            logger.error(f"Erro ao buscar atividades: {e}")
            return []

    def update_activity_status(self, activity_id: int, status: str) -> Tuple[bool, str]:
        """
        Atualiza o status de uma atividade no banco de dados.
        """
        try:
            logger.debug(f"[DB] Atualizando status para: {status}")
            status_updates = {
            "pausado": {
                "pausado": True,
                "ativo": True,
                "concluido": False,
                "total_time": self._get_current_total_time(activity_id),
                "time_regress": self._get_current_regress_time(activity_id),
                "time_exceeded": self._get_current_exceeded_time(activity_id)
            },
                "ativo": {
                    "pausado": False,
                    "ativo": True,
                    "concluido": False
                },
                "concluido": {
                    "pausado": False,
                    "ativo": False,
                    "concluido": True,
                    "total_time": self._get_current_total_time(activity_id),
                    "time_regress": self._get_current_regress_time(activity_id),  # Novo método
                    "time_exceeded": self._get_current_exceeded_time(activity_id)  # Novo método
                }
            }

            if status == "pausado":
                current_total = self._get_current_total_time(activity_id)
                logger.debug(f"[DB] Total time calculado: {current_total}")
                
                logger.debug(f"[DB] Query: {query}")
                logger.debug(f"[DB] Parâmetros: {params}")

            if status not in status_updates:
                return False, "Status inválido"

            # Construir query dinamicamente
            update_fields = []
            params = []
            for field, value in status_updates[status].items():
                update_fields.append(f"{field} = %s")
                params.append(value)
            params.append(activity_id)

            query = f"""
                UPDATE atividades 
                SET {', '.join(update_fields)}
                WHERE id = %s
            """

            self.db.execute_query(query, tuple(params))
            return True, f"Atividade {status} com sucesso!"
        
        except Exception as e:
            logger.error(f"Erro ao atualizar status da atividade: {e}")
            return False, f"Erro ao atualizar status: {e}"
        
    def _get_current_regress_time(self, activity_id: int) -> Optional[str]:
        """
        Obtém o tempo regressivo atual da atividade.
        Retorna None se não houver tempo regressivo ativo.
        """
        try:
            query = """
                SELECT time_regress, time_exceeded
                FROM atividades
                WHERE id = %s
            """
            result = self.db.execute_query(query, (activity_id,))
            
            if not result:
                return None
                
            # Se temos tempo excedido, retorna zero no regressivo
            if result[0]['time_exceeded'] != '00:00:00':
                return '00:00:00'
                
            return result[0]['time_regress']
            
        except Exception as e:
            logger.error(f"Erro ao obter tempo regressivo: {e}")
            return None

    def _get_current_exceeded_time(self, activity_id: int) -> Optional[str]:
        """
        Obtém o tempo excedido atual da atividade.
        Retorna None se não houver tempo excedido.
        """
        try:
            query = """
                SELECT time_regress, time_exceeded
                FROM atividades
                WHERE id = %s
            """
            result = self.db.execute_query(query, (activity_id,))
            
            if not result:
                return None
                
            # Se ainda temos tempo regressivo, retorna zero no excedido
            if result[0]['time_regress'] != '00:00:00':
                return '00:00:00'
                
            return result[0]['time_exceeded']
            
        except Exception as e:
            logger.error(f"Erro ao obter tempo excedido: {e}")
            return None
        
    def _get_current_total_time(self, activity_id: int) -> Optional[str]:
        """Calcula o tempo total atual da atividade"""
        try:
            logger.debug(f"[DB] Calculando tempo total para atividade {activity_id}")
            
            # Buscar dados da atividade
            query = """
                SELECT start_time, total_time, pausado, 
                    time_regress, time_exceeded
                FROM atividades
                WHERE id = %s
            """
            result = self.db.execute_query(query, (activity_id,))
            logger.debug(f"[DB] Resultado da query: {result}")
            
            if not result:
                logger.warning(f"[DB] Atividade {activity_id} não encontrada")
                return None
                
            activity = result[0]
            logger.debug(f"[DB] Dados recuperados: {activity}")
            
            # Se já tiver tempo total e estiver pausada, retornar valor existente
            if activity['pausado'] and activity['total_time']:
                logger.debug(f"[DB] Retornando tempo total existente: {activity['total_time']}")
                return activity['total_time']
                
            # Calcular tempo decorrido
            start_time = activity['start_time']
            if isinstance(start_time, str):
                start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
                
            logger.debug(f"[DB] Start time: {start_time}")
            current_time = datetime.now()
            logger.debug(f"[DB] Current time: {current_time}")
            
            # Calcular tempo existente
            existing_seconds = 0
            if activity['total_time']:
                try:
                    h, m, s = map(int, activity['total_time'].split(':'))
                    existing_seconds = h * 3600 + m * 60 + s
                    logger.debug(f"[DB] Segundos existentes: {existing_seconds}")
                except ValueError:
                    logger.warning("[DB] Erro ao converter tempo existente, usando 0")
                    existing_seconds = 0
            
            # Calcular tempo decorrido em segundos
            elapsed_seconds = int((current_time - start_time).total_seconds()) + existing_seconds
            logger.debug(f"[DB] Segundos totais: {elapsed_seconds}")
            
            # Converter para HH:MM:SS
            hours = elapsed_seconds // 3600
            minutes = (elapsed_seconds % 3600) // 60
            seconds = elapsed_seconds % 60
            
            total_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            logger.debug(f"[DB] Tempo total calculado: {total_time}")
            
            return total_time
            
        except Exception as e:
            logger.error(f"[DB] Erro ao calcular tempo total: {e}")
            return None

    def update_time_exceeded(self, activity_id: int) -> bool:
        """
        Atualiza o status de tempo excedido no banco.
        """
        try:
            query = """
                UPDATE atividades 
                SET time_exceeded = CASE
                    WHEN NOW() > end_time THEN TRUE
                    ELSE time_exceeded
                END
                WHERE id = %s
            """
            self.db.execute_query(query, (activity_id,))
            return True
        except Exception as e:
            logger.error(f"Erro ao atualizar tempo excedido: {e}")
            return False

    def get_active_activity(self, user_id: int) -> Optional[Dict]:
        """
        Busca a atividade ativa do usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Optional[Dict]: Dados da atividade ativa ou None
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
            
            result = self.db.execute_query(query, (user_id,))
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"Erro ao buscar atividade ativa: {e}")
            return None

    def handle_activity_notifications(self, activity_id: int) -> None:
        """
        Gerencia notificações relacionadas a uma atividade.
        """
        try:
            # Busca dados da atividade
            query = """
                SELECT end_time
                FROM atividades 
                WHERE id = %s
            """
            result = self.db.execute_query(query, (activity_id,))
            
            if not result:
                return
                
            activity = result[0]
            now = datetime.now()
            
            # Verifica se está próximo do fim
            time_diff = activity['end_time'] - now
            minutes_remaining = time_diff.total_seconds() / 60
            
            # Notifica quando faltam 15 minutos
            if 14 <= minutes_remaining <= 15:
                self._notify_time_remaining(15)
                
            # Notifica quando faltam 5 minutos
            elif 4 <= minutes_remaining <= 5:
                self._notify_time_remaining(5)
                
            # Notifica quando o tempo acabou
            elif -1 <= minutes_remaining <= 0:
                self._notify_time_exceeded()

        except Exception as e:
            logger.error(f"Erro ao gerenciar notificações: {e}")

    def _notify_time_remaining(self, minutes: int) -> None:
        """
        Envia notificação de tempo restante.
        """
        title = f"Aviso de Tempo - {minutes} minutos"
        message = f"Faltam {minutes} minutos para o término da atividade!"
        messagebox.showwarning(title, message)

    def notify_time_exceeded(self, activity_info: Dict) -> None:
        """
        Registra que o tempo foi excedido sem mostrar mensagem
        """
        try:
            if not activity_info:
                return
                
            # Apenas atualiza o status no banco
            query = """
                UPDATE atividades 
                SET time_exceeded = TRUE 
                WHERE id = %s
            """
            self.db.execute_query(query, (activity_info['id'],))
            logger.debug(f"Tempo excedido registrado para atividade {activity_info['id']}")
            
        except Exception as e:
            logger.error(f"Erro ao registrar tempo excedido: {e}")